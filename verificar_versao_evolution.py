#!/usr/bin/env python3
"""
Script para verificar a versão exata da Evolution API
"""

import requests
import subprocess
import json

EVOLUTION_URL = "http://78.142.242.82:8080"
API_KEY = "Josevfg2409@"

print("=" * 70)
print("🔍 VERIFICANDO VERSÃO DA EVOLUTION API")
print("=" * 70)
print()

# Método 1: Via Docker
print("📦 Método 1: Verificando via Docker...")
try:
    result = subprocess.run(
        ["docker", "inspect", "evolution_api"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        data = json.loads(result.stdout)
        if data and len(data) > 0:
            image = data[0].get('Config', {}).get('Image', 'N/A')
            print(f"   Imagem: {image}")
            
            labels = data[0].get('Config', {}).get('Labels', {})
            if labels:
                print("   Labels:")
                for key, value in labels.items():
                    if 'version' in key.lower():
                        print(f"     {key}: {value}")
    else:
        print("   ❌ Erro ao executar docker inspect")
except Exception as e:
    print(f"   ❌ Erro: {e}")

print()

# Método 2: Via docker ps
print("📦 Método 2: Verificando via docker ps...")
try:
    result = subprocess.run(
        ["docker", "ps", "--filter", "name=evolution_api", "--format", "{{.Image}}"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0 and result.stdout.strip():
        print(f"   Imagem rodando: {result.stdout.strip()}")
    else:
        print("   ❌ Container não encontrado")
except Exception as e:
    print(f"   ❌ Erro: {e}")

print()

# Método 3: Tentar acessar endpoint de versão (se existir)
print("🌐 Método 3: Tentando endpoint /version...")
try:
    response = requests.get(f"{EVOLUTION_URL}/version", timeout=5)
    if response.status_code == 200:
        print(f"   Versão: {response.text}")
    else:
        print(f"   ⚠️ Endpoint não disponível (status {response.status_code})")
except Exception as e:
    print(f"   ⚠️ Endpoint não existe ou erro: {type(e).__name__}")

print()

# Método 4: Verificar docker-compose.yml
print("📄 Método 4: Verificando docker-compose.yml...")
try:
    with open('docker-compose.yml', 'r') as f:
        content = f.read()
        for line in content.split('\n'):
            if 'evolution-api' in line.lower() and 'image:' in line.lower():
                print(f"   Linha encontrada: {line.strip()}")
except Exception as e:
    print(f"   ❌ Erro ao ler arquivo: {e}")

print()

# Método 5: Logs do container
print("📋 Método 5: Verificando logs do container...")
try:
    result = subprocess.run(
        ["docker", "logs", "--tail", "50", "evolution_api"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        logs = result.stdout + result.stderr
        # Procura por menções de versão nos logs
        for line in logs.split('\n'):
            if any(palavra in line.lower() for palavra in ['version', 'v2.', 'evolution']):
                if len(line.strip()) > 0 and len(line) < 200:
                    print(f"   {line.strip()}")
except Exception as e:
    print(f"   ❌ Erro: {e}")

print()
print("=" * 70)
print("✅ VERIFICAÇÃO CONCLUÍDA")
print("=" * 70)
print()
print("💡 A versão mais confiável é a do 'docker ps' (Método 2)")
