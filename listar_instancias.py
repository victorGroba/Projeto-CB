import requests
import json

# Configurações
EVOLUTION_URL = "http://78.142.242.82:8080"
API_KEY = "Josevfg2409@"

def listar_instancias():
    """Lista todas as instâncias disponíveis na Evolution API"""
    url = f"{EVOLUTION_URL}/instance/fetchInstances"
    headers = {
        "apikey": API_KEY
    }
    
    print("=" * 60)
    print("📋 LISTANDO INSTÂNCIAS DA EVOLUTION API")
    print("=" * 60)
    print()
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                print(f"✅ Encontradas {len(data)} instância(s):")
                print()
                
                for i, instance in enumerate(data, 1):
                    print(f"{i}. Nome: {instance.get('instance', {}).get('instanceName', 'N/A')}")
                    print(f"   ID: {instance.get('instance', {}).get('instanceId', 'N/A')}")
                    print(f"   Status: {instance.get('instance', {}).get('status', 'N/A')}")
                    print(f"   Conectado: {'Sim' if instance.get('instance', {}).get('state') == 'open' else 'Não'}")
                    print()
                
                # Mostra o JSON completo para debug
                print("=" * 60)
                print("📄 JSON COMPLETO (para debug):")
                print("=" * 60)
                print(json.dumps(data, indent=2))
                
                return data
            else:
                print("⚠️ Nenhuma instância encontrada!")
                print()
                print("💡 Você precisa criar uma instância primeiro.")
                print()
                print("Como criar:")
                print("1. Acesse: http://78.142.242.82:8080/manager")
                print("2. Crie uma nova instância")
                print("3. Anote o nome da instância")
                print("4. Execute este script novamente")
                return None
                
        else:
            print(f"❌ Erro ao listar instâncias!")
            print(f"Status Code: {response.status_code}")
            print(f"Resposta: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ ERRO na requisição: {e}")
        return None

def main():
    instancias = listar_instancias()
    
    if instancias and len(instancias) > 0:
        print()
        print("=" * 60)
        print("🎯 PRÓXIMO PASSO")
        print("=" * 60)
        print()
        print("Agora você precisa:")
        print("1. Anotar o nome EXATO da instância (case-sensitive)")
        print("2. Editar o arquivo 'configurar_webhook.py'")
        print("3. Alterar a linha: INSTANCE_NAME = 'ZapBot'")
        print("4. Para: INSTANCE_NAME = 'NOME_DA_SUA_INSTANCIA'")
        print("5. Executar: python3 configurar_webhook.py")
        print()

if __name__ == "__main__":
    main()
