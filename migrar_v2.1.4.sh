#!/bin/bash
# Script para migrar para Evolution API v2.1.4 (mais estável)

echo "========================================================================"
echo "🔄 MIGRANDO PARA EVOLUTION API v2.1.4"
echo "========================================================================"
echo ""
echo "⚠️  ATENÇÃO: Isso vai apagar TODOS os dados e recomeçar do zero!"
echo "   - Sessões do WhatsApp"
echo "   - Histórico de mensagens"
echo "   - Configurações"
echo ""
read -p "Deseja continuar? (s/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Ss]$ ]]
then
    echo "Operação cancelada."
    exit 1
fi

echo ""
echo "1️⃣ Parando todos os containers..."
docker-compose down

echo ""
echo "2️⃣ Removendo imagens antigas da Evolution..."
docker rmi atendai/evolution-api:v2.0.9 -f 2>/dev/null || echo "Imagem v2.0.9 não encontrada"
docker rmi atendai/evolution-api:v2.2.2 -f 2>/dev/null || echo "Imagem v2.2.2 não encontrada"

echo ""
echo "3️⃣ Deletando volumes (apagando dados corrompidos)..."
docker volume rm bot-agendamento_evolution_store -f 2>/dev/null || echo "Volume evolution_store não encontrado"
docker volume rm bot-agendamento_postgres_data -f 2>/dev/null || echo "Volume postgres_data não encontrado"
docker volume rm bot-agendamento_redis_data -f 2>/dev/null || echo "Volume redis_data não encontrado"

echo ""
echo "4️⃣ Fazendo backup do docker-compose.yml atual..."
cp docker-compose.yml docker-compose.yml.backup-$(date +%Y%m%d-%H%M%S) 2>/dev/null || echo "Arquivo não encontrado"

echo ""
echo "5️⃣ Copiando novo docker-compose.yml (v2.1.4)..."
cp docker-compose-v2.1.4.yml docker-compose.yml

echo ""
echo "6️⃣ Baixando imagem v2.1.4..."
docker pull atendai/evolution-api:v2.1.4

echo ""
echo "7️⃣ Subindo todos os containers..."
docker-compose up -d

echo ""
echo "8️⃣ Aguardando containers iniciarem (30 segundos)..."
sleep 30

echo ""
echo "9️⃣ Verificando se tudo está rodando..."
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "bot_medico|evolution_api|postgres_db|redis"

echo ""
echo "🔟 Criando instância BotMedico..."
curl -X POST http://78.142.242.82:8080/instance/create \
  -H "apikey: Josevfg2409@" \
  -H "Content-Type: application/json" \
  -d '{
    "instanceName": "BotMedico",
    "qrcode": true,
    "integration": "WHATSAPP-BAILEYS"
  }'

echo ""
echo ""
echo "1️⃣1️⃣ Configurando webhook..."
sleep 3
curl -X POST http://78.142.242.82:8080/webhook/set/BotMedico \
  -H "apikey: Josevfg2409@" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook": {
      "url": "http://78.142.242.82:5025/webhook",
      "enabled": true,
      "webhookByEvents": true,
      "events": ["MESSAGES_UPSERT", "SEND_MESSAGE"]
    }
  }'

echo ""
echo ""
echo "========================================================================"
echo "✅ MIGRAÇÃO CONCLUÍDA!"
echo "========================================================================"
echo ""
echo "📱 PRÓXIMOS PASSOS:"
echo ""
echo "1. Acesse: http://78.142.242.82:8080/manager"
echo "2. Encontre a instância 'BotMedico'"
echo "3. Leia o QR Code com o WhatsApp: 5521980377236"
echo "4. Envie mensagem de outro número: 5521968127948"
echo "5. Monitore os logs: docker logs -f bot_medico"
echo ""
echo "🔍 Para verificar a versão instalada:"
echo "   docker ps | grep evolution"
echo ""
echo "Deve mostrar: atendai/evolution-api:v2.1.4"
echo ""
