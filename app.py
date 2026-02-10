import os
import logging
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from calendar_service import listar_proximos_dias

# --- Configuração de Logs (Crucial para ver os erros) ---
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app) # Permite que o Typebot e outros sites acessem

# --- Configurações ---
API_KEY = os.getenv("GEMINI_API_KEY")

def consultar_gemini(user_message):
    """
    Função que conversa com a IA, injetando o contexto da agenda.
    """
    # 1. Busca a agenda para dar contexto à IA (lê os próximos 3 dias)
    try:
        agenda_info = listar_proximos_dias(3)
    except Exception as e:
        logging.error(f"Erro ao ler agenda: {e}")
        agenda_info = "Erro ao ler agenda. O sistema está parcialmente indisponível."

    # 2. Monta o Prompt de Sistema (A personalidade da Clara)
    system_prompt = f"""
    Você é a Clara, secretária virtual do Dr. Victor.
    
    --- STATUS DA AGENDA (LEITURA APENAS) ---
    {agenda_info}
    -----------------------------------------
    
    INSTRUÇÕES:
    1. Se o paciente perguntar sobre horários, consulte a lista acima.
    2. Ofereça SOMENTE os horários que NÃO estão marcados como 'Ocupado'.
    3. Se o dia estiver "Livre (Dia todo)", sugira horários comerciais (08:00 as 18:00).
    4. Seja curta, educada e direta.
    5. Se o paciente confirmar um horário, peça o Nome Completo dele para agendar.
    """

    # URL da API do Google Gemini 1.5 Flash
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [{"text": f"{system_prompt}\n\nPaciente: {user_message}"}]
        }]
    }
    
    try:
        # Faz a requisição para o Google
        response = requests.post(url, json=payload)
        
        # --- VERIFICAÇÃO DE SUCESSO OU ERRO ---
        if response.status_code == 200:
            # Sucesso! Extrai o texto da resposta
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            # ERRO! Imprime o detalhe no terminal para você ver
            logging.error(f"ERRO GOOGLE (Status {response.status_code}):")
            logging.error(f"DETALHE DO ERRO: {response.text}")
            return "Desculpe, estou verificando a agenda, pode repetir?"
            
    except Exception as e:
        logging.error(f"Erro de conexão com a inteligência: {e}")
        return "Erro interno de conexão com a inteligência."

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        # Tenta pegar a mensagem de várias formas para garantir compatibilidade
        user_message = data.get('message') or data.get('text')
        
        if not user_message:
            logging.warning("Recebi uma requisição vazia do Typebot.")
            return jsonify({"response": "Olá! Como posso ajudar?"}), 200

        logging.info(f"Recebido: {user_message}")

        # Chama a função que fala com o Gemini
        resposta_ia = consultar_gemini(user_message)

        # Retorna para o Typebot
        return jsonify({
            "response": resposta_ia
        })

    except Exception as e:
        logging.error(f"ERRO CRÍTICO NO SERVIDOR: {e}")
        return jsonify({"error": "Erro interno do servidor", "details": str(e)}), 500

if __name__ == '__main__':
    # Roda o servidor (Gunicorn vai substituir isso em produção, mas ok deixar aqui)
    app.run(host='0.0.0.0', port=5000)
