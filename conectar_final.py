import requests
import json

# ==============================================================================
# CONFIGURAÇÕES JÁ PREENCHIDAS
# ==============================================================================

# Seu Token de Admin (que você acabou de mandar)
CHATWOOT_TOKEN = 'xtgDXtVqNrMvqimjHqSr3Fjs'

# ID da conta (Padrão é 1)
CHATWOOT_ACCOUNT_ID = "1"

# Endereços da VPS (Configurados via Docker Internal)
EVOLUTION_URL = "http://localhost:8080"
INSTANCE_NAME = "BotMedico"
API_KEY = "Josevfg2409@"

# URL que a Evolution vai usar para falar com o Chatwoot
# (Confirmado pelo seu docker ps: o container se chama chatwoot_base)
CHATWOOT_DOCKER_URL = "http://chatwoot.grobatech.online:3001/"

def configurar_integracao():
    print("=" * 60)
    print(f"🔌 CONECTANDO {INSTANCE_NAME} AO CHATWOOT")
    print("=" * 60)
    
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
        "mergeBrazilContacts": True,
        "daysLimitImportMessages": 10, # Importa histórico dos últimos 10 dias
        "organization": "Clinica Dr Victor"
    }
    
    print(f"📡 Enviando dados para Evolution API...")
    print(f"🎯 URL Interna do Chatwoot: {CHATWOOT_DOCKER_URL}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"\nStatus: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print("\n✅ SUCESSO TOTAL! 🚀")
            print("A integração foi realizada.")
            print("\n📋 COMO TESTAR AGORA:")
            print("1. Abra o Chatwoot no navegador (http://IP:3001)")
            print("2. Mande um 'Oi' do seu celular pessoal para o WhatsApp do Bot.")
            print("3. A mensagem DEVE aparecer na hora no Chatwoot.")
        else:
            print("\n❌ ALGO DEU ERRADO:")
            print(response.text)
            
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {e}")

if __name__ == "__main__":
    configurar_integracao()
