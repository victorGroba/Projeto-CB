import requests
import json

# Configurações
EVOLUTION_URL = "http://78.142.242.82:8080"
API_KEY = "Josevfg2409@"
INSTANCE_NAME = "BotMedico"

def verificar_instancia():
    """Verifica o status da instância"""
    print("=" * 80)
    print("🔍 VERIFICANDO INSTÂNCIA DO BOT")
    print("=" * 80)
    print()
    
    url = f"{EVOLUTION_URL}/instance/fetchInstances"
    headers = {"apikey": API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            instances = response.json()
            
            for inst in instances:
                instance_data = inst.get('instance', {})
                if instance_data.get('instanceName') == INSTANCE_NAME:
                    print(f"✅ Instância encontrada: {INSTANCE_NAME}")
                    print(f"   Status: {instance_data.get('status')}")
                    print(f"   Estado: {instance_data.get('state')}")
                    print(f"   Número: {instance_data.get('number', 'Não conectado')}")
                    print()
                    return True
            
            print(f"❌ Instância '{INSTANCE_NAME}' não encontrada!")
            print()
            print("Instâncias disponíveis:")
            for inst in instances:
                print(f"  - {inst.get('instance', {}).get('instanceName')}")
            return False
        else:
            print(f"❌ Erro ao consultar API: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def testar_envio_mensagem(numero_destino="5521972706068"):
    """Testa envio de mensagem para um número específico"""
    print("=" * 80)
    print("📤 TESTANDO ENVIO DE MENSAGEM")
    print("=" * 80)
    print()
    
    url = f"{EVOLUTION_URL}/message/sendText/{INSTANCE_NAME}"
    headers = {
        "apikey": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "number": numero_destino,
        "text": "🤖 Teste de envio do bot Clara\n\nSe você recebeu esta mensagem, o bot está funcionando corretamente!"
    }
    
    try:
        print(f"Enviando mensagem para: {numero_destino}")
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"Status: {response.status_code}")
        print(f"Resposta: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 201:
            print("\n✅ Mensagem enviada com sucesso!")
            return True
        else:
            print("\n❌ Falha ao enviar mensagem")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def verificar_webhook():
    """Verifica se o webhook está configurado"""
    print("=" * 80)
    print("🔗 VERIFICANDO WEBHOOK")
    print("=" * 80)
    print()
    
    url = f"{EVOLUTION_URL}/webhook/find/{INSTANCE_NAME}"
    headers = {"apikey": API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            webhook_data = response.json()
            print(f"Webhook configurado:")
            print(json.dumps(webhook_data, indent=2))
            print()
            
            # Verifica se está apontando para o bot correto
            webhook_url = webhook_data.get('webhook', {}).get('url', '')
            if 'bot-medico:5000/webhook' in webhook_url or 'bot_medico:5000/webhook' in webhook_url:
                print("✅ Webhook configurado corretamente!")
            else:
                print(f"⚠️ Webhook pode estar incorreto: {webhook_url}")
                print(f"   Esperado: http://bot-medico:5000/webhook")
            
            return True
        else:
            print(f"❌ Erro ao consultar webhook: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    print("\n🤖 DIAGNÓSTICO DO BOT CLARA\n")
    
    # 1. Verifica instância
    if verificar_instancia():
        print()
        
        # 2. Verifica webhook
        verificar_webhook()
        print()
        
        # 3. Pergunta se quer testar envio
        print("=" * 80)
        resposta = input("\nDeseja testar envio de mensagem? (s/n): ")
        if resposta.lower() == 's':
            numero = input("Digite o número (com código do país, ex: 5521972706068): ")
            testar_envio_mensagem(numero)
    
    print("\n" + "=" * 80)
    print("✅ Diagnóstico concluído!")
    print("=" * 80)
