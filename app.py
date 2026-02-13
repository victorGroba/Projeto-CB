import os
import logging
import requests
import json
import threading
import google.generativeai as genai
from flask import Flask, request, jsonify
from database import get_db_connection, init_db
from tools import tools_config, ferramenta_ver_agenda, agendar_consulta

# --- Configurações ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# Credenciais (Vêm do Docker environment)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
EVOLUTION_URL = os.getenv("EVOLUTION_URL")
EVOLUTION_APIKEY = os.getenv("EVOLUTION_APIKEY")
INSTANCE_NAME = os.getenv("INSTANCE_NAME", "BotMedico")

# Configura o Gemini
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
        
        # O banco retorna do mais recente para o antigo, precisamos inverter
        historico = []
        for row in reversed(rows):
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
        logging.info(f"📤 Enviando resposta para: {remote_jid}")
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200 or response.status_code == 201:
            logging.info(f"✅ Mensagem enviada com sucesso para {remote_jid}")
        else:
            logging.error(f"❌ Erro ao enviar para {remote_jid}: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"❌ Exceção ao enviar para Evolution: {e}")

# --- Cérebro da IA (Gemini + Tools) ---

def processar_ia(remote_jid, mensagem_usuario):
    """Processa a mensagem do usuário com o Gemini"""
    logging.info(f"🧠 Iniciando processamento IA para {remote_jid}")
    try:
        # 1. Recupera histórico
        historico = buscar_historico(remote_jid)
        
        # 2. Adiciona a mensagem atual (apenas localmente para o prompt, pois já salvamos no webhook)
        # OBS: Se você quiser salvar aqui, descomente a linha de salvar_mensagem no final
        
        # 3. Configura o Modelo e o System Prompt
        system_instruction = """
Você é a Clara, secretária virtual do Dr. Victor.
Sua função é agendar consultas e tirar dúvidas sobre a clínica.

REGRAS IMPORTANTES:
1. SEMPRE que perguntarem sobre horários disponíveis, USE a ferramenta 'ver_agenda'. NUNCA invente horários.
2. Para agendar, você PRECISA coletar: Nome Completo, Telefone e Data de Nascimento.
3. Após confirmar todas as informações, use a ferramenta 'agendar_consulta'.
4. Seja extremamente educada, profissional e empática.
5. Se não tiver certeza de algo, pergunte ao paciente.
6. Confirme todas as informações antes de agendar.
7. Responda de forma curta e natural, como no WhatsApp.

HORÁRIO DE FUNCIONAMENTO:
- Segunda a Sexta: 8h às 18h
- Consultas de 1 hora
"""
        
        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            tools=tools_config,
            system_instruction=system_instruction
        )

        chat = model.start_chat(history=historico)

        # Envia a mensagem do usuário para o Gemini
        response = chat.send_message(mensagem_usuario)
        
        # --- Lógica de Function Calling ---
        max_iterations = 5
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Verifica se há chamada de função
            if not response.candidates or not response.candidates[0].content.parts:
                break
                
            first_part = response.candidates[0].content.parts[0]
            
            # Se não for chamada de função, é texto final. Sai do loop.
            if not hasattr(first_part, 'function_call'):
                break
            
            # Executa a ferramenta
            fn = first_part.function_call
            logging.info(f"🔧 Gemini chamou a ferramenta: {fn.name}")
            
            function_response = None
            
            if fn.name == 'ver_agenda':
                args = dict(fn.args)
                dados_agenda = ferramenta_ver_agenda(args.get('data_relativa', 'hoje'))
                function_response = {'result': dados_agenda}
                
            elif fn.name == 'agendar_consulta':
                args = dict(fn.args)
                resultado = agendar_consulta(
                    nome_paciente=args.get('nome_paciente'),
                    telefone=args.get('telefone'),
                    data=args.get('data'),
                    horario=args.get('horario')
                )
                function_response = {'result': resultado}
            
            # Envia o resultado da função de volta para o Gemini
            if function_response:
                response = chat.send_message(
                    genai.protos.Content(
                        parts=[genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=fn.name,
                                response=function_response
                            )
                        )]
                    )
                )
            else:
                break

        # Texto final da resposta
        if response.text:
            resposta_texto = response.text
            
            # Salva no banco e envia
            salvar_mensagem(remote_jid, "user", mensagem_usuario)
            salvar_mensagem(remote_jid, "model", resposta_texto)
            enviar_whatsapp(remote_jid, resposta_texto)
            
            logging.info(f"✅ Ciclo concluído para {remote_jid}")
        else:
            logging.warning("⚠️ Gemini não retornou texto final.")

    except Exception as e:
        logging.error(f"❌ Erro no processamento da IA: {e}", exc_info=True)
        # Opcional: Enviar mensagem de erro para o usuário
        # enviar_whatsapp(remote_jid, "Desculpe, tive um erro técnico momentâneo.")

