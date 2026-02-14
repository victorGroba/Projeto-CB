import requests
import json

# --- CONFIGURAÇÕES ---
CHATWOOT_TOKEN = 'QifaLugsbW88qBoLmXSPi9YK' 

# URL da Evolution API (acessível pelo localhost do servidor)
EVOLUTION_URL = "http://localhost:8080" 
INSTANCE_NAME = "BotMedico"
API_KEY = "Josevfg2409@"

# URL interna do Docker (A Evolution usa essa para falar com o Chatwoot)
CHATWOOT_DOCKER_URL = "http://78.142.242.82:3001" 

def configurar_integracao():
    url = f"{EVOLUTION_URL}/chatwoot/set/{INSTANCE_NAME}"
    
    headers = {
        "apikey": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "enabled": True,
        "accountId": "1",            # <--- CORREÇÃO: Tem que ser String ("1")
        "token": CHATWOOT_TOKEN,
        "url": CHATWOOT_DOCKER_URL,
        "signMsg": True,
        "reopenConversation": True,
        "conversationPending": False
    }
    
    print(f"🔌 Conectando {INSTANCE_NAME} ao Chatwoot...")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            # A Evolution retorna { "status": 200, ... } ou { "status": 201, ... } quando dá certo
            if data.get('status') in [200, 201]:
                print("\n✅ SUCESSO! Integração configurada.")
                print("Agora as mensagens do WhatsApp aparecerão no Chatwoot.")
            else:
                print("\n⚠️  Atenção: A API respondeu, mas verifique o conteúdo:")
                print(json.dumps(data, indent=2))
        else:
            print(f"\n❌ ERRO: Status {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"\n❌ ERRO DE CONEXÃO: {e}")

if __name__ == "__main__":
    configurar_integracao()
