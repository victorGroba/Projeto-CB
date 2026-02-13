import os
import logging
import requests
import json
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS
from database import get_db_connection, init_db
from tools import tools_config, ferramenta_ver_agenda, agendar_consulta

# --- Configurações ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
CORS(app)

# Credenciais (Vêm do Docker environment)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
EVOLUTION_URL = os.getenv("EVOLUTION_URL")  # Ex: http://evolution_api:8080
EVOLUTION_APIKEY = os.getenv("EVOLUTION_APIKEY")
INSTANCE_NAME = os.getenv("INSTANCE_NAME", "ZapBot")

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
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200 or response.status_code == 201:
            logging.info(f"✅ Mensagem enviada para {remote_jid}")
        else:
            logging.error(f"❌ Erro ao enviar para {remote_jid}: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"❌ Exceção ao enviar para Evolution: {e}")

# --- Cérebro da IA (Gemini + Tools) ---

def processar_ia(remote_jid, mensagem_usuario):
    """Processa a mensagem do usuário com o Gemini"""
    try:
        # 1. Recupera histórico
        historico = buscar_historico(remote_jid)
        
        # 2. Adiciona a mensagem atual
        historico.append({"role": "user", "parts": [mensagem_usuario]})
        
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

HORÁRIO DE FUNCIONAMENTO:
- Segunda a Sexta: 8h às 18h
- Consultas de 1 hora

EXEMPLO DE CONVERSA:
Paciente: "Oi, queria marcar uma consulta"
Clara: "Olá! Fico feliz em ajudar. Qual data você prefere para a consulta?"
Paciente: "Amanhã tem?"
Clara: [USA ver_agenda('amanha')] "Deixe me verificar... Amanhã temos os seguintes horários disponíveis: 9h, 14h e 16h. Qual prefere?"
Paciente: "14h tá bom"
Clara: "Perfeito! Para confirmar, preciso de seu nome completo, telefone e data de nascimento."
"""
        
        model = genai.GenerativeModel(
            model_name='gemini-2.0-flash-exp',
            tools=tools_config,
            system_instruction=system_instruction
        )

        chat = model.start_chat(history=historico[:-1])

        # Envia a mensagem do usuário para o Gemini
        response = chat.send_message(mensagem_usuario)
        
        # --- Lógica de Function Calling ---
        # Loop para lidar com múltiplas chamadas de função
        max_iterations = 5
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Verifica se há chamada de função
            if not response.candidates[0].content.parts:
                break
                
            first_part = response.candidates[0].content.parts[0]
            
            if not hasattr(first_part, 'function_call'):
                break
            
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
        resposta_texto = response.text
        
        # Salva no banco e envia
        salvar_mensagem(remote_jid, "user", mensagem_usuario)
        salvar_mensagem(remote_jid, "model", resposta_texto)
        enviar_whatsapp(remote_jid, resposta_texto)
        
        logging.info(f"✅ Processamento concluído para {remote_jid}")

    except Exception as e:
        logging.error(f"❌ Erro no processamento da IA: {e}", exc_info=True)
        enviar_whatsapp(remote_jid, "Desculpe, tive um erro técnico momentâneo. Pode repetir?")

# --- Rotas ---

@app.route('/webhook', methods=['POST'])
def webhook():
    """Recebe mensagens do WhatsApp via Evolution API"""
    try:
        data = request.json
        logging.info(f"📥 Webhook recebido: {json.dumps(data, indent=2)}")
        
        # Verifica se é uma mensagem nova
        if data.get('event') == 'messages.upsert':
            msg_data = data.get('data', {})
            key = msg_data.get('key', {})
            remote_jid = key.get('remoteJid')
            from_me = key.get('fromMe', False)
            
            # Ignora mensagens enviadas pelo próprio bot
            if from_me:
                logging.info(f"⏭️  Ignorando mensagem própria")
                return jsonify({"status": "ignored_own_message"}), 200
            
            # Ignora mensagens de grupos
            if remote_jid and '@g.us' in remote_jid:
                logging.info(f"⏭️  Ignorando mensagem de grupo")
                return jsonify({"status": "ignored_group"}), 200
            
            if remote_jid:
                # Extrai o texto da mensagem
                message_content = msg_data.get('message', {})
                
                # Tenta várias formas de extrair texto
                texto = None
                if 'conversation' in message_content:
                    texto = message_content['conversation']
                elif 'extendedTextMessage' in message_content:
                    texto = message_content['extendedTextMessage'].get('text')
                elif 'imageMessage' in message_content:
                    texto = message_content['imageMessage'].get('caption', '[Imagem recebida]')
                
                if texto and texto.strip():
                    logging.info(f"💬 Mensagem de {remote_jid}: {texto}")
                    # Processa em background (em produção, use Celery ou similar)
                    processar_ia(remote_jid, texto)
                else:
                    logging.warning(f"⚠️  Mensagem sem texto de {remote_jid}")
        
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

@app.route('/test-send', methods=['POST'])
def test_send():
    """Endpoint de teste para enviar mensagens"""
    data = request.json
    numero = data.get('numero')
    texto = data.get('texto', 'Mensagem de teste do bot!')
    
    if not numero:
        return jsonify({"error": "número é obrigatório"}), 400
    
    enviar_whatsapp(numero, texto)
    return jsonify({"status": "enviado"}), 200

# Inicializa o banco ao ligar
with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
