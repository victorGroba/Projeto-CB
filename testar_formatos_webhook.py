#!/usr/bin/env python3
"""
Script para testar diferentes formatos de webhook
Testa todos os formatos conhecidos da Evolution API
"""

import requests
import json

# Configurações
EVOLUTION_URL = "http://78.142.242.82:8080"
API_KEY = "Josevfg2409@"
INSTANCE_NAME = "BotMedico"
WEBHOOK_URL = "http://78.142.242.82:5025/webhook"

def testar_formato(numero, nome, payload):
    """Testa um formato específico de payload"""
    url = f"{EVOLUTION_URL}/webhook/set/{INSTANCE_NAME}"
    headers = {
        "apikey": API_KEY,
        "Content-Type": "application/json"
    }
    
    print("=" * 70)
    print(f"🧪 TESTE #{numero}: {nome}")
    print("=" * 70)
    print()
    print("📦 Payload:")
    print(json.dumps(payload, indent=2))
    print()
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200 or response.status_code == 201:
            print(f"✅ SUCESSO! Status: {response.status_code}")
            print()
            print("📋 Resposta:")
            print(json.dumps(response.json(), indent=2))
            return True
        else:
            print(f"❌ ERRO! Status: {response.status_code}")
            print()
            try:
                print("📋 Resposta:")
                print(json.dumps(response.json(), indent=2))
            except:
                print(f"Resposta (texto): {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERRO na requisição: {e}")
        return False

def main():
    print()
    print("=" * 70)
    print("🔬 TESTADOR DE FORMATOS DE WEBHOOK - Evolution API")
    print("=" * 70)
    print()
    print(f"Instância: {INSTANCE_NAME}")
    print(f"Webhook URL: {WEBHOOK_URL}")
    print()
    
    # Formato 1: Simples (v2.0.x antigo)
    formato1 = {
        "url": WEBHOOK_URL,
        "enabled": True,
        "webhookByEvents": True,
        "events": ["MESSAGES_UPSERT", "SEND_MESSAGE"]
    }
    
    # Formato 2: Com wrapper "webhook" (v2.2.x)
    formato2 = {
        "webhook": {
            "url": WEBHOOK_URL,
            "enabled": True,
            "webhookByEvents": True,
            "events": ["MESSAGES_UPSERT", "SEND_MESSAGE"]
        }
    }
    
    # Formato 3: Com wrapper e configurações extras
    formato3 = {
        "webhook": {
            "url": WEBHOOK_URL,
            "enabled": True,
            "webhookByEvents": True,
            "webhookBase64": False,
            "events": ["MESSAGES_UPSERT", "SEND_MESSAGE"]
        }
    }
    
    # Formato 4: Estilo antigo sem webhookByEvents
    formato4 = {
        "url": WEBHOOK_URL,
        "enabled": True,
        "events": ["MESSAGES_UPSERT"]
    }
    
    # Formato 5: Com wrapper, sem webhookByEvents
    formato5 = {
        "webhook": {
            "url": WEBHOOK_URL,
            "enabled": True,
            "events": ["MESSAGES_UPSERT", "SEND_MESSAGE"]
        }
    }
    
    # Formato 6: Mínimo possível com wrapper
    formato6 = {
        "webhook": {
            "url": WEBHOOK_URL,
            "enabled": True
        }
    }
    
    formatos = [
        (1, "Simples (v2.0.x)", formato1),
        (2, "Com wrapper 'webhook' (v2.2.x)", formato2),
        (3, "Com wrapper + webhookBase64", formato3),
        (4, "Sem webhookByEvents", formato4),
        (5, "Wrapper sem webhookByEvents", formato5),
        (6, "Mínimo com wrapper", formato6),
    ]
    
    sucesso = None
    
    for numero, nome, payload in formatos:
        if testar_formato(numero, nome, payload):
            sucesso = (numero, nome, payload)
            print()
            print("=" * 70)
            print("🎉 FORMATO CORRETO ENCONTRADO!")
            print("=" * 70)
            print()
            print(f"Use o Formato #{numero}: {nome}")
            print()
            print("Payload correto:")
            print(json.dumps(payload, indent=2))
            break
        print()
        input("Pressione ENTER para testar o próximo formato...")
        print()
    
    if not sucesso:
        print()
        print("=" * 70)
        print("❌ NENHUM FORMATO FUNCIONOU")
        print("=" * 70)
        print()
        print("Possíveis causas:")
        print("  1. A instância não existe ou nome está errado")
        print("  2. A API Key está incorreta")
        print("  3. A versão da Evolution API é diferente")
        print("  4. Há algum problema com a instalação")
        print()
        print("Verifique:")
        print(f"  - Instâncias: curl -H 'apikey: {API_KEY}' {EVOLUTION_URL}/instance/fetchInstances")
        print(f"  - Logs: docker logs evolution_api")
    
    return sucesso is not None

if __name__ == "__main__":
    import sys
    sucesso = main()
    sys.exit(0 if sucesso else 1)
