import os
import logging
import requests
import json
import google.generativeai as genai
from flask import Flask, request, jsonify
from database import get_db_connection, init_db
from tools import tools_config, ferramenta_ver_agenda

# --- Configurações ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# Credenciais (Vêm do Docker environment)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
EVOLUTION_URL = os.getenv("EVOLUTION_URL") # Ex: http://evolution_api:8080
EVOLUTION_APIKEY = os.getenv("EVOLUTION_APIKEY")
INSTANCE_NAME = "MyInstance" # Nome da instância que você criará na Evolution

# Configura o Gemini com as ferramentas
genai.configure(api_key=GEMINI_API_KEY)

# --- Funções de Banco de Dados ---

def salvar_mensagem(telefone, role, mensagem):
    """Salva a mensagem no histórico do PostgreSQL"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO historico (telefone, role, mensagem) VALUES (%s, %s, %s)",
            (telefone, role, mensagem)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logging.error(f"Erro ao salvar no banco: {e}")

def buscar_historico(telefone, limite=10):
    """Recupera as últimas mensagens para dar contexto à IA"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT role, mensagem FROM historico WHERE telefone = %s ORDER BY created_at DESC LIMIT %s",
            (telefone, limite)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        # O banco retorna do mais recente para o antigo, precisamos inverter para a IA ler na ordem certa
        historico = []
        for row in reversed(rows): # Inverte a lista
            # Mapeia 'user' e 'model' para o formato do Gemini
            role = "user" if row[0] == "user" else "model"
            historico.append({"role": role, "parts": [row[1]]})
            
        return historico
    except Exception as e:
        logging.error(f"Erro ao buscar histórico: {e}")
        return []

# --- Funções de Envio (Evolution API) ---

def enviar_whatsapp(remote_jid, texto):
    """Envia a resposta final para o WhatsApp via Evolution API"""
    url = f"{EVOLUTION_URL}/message/sendText/{INSTANCE_NAME}"
    headers = {
        "apikey": EVOLUTION_APIKEY,
        "Content-Type": "application/json"
    }
    payload = {
        "number": remote_jid,
        "text": texto
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        logging.info(f"Resposta enviada para {remote_jid}: {response.status_code}")
    except Exception as e:
        logging.error(f"Erro ao enviar para Evolution: {e}")

# --- Cérebro da IA (Gemini + Tools) ---

def processar_ia(remote_jid, mensagem_usuario):
    # 1. Recupera histórico
    historico = buscar_historico(remote_jid)
    
    # 2. Adiciona a mensagem atual
    historico.append({"role": "user", "parts": [mensagem_usuario]})
    
    # 3. Configura o Modelo e o System Prompt
    system_instruction = """
    Você é a Clara, secretária virtual do Dr. Victor.
    Sua função é agendar consultas e tirar dúvidas.
    
    REGRAS:
    1. Sempre que perguntarem de horários, USE a ferramenta 'ver_agenda'. NÃO invente.
    2. Seja extremamente educada e profissional.
    3. Para agendar, peça: Nome Completo e Data de Nascimento.
    4. Se a ferramenta retornar 'Livre', ofereça o horário.
    """
    
    model = genai.GenerativeModel(
        model_name='gemini-2.0-flash', # Ou 1.5-flash
        tools=tools_config,
        system_instruction=system_instruction
    )

    chat = model.start_chat(history=historico[:-1]) # Inicia com histórico (menos a última msg que vai no send)

    try:
        # Envia a mensagem do usuário para o Gemini
        response = chat.send_message(mensagem_usuario)
        
        # --- Lógica de Function Calling (O "Pulo do Gato") ---
        # Verifica se o Gemini quer usar uma ferramenta (ex: ver a agenda)
        if response.candidates[0].content.parts[0].function_call:
            fn = response.candidates[0].content.parts[0].function_call
            logging.info(f"Gemini quer usar a ferramenta: {fn.name}")
            
            if fn.name == 'ver_agenda':
                # Executa a nossa função Python real
                args = dict(fn.args)
                dados_agenda = ferramenta_ver_agenda(args.get('data_relativa'))
                
                # Devolve o resultado (JSON) para o Gemini
                response = chat.send_message(
                    genai.protos.Content(
                        parts=[genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name='ver_agenda',
                                response={'result': dados_agenda}
                            )
                        )]
                    )
                )

        # Texto final da resposta
        resposta_texto = response.text
        
        # Salva no banco e envia
        salvar_mensagem(remote_jid, "user", mensagem_usuario)
        salvar_mensagem(remote_jid, "model", resposta_texto)
        enviar_whatsapp(remote_jid, resposta_texto)

    except Exception as e:
        logging.error(f"Erro no processamento da IA: {e}")
        enviar_whatsapp(remote_jid, "Desculpe, tive um erro técnico momentâneo. Pode repetir?")

# --- Rota do Webhook (Recebe do WhatsApp) ---

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    
    # Verifica se é uma mensagem nova (upsert)
    if data.get('event') == 'messages.upsert':
        msg_data = data.get('data', {})
        key = msg_data.get('key', {})
        remote_jid = key.get('remoteJid')
        from_me = key.get('fromMe')
        
        # Ignora mensagens enviadas pelo próprio bot/você
        if not from_me and remote_jid:
            # Extrai o texto (lida com variações da Evolution)
            message_content = msg_data.get('message', {})
            texto = (
                message_content.get('conversation') or 
                message_content.get('extendedTextMessage', {}).get('text')
            )
            
            if texto:
                logging.info(f"Mensagem recebida de {remote_jid}: {texto}")
                # Processa em background (ou direto aqui para simplificar)
                processar_ia(remote_jid, texto)
    
    return jsonify({"status": "recebido"}), 200

# Inicializa o banco ao ligar
with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)