import os
import logging
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

# Configuração de Logs
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Habilita CORS para permitir requisições do seu Front-end (Next.js/React)
CORS(app)

# Pega a chave da API (tenta pegar do sistema, se não achar, usa a que você passou)
API_KEY = os.getenv("GEMINI_API_KEY")

# Defina aqui a personalidade do Bot
SYSTEM_PROMPT = "Você é uma secretária eficiente de um consultório. Responda de forma curta e educada."

def chamar_gemini_bruto(user_message):
    # URL da API do Gemini 1.5 Flash (Rápido e barato)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

    headers = {
        "Content-Type": "application/json"
    }

    # Monta o prompt combinando a instrução do sistema + mensagem do usuário
    full_prompt = f"{SYSTEM_PROMPT}\n\nUsuário: {user_message}"

    payload = {
        "contents": [{
            "parts": [{"text": full_prompt}]
        }]
    }

    try:
        # Faz o POST direto
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            dados = response.json()
            # Extrai o texto com segurança
            if 'candidates' in dados and len(dados['candidates']) > 0:
                texto = dados['candidates'][0]['content']['parts'][0]['text']
                return texto
            else:
                return "O modelo não retornou uma resposta válida (conteúdo vazio)."
        else:
            logging.error(f"Erro Google: {response.text}")
            return f"Erro na API do Google: {response.status_code}"
            
    except Exception as e:
        logging.error(f"Erro de conexão: {str(e)}")
        return "Erro interno ao conectar com a IA."

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        # Garante que não quebre se vier sem mensagem
        user_message = data.get('message', '')

        if not user_message:
            return jsonify({"error": "Mensagem vazia"}), 400

        logging.info(f"Recebido: {user_message}")

        # Chama a função que fala com o Google
        resposta = chamar_gemini_bruto(user_message)

        return jsonify({"response": resposta})

    except Exception as e:
        logging.error(f"ERRO CRÍTICO: {e}")
        return jsonify({"error": "Erro interno do servidor", "details": str(e)}), 500

if __name__ == '__main__':
    # Rodando em todas as interfaces na porta 5000
    app.run(host='0.0.0.0', port=5000)
