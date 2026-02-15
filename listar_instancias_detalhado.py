import requests
import json

EVOLUTION_URL = "http://78.142.242.82:8080"
API_KEY = "Josevfg2409@"

print("\n" + "=" * 80)
print("📋 LISTANDO TODAS AS INSTÂNCIAS")
print("=" * 80 + "\n")

try:
    response = requests.get(f"{EVOLUTION_URL}/instance/fetchInstances", 
                          headers={"apikey": API_KEY}, 
                          timeout=5)
    
    print(f"Status da resposta: {response.status_code}\n")
    
    if response.status_code == 200:
        data = response.json()
        
        print("Resposta completa da API:")
        print(json.dumps(data, indent=2))
        print()
        
        if isinstance(data, list):
            if len(data) == 0:
                print("❌ NENHUMA INSTÂNCIA ENCONTRADA!")
                print()
                print("Isso significa que você precisa criar a instância.")
                print()
                print("=" * 80)
                print("🌐 COMO CRIAR PELA INTERFACE WEB:")
                print("=" * 80)
                print()
                print("1. Abra no navegador: http://78.142.242.82:8080/manager")
                print()
                print("2. Procure um botão/link escrito:")
                print("   - 'Create Instance' ou")
                print("   - '+ New Instance' ou") 
                print("   - 'Add Instance'")
                print()
                print("3. Preencha:")
                print("   Nome: BotMedico")
                print("   (Outras opções deixe padrão)")
                print()
                print("4. Clique em 'Create' ou 'Criar'")
                print()
                print("5. Um QR Code vai aparecer")
                print()
                print("6. Escaneie com WhatsApp do 5521972706068")
                print()
                print("7. Aguarde conectar (ícone verde ✅)")
                print()
                print("8. Execute novamente: python3 configurar_webhook.py")
                print()
            else:
                print(f"✅ Encontradas {len(data)} instância(s):\n")
                for i, inst in enumerate(data, 1):
                    instance_info = inst.get('instance', {})
                    name = instance_info.get('instanceName', 'N/A')
                    state = instance_info.get('state', 'N/A')
                    status = instance_info.get('status', 'N/A')
                    
                    print(f"{i}. Nome: {name}")
                    print(f"   Estado: {state}")
                    print(f"   Status: {status}")
                    print()
                
                # Verifica se BotMedico existe
                has_botmedico = any(
                    inst.get('instance', {}).get('instanceName') == 'BotMedico' 
                    for inst in data
                )
                
                if has_botmedico:
                    print("✅ Instância 'BotMedico' ENCONTRADA!")
                    print()
                    print("Se o webhook está configurado e mesmo assim não funciona,")
                    print("execute: docker logs -f bot_medico")
                    print("E envie uma mensagem para ver se chega no webhook.")
                else:
                    print("❌ Instância 'BotMedico' NÃO encontrada!")
                    print()
                    print("As instâncias acima têm nomes diferentes.")
                    print("Você pode:")
                    print("1. Deletar as existentes e criar 'BotMedico' ou")
                    print("2. Usar uma das existentes (se houver)")
        else:
            print("⚠️ Formato de resposta inesperado")
            print(f"Tipo: {type(data)}")
    else:
        print(f"❌ Erro: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"❌ Erro ao conectar: {e}")
    print()
    print("Verifique se a Evolution API está rodando:")
    print("docker ps | grep evolution")

print("\n" + "=" * 80)
