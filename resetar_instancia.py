import requests
import json
import time

# Configurações
EVOLUTION_URL = "http://78.142.242.82:8080"
API_KEY = "Josevfg2409@"
INSTANCE_NAME = "BotMedico"

def deletar_instancia():
    """Deleta a instância existente"""
    print("=" * 80)
    print("🗑️  DELETANDO INSTÂNCIA ANTIGA")
    print("=" * 80)
    print()
    
    url = f"{EVOLUTION_URL}/instance/delete/{INSTANCE_NAME}"
    headers = {
        "apikey": API_KEY
    }
    
    print(f"Deletando instância: {INSTANCE_NAME}")
    print()
    
    try:
        response = requests.delete(url, headers=headers)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code in [200, 201, 204]:
            print("\n✅ Instância deletada com sucesso!")
            print()
            return True
        elif response.status_code == 404:
            print("\n⚠️ Instância não encontrada (pode já estar deletada)")
            print()
            return True
        else:
            print(f"\n⚠️ Resposta: {response.text}")
            print("\nVou tentar criar mesmo assim...")
            return True
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        print("\nVou tentar continuar mesmo assim...")
        return True

def criar_instancia():
    """Cria uma nova instância do WhatsApp"""
    print("=" * 80)
    print("🚀 CRIANDO NOVA INSTÂNCIA")
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
    print("📱 GERANDO QR CODE")
    print("=" * 80)
    print()
    
    url = f"{EVOLUTION_URL}/instance/connect/{INSTANCE_NAME}"
    headers = {
        "apikey": API_KEY
    }
    
    print("Gerando QR Code...")
    print("(Aguarde alguns segundos)")
    print()
    
    # Aguarda um pouco para a instância estar pronta
    time.sleep(3)
    
    try:
        response = requests.get(url, headers=headers)
        
        print(f"Status da resposta: {response.status_code}")
        print()
        
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
                print("📲 COMO ESCANEAR:")
                print("1. Abra o WhatsApp do número 5521972706068")
                print("2. Toque em Menu (⋮) ou Configurações")
                print("3. Toque em 'Aparelhos conectados'")
                print("4. Toque em 'Conectar um aparelho'")
                print("5. Escaneie o QR Code acima")
                print()
                print("⏱️  Você tem 60 segundos para escanear!")
                print()
                return True
            else:
                print("⚠️ QR Code não encontrado na resposta")
                print()
                print("📋 Resposta completa da API:")
                print(json.dumps(data, indent=2))
                print()
                print("=" * 80)
                print("💡 SOLUÇÃO ALTERNATIVA:")
                print("=" * 80)
                print()
                print("Acesse pelo navegador:")
                print(f"http://78.142.242.82:8080/manager")
                print()
                print("1. Procure pela instância 'BotMedico'")
                print("2. Clique em 'Connect'")
                print("3. Escaneie o QR Code que aparecer")
                print()
                return False
                
        else:
            print(f"❌ Erro ao buscar QR Code: {response.status_code}")
            print(f"Resposta: {response.text}")
            print()
            print("=" * 80)
            print("💡 TENTE PELA INTERFACE WEB:")
            print("=" * 80)
            print(f"http://78.142.242.82:8080/manager")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def verificar_conexao():
    """Verifica se a instância foi conectada"""
    print()
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
                    print("\n" + "=" * 80)
                    print("✅ CONECTADO COM SUCESSO!")
                    print("=" * 80)
                    print()
                    print("📋 Informações da conexão:")
                    print(json.dumps(data, indent=2))
                    print()
                    return True
                else:
                    print(f"⏳ Tentativa {tentativa + 1}/{max_tentativas} - Status: {state or 'aguardando'}")
                    
            tentativa += 1
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Erro na tentativa {tentativa + 1}: {e}")
            tentativa += 1
            time.sleep(2)
    
    print("\n⏱️ Tempo esgotado. QR Code não foi escaneado.")
    print()
    print("=" * 80)
    print("💡 O QUE FAZER:")
    print("=" * 80)
    print("1. Acesse: http://78.142.242.82:8080/manager")
    print("2. Localize a instância 'BotMedico'")
    print("3. Clique em 'Connect' e escaneie o QR Code")
    print("4. Depois execute: python3 configurar_webhook.py")
    print()
    return False

def configurar_webhook():
    """Configura o webhook após conectar"""
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
        "webhook": {
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
    }
    
    print(f"Webhook URL: {webhook_url}")
    print()
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code in [200, 201]:
            print("✅ Webhook configurado com sucesso!")
            print()
            return True
        else:
            print(f"⚠️ Erro ao configurar webhook: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    print("\n🔄 RESET E RECONFIGURAÇÃO DO BOT CLARA\n")
    
    # Passo 1: Deletar instância antiga
    deletar_instancia()
    
    print("Aguardando 3 segundos...")
    time.sleep(3)
    print()
    
    # Passo 2: Criar nova instância
    if criar_instancia():
        print()
        time.sleep(2)
        
        # Passo 3: Buscar QR Code
        if buscar_qrcode():
            
            # Passo 4: Aguardar conexão
            if verificar_conexao():
                
                # Passo 5: Configurar webhook
                if configurar_webhook():
                    
                    print()
                    print("=" * 80)
                    print("✅ CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!")
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
                    print("3. Teste enviando uma mensagem para: 5521972706068")
                    print()
                    print("4. Execute o diagnóstico:")
                    print("   python3 diagnostico_bot.py")
                    print()
            else:
                print()
                print("⚠️ Conexão não estabelecida via script.")
                print("   Conecte manualmente pela interface web e depois execute:")
                print("   python3 configurar_webhook.py")
        else:
            print()
            print("⚠️ Não foi possível gerar QR Code via API.")
            print("   Use a interface web para conectar.")
    
    print()
    print("=" * 80)
    print("Script finalizado!")
    print("=" * 80)
    print()
