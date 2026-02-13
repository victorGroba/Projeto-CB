#!/bin/bash
# Script para forçar o uso da Evolution API v2.0.9

echo "========================================================================"
echo "🔄 FORÇANDO DOWNGRADE PARA EVOLUTION API v2.0.9"
echo "========================================================================"
echo ""

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "1️⃣ Parando containers..."
docker-compose down

echo ""
echo "2️⃣ Removendo imagem v2.2.2..."
docker rmi atendai/evolution-api:v2.2.2 -f 2>/dev/null || echo "Imagem v2.2.2 não encontrada"

echo ""
echo "3️⃣ Removendo evolution_api manualmente..."
docker rm -f evolution_api 2>/dev/null || echo "Container já foi removido"

echo ""
echo "4️⃣ Baixando imagem v2.0.9 especificamente..."
docker pull atendai/evolution-api:v2.0.9

echo ""
echo "5️⃣ Recriando todos os containers com v2.0.9..."
docker-compose up -d --force-recreate

echo ""
echo "6️⃣ Verificando versão instalada..."
sleep 3
docker ps | grep evolution

echo ""
echo "7️⃣ Verificando versão exata..."
docker inspect evolution_api | grep -i "image.*evolution" || echo "Container ainda não está pronto"

echo ""
echo "========================================================================"
echo "✅ PROCESSO CONCLUÍDO!"
echo "========================================================================"
echo ""
echo "Verifique se está rodando v2.0.9:"
echo "  docker ps | grep evolution"
echo ""
echo "Se estiver correto, acesse o manager para ler o QR Code:"
echo "  http://78.142.242.82:8080/manager"
