import requests
import time
import base64

# --- CONFIGURAÇÕES ---
EVOLUTION_URL = "http://localhost:8080"
API_KEY = "Josevfg2409@"
INSTANCE_NAME = "BotMedico"

def criar_e_conectar():
    print("=" * 60)
    print("🔄 RECRIANDO INSTÂNCIA BOT MÉDICO")
    print("=" * 60)

    # 1. CRIAR INSTÂNCIA
    url_create = f"{EVOLUTION_URL}/instance/create"
    headers = {
        "apikey": API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "instanceName": INSTANCE_NAME,
        "token": "",
        "qrcode": True,
        "integration": "WHATSAPP-BAILEYS"
    }

    try:
        print(f"📡 Criando instância '{INSTANCE_NAME}'...")
        response = requests.post(url_create, json=payload, headers=headers)
        
        # Se já existir, tudo bem, vamos apenas conectar
        if response.status_code == 403: # Já existe
            print("⚠️ A instância já existia (mas talvez esteja desconectada).")
        elif response.status_code in [200, 201]:
            print("✅ Instância criada com sucesso!")
        else:
            print(f"❌ Erro ao criar: {response.text}")
            return

        # 2. BUSCAR QR CODE
        print("\n🔍 Buscando QR Code para conexão...")
        time.sleep(2) # Espera um pouquinho
        
        url_connect = f"{EVOLUTION_URL}/instance/connect/{INSTANCE_NAME}"
        resp_connect = requests.get(url_connect, headers=headers)
        
        if resp_connect.status_code == 200:
            data = resp_connect.json()
            # Tenta pegar o base64 ou o código
            qr_base64 = data.get('base64') or data.get('qrcode', {}).get('base64')
            qr_code = data.get('code') or data.get('qrcode', {}).get('code')
            
            if qr_code:
                print("\n" + "="*60)
                print("📱 ESCANEIE O QR CODE ABAIXO NO SEU WHATSAPP:")
                print("="*60)
                print(qr_code) # Imprime o código para terminal (alguns terminais renderizam)
                print("\n⚠️ Se o QR Code não apareceu ou ficou ruim de ler:")
                print(f"Acesse pelo navegador: http://SEU_IP_DA_VPS:8080/manager")
                print(f"Login Global Api Key: {API_KEY}")
            else:
                print("✅ Parece que já está conectado!")
        else:
            print(f"❌ Erro ao pegar QR Code: {resp_connect.text}")

    except Exception as e:
        print(f"❌ Erro crítico: {e}")

if __name__ == "__main__":
    criar_e_conectar()
