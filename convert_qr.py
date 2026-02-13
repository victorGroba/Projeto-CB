import requests
import json
import base64

# Obter QR code
response = requests.get(
    'http://localhost:8080/instance/connect/BotMedico',
    headers={'apikey': 'Josevfg2409@'}
)

data = response.json()
if 'base64' in data:
    # Extrair base64
    base64_str = data['base64'].split(',')[1]
    
    # Converter para imagem
    img_data = base64.b64decode(base64_str)
    
    # Salvar arquivo
    with open('qrcode.png', 'wb') as f:
        f.write(img_data)
    
    print("✅ QR Code salvo em: qrcode.png")
    print(f"📊 Tamanho: {len(img_data)} bytes")
else:
    print("❌ Erro: QR code não encontrado")
    print(data)
