#!/usr/bin/env python3
import requests
import subprocess
import json

EVOLUTION_URL = "http://78.142.242.82:8080"
API_KEY = "Josevfg2409@"
INSTANCE_NAME = "BotMedico"

print("\n" + "=" * 80)
print("🔍 DIAGNÓSTICO RÁPIDO - BOT CLARA")
print("=" * 80)

# 1. VERIFICAR CONTAINERS
print("\n1️⃣ CONTAINERS:")
result = subprocess.run(['docker', 'ps', '--format', '{{.Names}}: {{.Status}}'], 
                       capture_output=True, text=True)
for line in result.stdout.strip().split('\n'):
    if any(x in line for x in ['bot_medico', 'evolution_api', 'postgres_db']):
        status = "✅" if "Up" in line else "❌"
        print(f"   {status} {line}")

# 2. TESTAR EVOLUTION API
print("\n2️⃣ EVOLUTION API:")
try:
    response = requests.get(f"{EVOLUTION_URL}/instance/fetchInstances", 
                          headers={"apikey": API_KEY}, timeout=3)
    if response.status_code == 200:
        print("   ✅ API respondendo")
        instances = response.json()
        if instances and len(instances) > 0:
            for inst in instances:
                name = inst.get('instance', {}).get('instanceName')
                state = inst.get('instance', {}).get('state')
                print(f"   ✅ Instância: {name} - Estado: {state}")
        else:
            print("   ❌ NENHUMA INSTÂNCIA ENCONTRADA!")
    else:
        print(f"   ❌ API retornou erro: {response.status_code}")
except Exception as e:
    print(f"   ❌ Erro ao conectar: {str(e)[:80]}")

# 3. VERIFICAR WEBHOOK
print("\n3️⃣ WEBHOOK:")
try:
    response = requests.get(f"{EVOLUTION_URL}/webhook/find/{INSTANCE_NAME}", 
                          headers={"apikey": API_KEY}, timeout=3)
    if response.status_code == 200:
        webhook = response.json()
        url = webhook.get('webhook', {}).get('url', 'N/A')
        print(f"   ✅ Webhook configurado: {url}")
    else:
        print(f"   ❌ Webhook não encontrado ou erro: {response.status_code}")
except Exception as e:
    print(f"   ❌ Erro: {str(e)[:80]}")

# 4. VERIFICAR LOGS DO BOT
print("\n4️⃣ ÚLTIMAS LINHAS DOS LOGS DO BOT:")
result = subprocess.run(['docker', 'logs', '--tail', '15', 'bot_medico'], 
                       capture_output=True, text=True)
for line in result.stdout.strip().split('\n')[-5:]:
    print(f"   {line}")

# 5. VERIFICAR LOGS DA EVOLUTION
print("\n5️⃣ ÚLTIMAS LINHAS DOS LOGS DA EVOLUTION:")
result = subprocess.run(['docker', 'logs', '--tail', '15', 'evolution_api'], 
                       capture_output=True, text=True)
for line in result.stdout.strip().split('\n')[-5:]:
    if line.strip():
        print(f"   {line}")

print("\n" + "=" * 80)
print("📋 RESUMO DO PROBLEMA:")
print("=" * 80)

# Análise
try:
    response = requests.get(f"{EVOLUTION_URL}/instance/fetchInstances", 
                          headers={"apikey": API_KEY}, timeout=3)
    if response.status_code == 200:
        instances = response.json()
        if not instances or len(instances) == 0:
            print("\n❌ PROBLEMA: Instância 'BotMedico' não existe!")
            print("\n🔧 SOLUÇÃO:")
            print("   1. Aguarde mais 30 segundos (API pode ainda estar iniciando)")
            print("   2. Execute: python3 aguardar_api.py")
            print("   3. Depois: python3 resetar_instancia.py")
        else:
            has_botmedico = False
            for inst in instances:
                name = inst.get('instance', {}).get('instanceName')
                if name == INSTANCE_NAME:
                    has_botmedico = True
                    state = inst.get('instance', {}).get('state')
                    if state == 'open':
                        print("\n✅ Instância conectada!")
                        print("\n🔍 MAS mensagens não chegam? Possíveis causas:")
                        print("   1. Webhook mal configurado")
                        print("   2. Bot não está escutando na porta correta")
                        print("   3. WhatsApp não está conectado de fato")
                        print("\n🔧 TESTE:")
                        print("   1. Veja logs em tempo real: docker logs -f bot_medico")
                        print("   2. Envie mensagem novamente")
                        print("   3. Veja se aparece '📨 Webhook recebido' no log")
                    else:
                        print(f"\n⚠️ Instância existe mas estado é: {state}")
                        print("\n🔧 SOLUÇÃO: Reconecte o WhatsApp")
                        print("   python3 resetar_instancia.py")
            
            if not has_botmedico:
                print(f"\n❌ PROBLEMA: Instância existe mas não é 'BotMedico'")
                print(f"   Instâncias encontradas: {[i.get('instance', {}).get('instanceName') for i in instances]}")
                print("\n🔧 SOLUÇÃO: Crie com o nome correto")
                print("   python3 resetar_instancia.py")
    else:
        print("\n❌ PROBLEMA: Evolution API não está respondendo corretamente")
        print("\n🔧 SOLUÇÃO:")
        print("   docker-compose restart evolution_api")
        print("   python3 aguardar_api.py")
        
except Exception as e:
    print("\n❌ PROBLEMA: Não consegui conectar na Evolution API")
    print(f"   Erro: {e}")
    print("\n🔧 SOLUÇÃO:")
    print("   1. Verifique se está rodando: docker ps | grep evolution")
    print("   2. Veja os logs: docker logs evolution_api")
    print("   3. Reinicie: docker-compose restart evolution_api")

print("\n" + "=" * 80)
print("Para monitorar em tempo real:")
print("docker logs -f bot_medico")
print("=" * 80 + "\n")
