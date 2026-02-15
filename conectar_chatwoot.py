import requests
import json

# --- PREENCHA AQUI ---
CHATWOOT_TOKEN = 'COLE_SEU_TOKEN_AQUI'  # <--- O TOKEN DO PASSO 2
CHATWOOT_ACCOUNT_ID = "1"               # <--- Geralmente é 1

# --- NÃO MEXA AQUI (Configurado para sua VPS) ---
EVOLUTION_URL = "http://localhost:8080"
INSTANCE_NAME = "BotMedico"
API_KEY = "Josevfg2409@"

# Endereço interno que a Evolution vai usar para falar com o Chatwoot
# (Confirmado pelo seu docker ps: o nome é chatwoot_base)
CHATWOOT_DOCKER_URL = "http://chatwoot_base:3000"

def configurar_integracao():
    print(f"🔌 Conectando {INSTANCE_NAME} ao Chatwoot...")
    
    url = f"{EVOLUTION_URL}/chatwoot/set/{INSTANCE_NAME}"
    headers = {
        "apikey": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "enabled": True,
        "accountId": CHATWOOT_ACCOUNT_ID,
        "token": CHATWOOT_TOKEN,
        "url": CHATWOOT_DOCKER_URL, 
        "signMsg": True,
        "reopenConversation": True,
        "conversationPending": False,
        "importContacts": True,
        "mergeBrazilContacts": True
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status: {response.status_code}")
        print(response.json())
        
        if response.status_code in [200, 201]:
            print("\n✅ SUCESSO! Integração feita.")
            print("Envie um 'Oi' no WhatsApp do bot e veja se aparece no Chatwoot (porta 3001).")
        else:
            print("\n❌ Erro na API Evolution.")
            
    except Exception as e:
        print(f"\n❌ Erro de conexão: {e}")

if __name__ == "__main__":
    configurar_integracao()
