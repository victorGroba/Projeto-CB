#!/usr/bin/env python3
"""
Script para configurar o webhook na Evolution API
ATUALIZADO COM O NOME CORRETO: BotMedico
"""

import requests
import sys

# Configurações - NOME CORRETO DA INSTÂNCIA
EVOLUTION_URL = "http://78.142.242.82:8080"
API_KEY = "Josevfg2409@"
INSTANCE_NAME = "BotMedico"  # ← NOME CORRETO!
WEBHOOK_URL = "http://78.142.242.82:5025/webhook"

def configurar_webhook():
    """Configura o webhook na Evolution API"""
    url = f"{EVOLUTION_URL}/webhook/set/{INSTANCE_NAME}"
    headers = {
        "apikey": API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "enabled": True,
        "url": WEBHOOK_URL,
        "webhookByEvents": True,
        "events": [
            "MESSAGES_UPSERT"
        ]
    }
    
    print(f"🔧 Configurando webhook para instância: {INSTANCE_NAME}")
    print(f"📡 URL do webhook: {WEBHOOK_URL}")
    print(f"🌐 Evolution API: {EVOLUTION_URL}")
    print()
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200 or response.status_code == 201:
            print("✅ WEBHOOK CONFIGURADO COM SUCESSO!")
            print()
            print("📋 Resposta:")
            print(response.json())
            return True
        else:
            print(f"❌ ERRO ao configurar webhook!")
            print(f"Status Code: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERRO na requisição: {e}")
        return False

def verificar_webhook():
    """Verifica se o webhook está configurado"""
    url = f"{EVOLUTION_URL}/webhook/find/{INSTANCE_NAME}"
    headers = {
        "apikey": API_KEY
    }
    
    print()
    print("🔍 Verificando configuração do webhook...")
    print()
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print("📊 Configuração atual do webhook:")
            print(f"   Habilitado: {data.get('enabled', 'N/A')}")
            print(f"   URL: {data.get('url', 'N/A')}")
            print(f"   Eventos: {data.get('events', 'N/A')}")
            return True
        else:
            print(f"⚠️ Webhook não encontrado ou erro ao verificar")
            print(f"Status Code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERRO ao verificar: {e}")
        return False

def verificar_conexao():
    """Verifica o status da conexão da instância"""
    url = f"{EVOLUTION_URL}/instance/connectionState/{INSTANCE_NAME}"
    headers = {
        "apikey": API_KEY
    }
    
    print()
    print("📱 Verificando status da conexão WhatsApp...")
    print()
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            estado = data.get('state', 'unknown')
            
            if estado == 'open':
                print("✅ WhatsApp CONECTADO!")
                return True
            else:
                print(f"⚠️ WhatsApp DESCONECTADO (estado: {estado})")
                print()
                print("🔄 Você precisa reconectar o WhatsApp:")
                print(f"   1. Acesse: {EVOLUTION_URL}/manager")
                print(f"   2. Encontre a instância 'BotMedico'")
                print(f"   3. Clique em 'Connect' ou leia o QR Code novamente")
                return False
        else:
            print(f"⚠️ Erro ao verificar conexão")
            print(f"Status Code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERRO ao verificar: {e}")
        return False

def main():
    print("=" * 60)
    print("🤖 CONFIGURADOR DE WEBHOOK - BOT WHATSAPP")
    print("=" * 60)
    print()
    
    # Verifica a conexão primeiro
    conectado = verificar_conexao()
    
    # Configura o webhook
    sucesso = configurar_webhook()
    
    if sucesso:
        # Verifica a configuração
        verificar_webhook()
        
        print()
        print("=" * 60)
        print("✅ WEBHOOK CONFIGURADO!")
        print("=" * 60)
        print()
        
        if conectado:
            print("🎯 Próximos passos:")
            print("   1. Envie uma mensagem para o número do WhatsApp")
            print("   2. Verifique os logs: docker logs -f bot_medico")
            print("   3. O bot deve responder automaticamente")
        else:
            print("⚠️ IMPORTANTE:")
            print("   O webhook está configurado, mas o WhatsApp está DESCONECTADO.")
            print("   Você precisa reconectar antes de testar!")
            print()
            print("   Para reconectar:")
            print(f"   1. Acesse: {EVOLUTION_URL}/manager")
            print(f"   2. Encontre 'BotMedico'")
            print(f"   3. Clique em 'Connect' e leia o QR Code")
        
        print()
        sys.exit(0)
    else:
        print()
        print("=" * 60)
        print("❌ FALHA AO CONFIGURAR WEBHOOK")
        print("=" * 60)
        print()
        print("🔧 Verifique:")
        print("   1. A Evolution API está rodando? docker ps")
        print("   2. A API Key está correta?")
        print("   3. O nome da instância é 'BotMedico'?")
        print()
        sys.exit(1)

if __name__ == "__main__":
    main()
