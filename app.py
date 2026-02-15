import os
import logging
import requests
import json
import threading
import google.generativeai as genai
from flask import Flask, request, jsonify
from database import get_db_connection, init_db, salvar_mensagem, buscar_historico
# Certifique-se de que o arquivo tools.py existe
from tools import tools_config, ferramenta_ver_agenda, agendar_consulta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# Configurações
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# IMPORTANTE: Se rodar em Docker, use o nome do container da Evolution (ex: http://evolution_api:8080)
EVOLUTION_URL = os.getenv("EVOLUTION_URL", "http://evolution_api:8080") 
EVOLUTION_APIKEY = os.getenv("EVOLUTION_APIKEY")
INSTANCE_NAME = os.getenv("INSTANCE_NAME", "BotMedico")

genai.configure(api_key=GEMINI_API_KEY)

def enviar_whatsapp(remote_jid, texto):
    """Envia mensagem via Evolution API"""
    url = f"{EVOLUTION_URL}/message/sendText/{INSTANCE_NAME}"
    headers = {
        "apikey": EVOLUTION_APIKEY,
        "Content-Type": "application/json"
    }
    payload = {"number": remote_jid, "text": texto}
    
    try:
        logging.info(f"📤 Enviando para {remote_jid} via {url}")
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code not in [200, 201]:
            logging.error(f"❌ Erro Evolution: {response.text}")
    except Exception as e:
        logging.error(f"❌ Falha de conexão Evolution: {e}")

def processar_ia(remote_jid, mensagem_usuario):
    """Lógica da IA"""
    logging.info(f"🧠 Processando mensagem de {remote_jid}: {mensagem_usuario}")
    try:
        historico = buscar_historico(remote_jid)
        
        system_instruction = """
        Você é a Clara, secretária virtual da Clínica Dr. Victor.
        Seu objetivo é agendar consultas.
        1. Use a ferramenta 'ver_agenda' para consultar horários.
        2. Use a ferramenta 'agendar_consulta' APENAS quando tiver Nome, Telefone e Data.
        3. Seja simpática e breve.
        """
        
        model = genai.GenerativeModel(
            model_name='gemini-2.0-flash', # Usei o 2.0 que é mais rápido, ou volte para 1.5-flash
            tools=tools_config,
            system_instruction=system_instruction
        )

        chat = model.start_chat(history=historico)
        response = chat.send_message(mensagem_usuario)
        
        # Loop de Function Calling
        for _ in range(5):
            if not response.candidates: break
            
            part = response.candidates[0].content.parts[0]
            
            # Se for texto, envia e encerra
            if part.text:
                resposta_final = part.text
                salvar_mensagem(remote_jid, "user", mensagem_usuario) # Salva o input original
                salvar_mensagem(remote_jid, "model", resposta_final)
                enviar_whatsapp(remote_jid, resposta_final)
                return

            # Se for chamada de função
            if part.function_call:
                fn = part.function_call
                logging.info(f"🔧 Chamando ferramenta: {fn.name}")
                
                api_response = {}
                if fn.name == 'ver_agenda':
                    api_response = ferramenta_ver_agenda(**dict(fn.args))
                elif fn.name == 'agendar_consulta':
                    api_response = agendar_consulta(**dict(fn.args))
                
                # Devolve a resposta da ferramenta para o Gemini gerar o texto final
                response = chat.send_message(
                    genai.protos.Content(
                        parts=[genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=fn.name,
                                response=api_response
                            )
                        )]
                    )
                )

    except Exception as e:
        logging.error(f"❌ ERRO GRAVE NA IA: {e}", exc_info=True)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        if data.get('event') == 'messages.upsert':
            msg = data.get('data', {})
            key = msg.get('key', {})
            remote_jid = key.get('remoteJid')
            from_me = key.get('fromMe', False)
            
            # 1. EVITAR LOOP: Ignorar mensagens enviadas pelo próprio bot
            if from_me:
                return jsonify({"status": "ignored_me"}), 200

            # 2. EVITAR GRUPOS
            if "@g.us" in remote_jid:
                return jsonify({"status": "ignored_group"}), 200

            # 3. Extrair texto
            content = msg.get('message', {})
            texto = content.get('conversation') or content.get('extendedTextMessage', {}).get('text')
            
            if texto:
                # Inicia a thread
                threading.Thread(target=processar_ia, args=(remote_jid, texto)).start()

        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logging.error(f"Erro webhook: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
