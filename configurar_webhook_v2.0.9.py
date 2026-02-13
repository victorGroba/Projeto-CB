#!/usr/bin/env python3
"""
Script para configurar o webhook na Evolution API v2.0.9
IMPORTANTE: Versão 2.0.9 tem formato diferente da 2.2.2!
"""

import requests
import sys
import json

# Configurações
EVOLUTION_URL = "http://78.142.242.82:8080"
API_KEY = "Josevfg2409@"
INSTANCE_NAME = "BotMedico"
WEBHOOK_URL = "http://78.142.242.82:5025/webhook"

def configurar_webhook_v2_0_9():
    """
    Configura o webhook na Evolution API v2.0.9
    Formato específico para esta versão
    """
    url = f"{EVOLUTION_URL}/webhook/set/{INSTANCE_NAME}"
    headers = {
        "apikey": API_KEY,
        "Content-Type": "application/json"
    }
    
    # Formato para v2.0.9 - SEM o objeto "webhook" wrapper
    payload = {
        "url": WEBHOOK_URL,
        "enabled": True,
        "webhookByEvents": True,
        "events": [
            "MESSAGES_UPSERT",
            "SEND_MESSAGE"
        ]
    }
    
    print("=" * 70)
    print("🤖 CONFIGURADOR DE WEBHOOK - Evolution API v2.0.9")
    print("=" * 70)
    print()
    print(f"🔧 Instância: {INSTANCE_NAME}")
    print(f"📡 Webhook URL: {WEBHOOK_URL}")
    print(f"🌐 Evolution API: {EVOLUTION_URL}")
    print()
    print("📦 Payload:")
    print(json.dumps(payload, indent=2))
    print()
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200 or response.status_code == 201:
            print("✅ WEBHOOK CONFIGURADO COM SUCESSO!")
            print()
            print("📋 Resposta da API:")
            print(json.dumps(response.json(), indent=2))
            return True
        else:
            print(f"❌ ERRO ao configurar webhook!")
            print(f"Status Code: {response.status_code}")
            try:
                print(f"Resposta: {json.dumps(response.json(), indent=2)}")
            except:
                print(f"Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERRO na requisição: {e}")
        import traceback
        traceback.print_exc()
        return False

def verificar_webhook():
    """Verifica se o webhook está configurado"""
    url = f"{EVOLUTION_URL}/webhook/find/{INSTANCE_NAME}"
    headers = {
        "apikey": API_KEY
    }
    
    print()
    print("=" * 70)
    print("🔍 Verificando configuração do webhook...")
    print("=" * 70)
    print()
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Webhook encontrado!")
            print()
            print("📊 Configuração atual:")
            print(json.dumps(data, indent=2))
            return True
        elif response.status_code == 404:
            print("⚠️ Webhook não configurado ainda")
            return False
        else:
            print(f"⚠️ Erro ao verificar")
            print(f"Status Code: {response.status_code}")
            try:
                print(f"Resposta: {json.dumps(response.json(), indent=2)}")
            except:
                print(f"Resposta: {response.text}")
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
    print("=" * 70)
    print("📱 Verificando status da conexão WhatsApp...")
    print("=" * 70)
    print()
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print("📊 Status da instância:")
            print(json.dumps(data, indent=2))
            print()
            
            # v2.0.9 pode retornar formato diferente
            estado = data.get('state', data.get('instance', {}).get('state', 'unknown'))
            
            if estado == 'open':
                print("✅ WhatsApp CONECTADO!")
                return True
            else:
                print(f"⚠️ WhatsApp DESCONECTADO (estado: {estado})")
                print()
                print("🔄 Para reconectar:")
                print(f"   Acesse: {EVOLUTION_URL}/manager")
                print(f"   Encontre 'BotMedico' e clique em Connect")
                return False
        else:
            print(f"⚠️ Não foi possível verificar a conexão")
            print(f"Status Code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERRO ao verificar: {e}")
        return False

def testar_webhook():
    """Testa se o endpoint do webhook está acessível"""
    print()
    print("=" * 70)
    print("🧪 Testando endpoint do webhook...")
    print("=" * 70)
    print()
    
    try:
        # Simula uma mensagem
        test_payload = {
            "event": "messages.upsert",
            "data": {
                "key": {
                    "remoteJid": "5511999999999@s.whatsapp.net",
                    "fromMe": False
                },
                "message": {
                    "conversation": "teste"
                }
            }
        }
        
        response = requests.post(WEBHOOK_URL, json=test_payload, timeout=5)
        
        if response.status_code == 200:
            print("✅ Endpoint do webhook está respondendo!")
            print(f"Resposta: {response.text}")
            return True
        else:
            print(f"⚠️ Endpoint retornou status: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Não foi possível conectar ao webhook!")
        print(f"URL: {WEBHOOK_URL}")
        print()
        print("Verifique:")
        print("  1. O container bot_medico está rodando? docker ps")
        print("  2. A porta 5025 está acessível?")
        return False
    except Exception as e:
        print(f"❌ Erro ao testar: {e}")
        return False

def main():
    print()
    
    # Verifica conexão WhatsApp
    conectado = verificar_conexao()
    
    # Testa o endpoint do webhook
    webhook_ok = testar_webhook()
    
    # Configura o webhook
    sucesso = configurar_webhook_v2_0_9()
    
    if sucesso:
        # Verifica a configuração
        verificar_webhook()
        
        print()
        print("=" * 70)
        print("✅ CONFIGURAÇÃO CONCLUÍDA!")
        print("=" * 70)
        print()
        
        if conectado and webhook_ok:
            print("🎉 TUDO PRONTO! Pode testar:")
            print("   1. Envie uma mensagem para o WhatsApp conectado")
            print("   2. Veja os logs: docker logs -f bot_medico")
            print("   3. O bot deve responder!")
        elif not conectado:
            print("⚠️ WhatsApp desconectado - Reconecte primeiro:")
            print(f"   Acesse: {EVOLUTION_URL}/manager")
        elif not webhook_ok:
            print("⚠️ Webhook do bot não está acessível:")
            print("   Verifique: docker logs bot_medico")
        
        print()
        sys.exit(0)
    else:
        print()
        print("=" * 70)
        print("❌ FALHA NA CONFIGURAÇÃO")
        print("=" * 70)
        print()
        sys.exit(1)

if __name__ == "__main__":
    main()
