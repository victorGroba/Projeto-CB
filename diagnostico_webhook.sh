#!/bin/bash
# Script de diagnóstico completo do webhook

echo "========================================================================"
echo "🔍 DIAGNÓSTICO COMPLETO DO WEBHOOK"
echo "========================================================================"
echo ""

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "1️⃣ Status dos containers..."
echo ""
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "bot_medico|evolution_api"
echo ""

echo "2️⃣ Verificando configuração do webhook na Evolution..."
echo ""
curl -s -X GET http://78.142.242.82:8080/webhook/find/BotMedico \
  -H "apikey: Josevfg2409@" | python3 -m json.tool
echo ""

echo "3️⃣ Verificando status da conexão WhatsApp..."
echo ""
curl -s -X GET http://78.142.242.82:8080/instance/connectionState/BotMedico \
  -H "apikey: Josevfg2409@" | python3 -m json.tool
echo ""

echo "4️⃣ Testando se o webhook do bot está acessível..."
echo ""
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST http://78.142.242.82:5025/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "event": "messages.upsert",
    "data": {
      "key": {
        "remoteJid": "5521980377236@s.whatsapp.net",
        "fromMe": false
      },
      "message": {
        "conversation": "teste diagnostico"
      }
    }
  }')

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Webhook do bot está respondendo!${NC}"
    echo "Resposta: $BODY"
else
    echo -e "${RED}❌ Webhook do bot NÃO está respondendo!${NC}"
    echo "HTTP Code: $HTTP_CODE"
    echo "Resposta: $BODY"
fi
echo ""

echo "5️⃣ Últimas 20 linhas do log do bot..."
echo ""
docker logs --tail 20 bot_medico
echo ""

echo "6️⃣ Últimas 30 linhas do log da Evolution (procurando webhooks)..."
echo ""
docker logs --tail 100 evolution_api 2>&1 | grep -i webhook | tail -30
echo ""

echo "7️⃣ Verificando se há erros recentes na Evolution..."
echo ""
docker logs --tail 50 evolution_api 2>&1 | grep -i error | tail -10
echo ""

echo "========================================================================"
echo "📊 RESUMO"
echo "========================================================================"
echo ""
echo "Para enviar mensagem de teste via Evolution API:"
echo "curl -X POST http://78.142.242.82:8080/message/sendText/BotMedico \\"
echo "  -H 'apikey: Josevfg2409@' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"number\": \"5521980377236\", \"text\": \"teste\"}'"
echo ""
echo "Para monitorar logs em tempo real:"
echo "  Bot: docker logs -f bot_medico"
echo "  Evolution: docker logs -f evolution_api"
echo ""
