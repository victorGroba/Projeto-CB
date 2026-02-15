import requests

EVOLUTION_URL = "http://localhost:8080"
API_KEY = "Josevfg2409@"

def ativar_globalmente():
    print("🔄 Ativando módulo Chatwoot na Evolution...")
    
    # Endpoint para alterar configurações globais (ou da instância)
    # Na v2 da Evolution, geralmente é via settings/global ou setenv
    # Mas o jeito mais garantido é passar a variável na criação ou via API de settings
    
    # Vamos tentar via endpoint de settings da instância, que força a habilitação
    url = f"{EVOLUTION_URL}/chatwoot/set/BotMedico"
    
    headers = {
        "apikey": API_KEY,
        "Content-Type": "application/json"
    }
    
    # O truque: Tentar enviar, mas se der "Chatwoot is disabled", 
    # significa que precisamos definir a variável de ambiente no Docker.
    
    print("\n⚠️ DIAGNÓSTICO:")
    print("O erro 'Chatwoot is disabled' significa que a Evolution API iniciou com a variável 'CHATWOOT_ENABLED=false' (padrão).")
    print("Precisamos editar o docker-compose.yml para ativar isso permanentemente.")

if __name__ == "__main__":
    ativar_globalmente()