# --- Rotas ---

@app.route('/webhook', methods=['POST'])
def webhook():
    """Recebe mensagens do WhatsApp via Evolution API"""
    try:
        data = request.json
        # logging.info(f"📥 Webhook recebido: {json.dumps(data, indent=2)}") # Descomente para debug total
        
        # Verifica se é uma mensagem nova
        if data.get('event') == 'messages.upsert':
            msg_data = data.get('data', {})
            key = msg_data.get('key', {})
            remote_jid = key.get('remoteJid')
            from_me = key.get('fromMe', False)
            
            # CORREÇÃO PRINCIPAL: Pega o sender (número real) em vez do remoteJid (que pode ser LID)
            sender_jid = data.get('sender')
            
            # Ignora mensagens enviadas pelo próprio bot
           # if from_me:
           #     logging.info(f"⏭️  Ignorando mensagem própria")
            #    return jsonify({"status": "ignored_own_message"}), 200
            
            # Lógica para definir quem recebe a resposta
            target_jid = remote_jid
            
            # Se for grupo, mantém o remoteJid (ID do grupo). Se for privado, usa o sender.
            if remote_jid and '@g.us' in remote_jid:
                logging.info(f"⏭️  Ignorando mensagem de grupo: {remote_jid}")
                return jsonify({"status": "ignored_group"}), 200
            else:
                # Se for conversa privada, usa o sender para garantir que não é LID
                if sender_jid:
                    target_jid = sender_jid
            
            if target_jid:
                # Extrai o texto da mensagem
                message_content = msg_data.get('message', {})
                texto = None
                
                if 'conversation' in message_content:
                    texto = message_content['conversation']
                elif 'extendedTextMessage' in message_content:
                    texto = message_content['extendedTextMessage'].get('text')
                
                if texto and texto.strip():
                    logging.info(f"💬 Mensagem de {target_jid}: {texto}")
                    
                    # CORREÇÃO 2: Executa em Thread separada para não travar o webhook
                    thread = threading.Thread(target=processar_ia, args=(target_jid, texto))
                    thread.start()
                    
                else:
                    logging.warning(f"⚠️  Mensagem sem texto de {target_jid}")
        
        return jsonify({"status": "recebido"}), 200
        
    except Exception as e:
        logging.error(f"❌ Erro no webhook: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Endpoint de health check"""
    return jsonify({
        "status": "ok",
        "evolution_url": EVOLUTION_URL,
        "instance_name": INSTANCE_NAME
    }), 200

# Inicializa o banco ao ligar
with app.app_context():
    try:
        init_db()
        logging.info("📦 Banco de dados inicializado.")
    except Exception as e:
        logging.error(f"❌ Erro ao iniciar banco: {e}")

if __name__ == '__main__':
    # Em produção, use Gunicorn. Para desenvolvimento:
    app.run(host='0.0.0.0', port=5000, debug=True)