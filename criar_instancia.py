import requests
import json
import time

# Configurações
EVOLUTION_URL = "http://78.142.242.82:8080"
API_KEY = "Josevfg2409@"
INSTANCE_NAME = "BotMedico"

def criar_instancia():
    """Cria uma nova instância do WhatsApp"""
    print("=" * 80)
    print("🚀 CRIANDO INSTÂNCIA DO BOT")
    print("=" * 80)
    print()
    
    url = f"{EVOLUTION_URL}/instance/create"
    headers = {
        "apikey": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "instanceName": INSTANCE_NAME,
        "qrcode": True,
        "integration": "WHATSAPP-BAILEYS"
    }
    
    print(f"Criando instância: {INSTANCE_NAME}")
    print()
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            print("\n✅ Instância criada com sucesso!")
            print()
            print("Dados da instância:")
            print(json.dumps(data, indent=2))
            print()
            return True
        else:
            print(f"\n❌ Erro ao criar instância")
            print(f"Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def buscar_qrcode():
    """Busca o QR Code para conectar o WhatsApp"""
    print("=" * 80)
    print("📱 BUSCANDO QR CODE")
    print("=" * 80)
    print()
    
    url = f"{EVOLUTION_URL}/instance/connect/{INSTANCE_NAME}"
    headers = {
        "apikey": API_KEY
    }
    
    print("Gerando QR Code...")
    print("(Aguarde alguns segundos)")
    print()
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Tenta pegar o QR code de diferentes formatos possíveis
            qrcode = None
            if isinstance(data, dict):
                qrcode = data.get('qrcode', {}).get('code') or data.get('code') or data.get('base64')
            
            if qrcode:
                print("✅ QR Code gerado!")
                print()
                print("=" * 80)
                print("📱 ESCANEIE ESTE QR CODE COM O WHATSAPP 5521972706068")
                print("=" * 80)
                print()
                print(qrcode)
                print()
                print("=" * 80)
                print()
                print("COMO ESCANEAR:")
                print("1. Abra o WhatsApp do número 5521972706068")
                print("2. Toque em Menu (⋮) ou Configurações")
                print("3. Toque em 'Aparelhos conectados'")
                print("4. Toque em 'Conectar um aparelho'")
                print("5. Escaneie o QR Code acima")
                print()
                return True
            else:
                print("⚠️ QR Code não encontrado na resposta")
                print("Resposta completa:")
                print(json.dumps(data, indent=2))
                print()
                print("💡 Tente acessar: http://78.142.242.82:8080/manager")
                print("   E escaneie o QR Code pela interface web")
                return False
                
        else:
            print(f"❌ Erro ao buscar QR Code: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def verificar_conexao():
    """Verifica se a instância foi conectada"""
    print("=" * 80)
    print("🔍 VERIFICANDO CONEXÃO")
    print("=" * 80)
    print()
    
    url = f"{EVOLUTION_URL}/instance/connectionState/{INSTANCE_NAME}"
    headers = {
        "apikey": API_KEY
    }
    
    max_tentativas = 30  # 30 tentativas (1 minuto)
    tentativa = 0
    
    print("Aguardando você escanear o QR Code...")
    print("(Verificando a cada 2 segundos)")
    print()
    
    while tentativa < max_tentativas:
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                state = data.get('instance', {}).get('state')
                
                if state == 'open':
                    print("✅ CONECTADO COM SUCESSO!")
                    print()
                    print("Informações da conexão:")
                    print(json.dumps(data, indent=2))
                    return True
                else:
                    print(f"⏳ Tentativa {tentativa + 1}/{max_tentativas} - Status: {state}")
                    
            tentativa += 1
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            tentativa += 1
            time.sleep(2)
    
    print("\n⏱️ Tempo esgotado. QR Code não foi escaneado.")
    print()
    print("💡 Você pode tentar novamente executando:")
    print("   python3 criar_instancia.py")
    return False

def configurar_webhook():
    """Configura o webhook após conectar"""
    print()
    print("=" * 80)
    print("🔗 CONFIGURANDO WEBHOOK")
    print("=" * 80)
    print()
    
    webhook_url = "http://bot-medico:5000/webhook"
    
    url = f"{EVOLUTION_URL}/webhook/set/{INSTANCE_NAME}"
    headers = {
        "apikey": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "url": webhook_url,
        "webhook_by_events": True,
        "webhook_base64": False,
        "events": [
            "QRCODE_UPDATED",
            "MESSAGES_UPSERT",
            "MESSAGES_UPDATE",
            "MESSAGES_DELETE",
            "SEND_MESSAGE",
            "CONNECTION_UPDATE"
        ]
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code in [200, 201]:
            print("✅ Webhook configurado!")
            print(f"   URL: {webhook_url}")
            return True
        else:
            print(f"⚠️ Erro ao configurar webhook: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def testar_envio():
    """Testa o envio de mensagem"""
    print()
    print("=" * 80)
    print("📤 TESTE DE ENVIO")
    print("=" * 80)
    print()
    
    numero = input("Digite um número para testar (ex: 5521999999999): ").strip()
    
    if not numero:
        print("Teste cancelado.")
        return
    
    url = f"{EVOLUTION_URL}/message/sendText/{INSTANCE_NAME}"
    headers = {
        "apikey": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "number": numero,
        "text": "🤖 *Teste do Bot Clara*\n\nOlá! Este é um teste de envio.\n\nSe você recebeu esta mensagem, o bot está funcionando corretamente! ✅"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 201:
            print("✅ Mensagem enviada com sucesso!")
            print()
            print("Verifique se a mensagem chegou no número informado.")
        else:
            print(f"❌ Erro ao enviar: {response.status_code}")
            print(f"Resposta: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    print("\n🤖 CONFIGURAÇÃO COMPLETA DO BOT CLARA\n")
    
    # Passo 1: Criar instância
    if criar_instancia():
        print()
        time.sleep(2)
        
        # Passo 2: Buscar QR Code
        if buscar_qrcode():
            print()
            
            # Passo 3: Aguardar conexão
            if verificar_conexao():
                
                # Passo 4: Configurar webhook
                configurar_webhook()
                
                # Passo 5: Teste (opcional)
                print()
                resposta = input("Deseja fazer um teste de envio? (s/n): ").lower()
                if resposta == 's':
                    testar_envio()
                
                print()
                print("=" * 80)
                print("✅ CONFIGURAÇÃO CONCLUÍDA!")
                print("=" * 80)
                print()
                print("📋 PRÓXIMOS PASSOS:")
                print()
                print("1. Reinicie o bot:")
                print("   docker-compose restart bot-medico")
                print()
                print("2. Verifique os logs:")
                print("   docker logs -f bot_medico")
                print()
                print("3. Envie uma mensagem de teste para: 5521972706068")
                print()
                print("4. A resposta deve ir para quem enviou!")
                print()
    
    print()
    print("=" * 80)
    print("Script finalizado!")
    print("=" * 80)
