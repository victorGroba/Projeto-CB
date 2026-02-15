import os
import logging
import requests
import json
import threading
import google.generativeai as genai
from flask import Flask, request, jsonify
from database import get_db_connection, init_db, salvar_mensagem, buscar_historico, salvar_lid_mapping, buscar_lid_mapping

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
EVOLUTION_URL = os.getenv("EVOLUTION_URL")
EVOLUTION_APIKEY = os.getenv("EVOLUTION_APIKEY")
INSTANCE_NAME = os.getenv("INSTANCE_NAME", "BotMedico")

genai.configure(api_key=GEMINI_API_KEY)

def descobrir_numero_real_lid(lid_jid, push_name, sender_field):
    try:
        lid_number = lid_jid.split('@')[0]
        
        mapeamentos_manuais = {
            "210067051794535": "5521980377236@s.whatsapp.net"
        }
        
        if lid_number in mapeamentos_manuais:
            numero_correto = mapeamentos_manuais[lid_number]
            logging.info(f"✅ Mapeamento manual: {lid_jid} -> {numero_correto}")
            salvar_lid_mapping(lid_jid, numero_correto, push_name)
            return numero_correto
        
        numero_salvo = buscar_lid_mapping(lid_jid)
        if numero_salvo and '5521972706086' not in numero_salvo:
            return numero_salvo
        
        if len(lid_number) >= 10:
            possivel_numero = f"55{lid_number[:2]}{lid_number[-9:]}@s.whatsapp.net"
            salvar_lid_mapping(lid_jid, possivel_numero, push_name)
            return possivel_numero
        
        return None
    except Exception as e:
        logging.error(f"❌ Erro: {e}")
        return None

def enviar_whatsapp(remote_jid, texto):
    url = f"{EVOLUTION_URL}/message/sendText/{INSTANCE_NAME}"
    headers = {"apikey": EVOLUTION_APIKEY, "Content-Type": "application/json"}
    payload = {"number": remote_jid, "text": texto}
    
    try:
        logging.info(f"📤 Enviando para: {remote_jid}")
        response = requests.post(url, json=payload, headers=headers)
        logging.info(f"✅ Status: {response.status_code}")
    except Exception as e:
        logging.error(f"❌ Erro: {e}")

def processar_ia(numero_para_envio, numero_limpo, mensagem_usuario):
    logging.info(f"🧠 Processando IA para {numero_limpo}")
    try:
        historico = buscar_historico(numero_limpo)
        
        system_instruction = """Você é a Clara, secretária virtual do Dr. Victor.
Seja educada, curta e natural. Colete: Nome, Telefone e Data desejada.
Horário: Segunda a Sexta, 8h às 18h."""
        
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        
        if not historico:
            mensagem = f"{system_instruction}\n\nPaciente: {mensagem_usuario}"
        else:
            mensagem = mensagem_usuario
        
        chat = model.start_chat(history=historico)
        response = chat.send_message(mensagem)
        
        if response.text:
            salvar_mensagem(numero_limpo, "user", mensagem_usuario)
            salvar_mensagem(numero_limpo, "model", response.text)
            enviar_whatsapp(numero_para_envio, response.text)
            logging.info(f"✅ Respondido")
            
    except Exception as e:
        logging.error(f"❌ Erro IA: {e}")
        try:
            enviar_whatsapp(numero_para_envio, "Desculpe, tive um problema técnico.")
        except:
            pass

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        
        if data.get('event') == 'messages.upsert':
            msg_data = data.get('data', {})
            key = msg_data.get('key', {})
            remote_jid = key.get('remoteJid')
            from_me = key.get('fromMe', False)
            
            if from_me or (remote_jid and '@g.us' in remote_jid):
                return jsonify({"status": "ignored"}), 200
            
            sender_jid = remote_jid
            push_name = msg_data.get('pushName', '')
            sender = data.get('sender')

            if '@lid' in sender_jid:
                real_number = descobrir_numero_real_lid(sender_jid, push_name, sender)
                if real_number:
                    sender_jid = real_number
                else:
                    return jsonify({"status": "error_lid"}), 200

            numero_para_envio = sender_jid
            numero_limpo = sender_jid.split('@')[0] if '@' in sender_jid else sender_jid
            
            message_content = msg_data.get('message', {})
            texto = message_content.get('conversation') or message_content.get('extendedTextMessage', {}).get('text')
            
            if texto:
                threading.Thread(target=processar_ia, args=(numero_para_envio, numero_limpo, texto)).start()
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logging.error(f"❌ Webhook: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "online"}), 200

with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
