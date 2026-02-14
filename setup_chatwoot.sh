#!/bin/bash

# Script de Configuração Automática - Chatwoot + Evolution API
# Autor: Claude AI
# Data: 2026

echo "🚀 Iniciando configuração do Chatwoot + Evolution API..."
echo ""

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configurações
EVOLUTION_URL="http://localhost:8080"
EVOLUTION_APIKEY="Josevfg2409@"
INSTANCE_NAME="BotMedico"

# Função para verificar se um container está rodando
check_container() {
    if docker ps | grep -q "$1"; then
        echo -e "${GREEN}✅ Container $1 está rodando${NC}"
        return 0
    else
        echo -e "${RED}❌ Container $1 NÃO está rodando${NC}"
        return 1
    fi
}

# Função para aguardar um serviço ficar disponível
wait_for_service() {
    local url=$1
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Aguardando $url ficar disponível..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200\|201\|302"; then
            echo -e "${GREEN}✅ Serviço disponível!${NC}"
            return 0
        fi
        echo "Tentativa $attempt de $max_attempts..."
        sleep 5
        ((attempt++))
    done
    
    echo -e "${RED}❌ Timeout aguardando o serviço${NC}"
    return 1
}

echo "📋 PASSO 1: Verificando containers..."
echo ""

check_container "evolution_api" || { echo "Inicie os containers primeiro: docker-compose up -d"; exit 1; }
check_container "chatwoot_base" || { echo "Chatwoot não está rodando!"; exit 1; }
check_container "bot_medico" || { echo "Bot não está rodando!"; exit 1; }

echo ""
echo "📋 PASSO 2: Aguardando serviços ficarem prontos..."
echo ""

wait_for_service "$EVOLUTION_URL/instance/fetchInstances"

echo ""
echo "📋 PASSO 3: Verificando conexão da Evolution API..."
echo ""

INSTANCE_STATUS=$(curl -s -X GET "$EVOLUTION_URL/instance/fetchInstances" \
  -H "apikey: $EVOLUTION_APIKEY" | jq -r ".[] | select(.instance.instanceName == \"$INSTANCE_NAME\") | .instance.state")

if [ "$INSTANCE_STATUS" == "open" ]; then
    echo -e "${GREEN}✅ Instância $INSTANCE_NAME conectada!${NC}"
else
    echo -e "${YELLOW}⚠️  Instância não conectada. Gerando QR Code...${NC}"
    
    QR_RESPONSE=$(curl -s -X GET "$EVOLUTION_URL/instance/connect/$INSTANCE_NAME" \
      -H "apikey: $EVOLUTION_APIKEY")
    
    echo "$QR_RESPONSE" | jq -r '.base64' | sed 's/data:image\/png;base64,//' | base64 -d > /tmp/qrcode.png
    
    echo -e "${YELLOW}QR Code salvo em: /tmp/qrcode.png${NC}"
    echo "Escaneie o QR Code e execute este script novamente."
    exit 0
fi

echo ""
echo "📋 PASSO 4: Configuração do Chatwoot..."
echo ""

# Solicitar o token do Chatwoot
echo -e "${YELLOW}⚠️  IMPORTANTE: Você precisa do TOKEN do Chatwoot${NC}"
echo ""
echo "Para obter o token:"
echo "1. Acesse: http://SEU_IP:3001"
echo "2. Faça login no Chatwoot"
echo "3. Vá em: Settings → Integrations → API Access Tokens"
echo "4. Clique em 'Add New Token'"
echo "5. Copie o token gerado"
echo ""

read -p "Cole aqui o TOKEN do Chatwoot: " CHATWOOT_TOKEN

if [ -z "$CHATWOOT_TOKEN" ]; then
    echo -e "${RED}❌ Token não pode ser vazio!${NC}"
    exit 1
fi

# Solicitar Account ID (normalmente é 1)
read -p "Informe o Account ID do Chatwoot (geralmente é 1): " CHATWOOT_ACCOUNT_ID
CHATWOOT_ACCOUNT_ID=${CHATWOOT_ACCOUNT_ID:-1}

echo ""
echo "🔧 Configurando integração Chatwoot na Evolution API..."
echo ""

CHATWOOT_CONFIG=$(cat <<EOF
{
  "enabled": true,
  "account_id": "$CHATWOOT_ACCOUNT_ID",
  "token": "$CHATWOOT_TOKEN",
  "url": "http://chatwoot_base:3000",
  "sign_msg": true,
  "reopen_conversation": true,
  "conversation_pending": false,
  "import_contacts": true,
  "name_inbox": "WhatsApp - Dr. Victor",
  "merge_brazil_contacts": true,
  "import_messages": true,
  "days_limit_import_messages": 60,
  "auto_create": true,
  "organization": "Clínica Dr. Victor",
  "logo": ""
}
EOF
)

RESPONSE=$(curl -s -X POST "$EVOLUTION_URL/chatwoot/set/$INSTANCE_NAME" \
  -H "apikey: $EVOLUTION_APIKEY" \
  -H "Content-Type: application/json" \
  -d "$CHATWOOT_CONFIG")

if echo "$RESPONSE" | jq -e '.hash' > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Chatwoot configurado com sucesso!${NC}"
    echo ""
    echo "📊 Detalhes da configuração:"
    echo "$RESPONSE" | jq '.'
else
    echo -e "${RED}❌ Erro ao configurar Chatwoot${NC}"
    echo "Resposta: $RESPONSE"
    exit 1
fi

echo ""
echo "📋 PASSO 5: Verificando configuração..."
echo ""

VERIFY=$(curl -s -X GET "$EVOLUTION_URL/chatwoot/find/$INSTANCE_NAME" \
  -H "apikey: $EVOLUTION_APIKEY")

if echo "$VERIFY" | jq -e '.enabled' > /dev/null 2>&1; then
    ENABLED=$(echo "$VERIFY" | jq -r '.enabled')
    if [ "$ENABLED" == "true" ]; then
        echo -e "${GREEN}✅ Integração Chatwoot está ATIVA!${NC}"
    else
        echo -e "${RED}❌ Integração está configurada mas DESATIVADA${NC}"
    fi
else
    echo -e "${RED}❌ Não foi possível verificar a configuração${NC}"
fi

echo ""
echo "🎉 CONFIGURAÇÃO CONCLUÍDA!"
echo ""
echo "📝 Próximos passos:"
echo "1. Acesse o Chatwoot: http://SEU_IP:3001"
echo "2. Vá em Settings → Inboxes"
echo "3. Verifique se a inbox 'WhatsApp - Dr. Victor' foi criada"
echo "4. Envie uma mensagem de teste pelo WhatsApp"
echo "5. A conversa deve aparecer no Chatwoot automaticamente!"
echo ""
echo "🔍 Comandos úteis:"
echo "- Ver logs do bot: docker logs bot_medico -f"
echo "- Ver logs da Evolution: docker logs evolution_api -f"
echo "- Ver logs do Chatwoot: docker logs chatwoot_base -f"
echo ""
echo "✅ Tudo pronto! 🚀"
