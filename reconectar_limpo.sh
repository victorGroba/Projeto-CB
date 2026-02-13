#!/bin/bash
# Script para limpar sessão corrompida e reconectar

echo "========================================================================"
echo "🔄 LIMPANDO E RECONECTANDO INSTÂNCIA DO WHATSAPP"
echo "========================================================================"
echo ""

API_KEY="Josevfg2409@"
EVOLUTION_URL="http://78.142.242.82:8080"
INSTANCE="BotMedico"

echo "1️⃣ Fazendo logout da instância atual..."
curl -X DELETE "${EVOLUTION_URL}/instance/logout/${INSTANCE}" \
  -H "apikey: ${API_KEY}"
echo ""
echo ""

echo "2️⃣ Aguardando 3 segundos..."
sleep 3
echo ""

echo "3️⃣ Reconectando instância..."
curl -X GET "${EVOLUTION_URL}/instance/connect/${INSTANCE}" \
  -H "apikey: ${API_KEY}"
echo ""
echo ""

echo "4️⃣ Reconfigurando webhook (URL INTERNA do Docker)..."
curl -X POST "${EVOLUTION_URL}/webhook/set/${INSTANCE}" \
  -H "apikey: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://bot_medico:5000/webhook",
    "enabled": true,
    "webhookByEvents": true,
    "events": ["MESSAGES_UPSERT", "SEND_MESSAGE"]
  }'
echo ""
echo ""

echo "========================================================================"
echo "✅ PROCESSO CONCLUÍDO!"
echo "========================================================================"
echo ""
echo "📱 PRÓXIMOS PASSOS:"
echo ""
echo "1. Acesse o manager: ${EVOLUTION_URL}/manager"
echo "2. Encontre a instância '${INSTANCE}'"
echo "3. Leia o QR Code com o WhatsApp: 5521980377236"
echo "4. Depois de conectar, envie mensagem de outro número"
echo "5. Monitore: docker logs -f bot_medico"
echo ""
