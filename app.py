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

# --- Funções de Descoberta de Número Real ---

def descobrir_numero_real_lid(lid_jid, push_name, sender_field):
    """
    Tenta descobrir o número real a partir de um @lid
    Usa múltiplas estratégias para encontrar o número
    """
    try:
        # Extrai apenas o número do @lid
        lid_number = lid_jid.split('@')[0]
        
        logging.info(f"🔍 Tentando descobrir número real para @lid: {lid_number}")
        
        # ESTRATÉGIA 1: Verificar se o número @lid é válido como @s.whatsapp.net
        url = f"{EVOLUTION_URL}/chat/whatsappNumbers/{INSTANCE_NAME}"
        headers = {
            "apikey": EVOLUTION_APIKEY,
            "Content-Type": "application/json"
        }
        payload = {"numbers": [lid_number]}
        
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                result = data[0]
                if result.get('exists'):
                    numero_real = result.get('jid')
                    logging.info(f"✅ Número real descoberto via API: {numero_real}")
                    return numero_real
                else:
                    logging.warning(f"⚠️ API diz que número {lid_number} não existe")
        
        # ESTRATÉGIA 2: Usar o sender se disponível (número de quem enviou)
        # Mas CUIDADO: sender pode ser o dono do bot, não o contato!
        if sender_field and '@s.whatsapp.net' in sender_field:
            # Extrai só o número do sender
            sender_number = sender_field.split('@')[0]
            # Valida se é diferente do dono do bot (evita loop)
            if sender_number != lid_number:
                logging.info(f"⚠️ Tentando usar sender como alternativa: {sender_field}")
                return sender_field
        
        # ESTRATÉGIA 3: Se nada funcionar, retorna None
        logging.error(f"❌ Não foi possível descobrir número real para @lid: {lid_number}")
        return None
        
    except Exception as e:
        logging.error(f"❌ Erro ao descobrir número real: {e}")
        return None

# --- Funções de Envio (Evolution API) ---

def enviar_whatsapp(remote_jid, texto):
    """Envia a resposta final para o WhatsApp via Evolution API"""
    url = f"{EVOLUTION_URL}/message/sendText/{INSTANCE_NAME}"
    headers = {
        "apikey": EVOLUTION_APIKEY,
        "Content-Type": "application/json"
    }
    
    # Garante que o número está no formato correto
    numero_envio = remote_jid
    
    payload = {
        "number": numero_envio,
        "text": texto
    }
    
    try:
        logging.info(f"📤 Enviando resposta para: {numero_envio}")
        logging.info(f"🔍 Payload: {payload}")
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200 or response.status_code == 201:
            logging.info(f"✅ Mensagem enviada com sucesso para {numero_envio}")
        else:
            logging.error(f"❌ Erro ao enviar para {numero_envio}: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"❌ Exceção ao enviar para Evolution: {e}")

# --- Cérebro da IA (Gemini + Tools) ---

def processar_ia(numero_para_envio, numero_limpo, mensagem_usuario):
    """Processa a mensagem do usuário com o Gemini
    
    Args:
        numero_para_envio: Número completo com @lid ou @s.whatsapp.net para enviar resposta
        numero_limpo: Número limpo para salvar no banco de dados
        mensagem_usuario: Texto da mensagem
    """
    logging.info(f"🧠 Iniciando processamento IA para {numero_limpo}")
    try:
        # 1. Recupera histórico usando o número limpo
        historico = buscar_historico(numero_limpo)
        
        # 2. Configura o Modelo e o System Prompt
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
            
            # Salva no banco usando número limpo
            salvar_mensagem(numero_limpo, "user", mensagem_usuario)
            salvar_mensagem(numero_limpo, "model", resposta_texto)
            
            # Envia usando número completo com @lid ou @s.whatsapp.net
            enviar_whatsapp(numero_para_envio, resposta_texto)
            
            logging.info(f"✅ Ciclo concluído para {numero_limpo}")
        else:
            logging.warning("⚠️ Gemini não retornou texto final.")

    except Exception as e:
        logging.error(f"❌ Erro no processamento da IA: {e}", exc_info=True)

# --- Rotas ---

@app.route('/webhook', methods=['POST'])
def webhook():
    """Recebe mensagens do WhatsApp via Evolution API"""
    try:
        data = request.json
        logging.info(f"📥 Webhook recebido: {json.dumps(data, indent=2)[:500]}...")
        
        # Verifica se é uma mensagem nova
        if data.get('event') == 'messages.upsert':
            msg_data = data.get('data', {})
            key = msg_data.get('key', {})
            remote_jid = key.get('remoteJid')
            from_me = key.get('fromMe', False)
            
            # 🔥 CORREÇÃO 1: Ignora mensagens enviadas pelo próprio bot
            if from_me:
                logging.info(f"⏭️ Ignorando mensagem própria (from_me=True)")
                return jsonify({"status": "ignored_own_message"}), 200
            
            # 🔥 CORREÇÃO 2: Ignora mensagens de grupos
            if remote_jid and '@g.us' in remote_jid:
                logging.info(f"⏭️ Ignorando mensagem de grupo: {remote_jid}")
                return jsonify({"status": "ignored_group"}), 200
            
            # 🔥 CORREÇÃO 3: Descobrir número real automaticamente quando for @lid
            target_jid = remote_jid
            sender_field = data.get('sender')
            push_name = msg_data.get('pushName', '')
            
            logging.info(f"🔍 DEBUG - remoteJid: {remote_jid}")
            logging.info(f"🔍 DEBUG - sender field: {sender_field}")
            logging.info(f"🔍 DEBUG - pushName: {push_name}")
            
            # Se for @lid, tenta descobrir o número real AUTOMATICAMENTE
            if '@lid' in target_jid:
                logging.info(f"⚠️ Detectado @lid - tentando descobrir número real...")
                numero_real = descobrir_numero_real_lid(target_jid, push_name, sender_field)
                
                if numero_real:
                    target_jid = numero_real
                    logging.info(f"✅ Usando número descoberto: {target_jid}")
                else:
                    logging.error(f"❌ Não foi possível descobrir número real para @lid - ignorando mensagem")
                    # Registra para análise posterior
                    logging.error(f"📊 Dados para debug: remoteJid={remote_jid}, sender={sender_field}, pushName={push_name}")
                    return jsonify({"status": "cannot_resolve_lid"}), 200
            
            logging.info(f"🔍 DEBUG - target_jid final: {target_jid}")
            
            numero_para_envio = target_jid
            numero_limpo = target_jid.split('@')[0] if '@' in target_jid else target_jid
            
            logging.info(f"🔍 DEBUG - numero_para_envio: {numero_para_envio}")
            logging.info(f"🔍 DEBUG - numero_limpo (banco): {numero_limpo}")
            
            if numero_para_envio:
                # Extrai o texto da mensagem
                message_content = msg_data.get('message', {})
                texto = None
                
                if 'conversation' in message_content:
                    texto = message_content['conversation']
                elif 'extendedTextMessage' in message_content:
                    texto = message_content['extendedTextMessage'].get('text')
                
                if texto and texto.strip():
                    logging.info(f"💬 Mensagem de {numero_limpo}: {texto}")
                    
                    # 🔥 CORREÇÃO 4: Passa ambos os números - um para enviar, outro para salvar
                    thread = threading.Thread(target=processar_ia, args=(numero_para_envio, numero_limpo, texto))
                    thread.start()
                    
                else:
                    logging.warning(f"⚠️ Mensagem sem texto de {numero_limpo}")
        
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

