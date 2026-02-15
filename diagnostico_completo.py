import requests
import json
import subprocess

# Configurações
EVOLUTION_URL = "http://78.142.242.82:8080"
API_KEY = "Josevfg2409@"

def verificar_containers():
    """Verifica quais containers estão rodando"""
    print("=" * 80)
    print("🐳 VERIFICANDO CONTAINERS DOCKER")
    print("=" * 80)
    print()
    
    try:
        result = subprocess.run(['docker', 'ps', '--format', 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'], 
                              capture_output=True, text=True)
        print(result.stdout)
        
        # Verifica se evolution_api está rodando
        if 'evolution_api' in result.stdout:
            print("✅ Evolution API está rodando")
            return True
        else:
            print("❌ Evolution API NÃO está rodando!")
            print()
            print("Execute: docker-compose up -d evolution_api")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao verificar containers: {e}")
        return False

def verificar_logs_evolution():
    """Mostra os últimos logs da Evolution API"""
    print()
    print("=" * 80)
    print("📋 ÚLTIMOS LOGS DA EVOLUTION API")
    print("=" * 80)
    print()
    
    try:
        result = subprocess.run(['docker', 'logs', '--tail', '30', 'evolution_api'], 
                              capture_output=True, text=True)
        print(result.stdout)
        print(result.stderr)
        
    except Exception as e:
        print(f"❌ Erro ao verificar logs: {e}")

def testar_api_evolution():
    """Testa se a API da Evolution está respondendo"""
    print()
    print("=" * 80)
    print("🔌 TESTANDO CONEXÃO COM EVOLUTION API")
    print("=" * 80)
    print()
    
    try:
        # Testa endpoint básico
        url = f"{EVOLUTION_URL}/instance/fetchInstances"
        headers = {"apikey": API_KEY}
        
        print(f"Testando: {url}")
        print()
        
        response = requests.get(url, headers=headers, timeout=5)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API está respondendo!")
            print()
            
            data = response.json()
            print(f"Resposta: {json.dumps(data, indent=2)}")
            print()
            
            if isinstance(data, list):
                if len(data) == 0:
                    print("⚠️ Nenhuma instância encontrada na API")
                    print()
                    print("Possíveis causas:")
                    print("1. Evolution API reiniciou e perdeu os dados")
                    print("2. Instâncias não estão sendo persistidas no banco")
                    print("3. Problema com o volume do Docker")
                else:
                    print(f"✅ Encontradas {len(data)} instância(s)")
            
            return True
        else:
            print(f"❌ API retornou erro: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Timeout ao conectar com a API")
        print("A Evolution API pode não estar rodando ou está travada")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Erro de conexão com a API")
        print("A Evolution API pode estar offline")
        return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def verificar_banco_dados():
    """Verifica se o banco de dados está persistindo as instâncias"""
    print()
    print("=" * 80)
    print("💾 VERIFICANDO BANCO DE DADOS")
    print("=" * 80)
    print()
    
    try:
        # Verifica logs do postgres
        result = subprocess.run(['docker', 'logs', '--tail', '20', 'postgres_db'], 
                              capture_output=True, text=True)
        
        if 'database system is ready to accept connections' in result.stdout:
            print("✅ Banco PostgreSQL está rodando")
        else:
            print("⚠️ Banco pode ter problemas:")
            print(result.stdout[-500:])  # Últimos 500 caracteres
        
    except Exception as e:
        print(f"❌ Erro ao verificar banco: {e}")

def verificar_volumes():
    """Verifica os volumes do Docker"""
    print()
    print("=" * 80)
    print("📦 VERIFICANDO VOLUMES DOCKER")
    print("=" * 80)
    print()
    
    try:
        result = subprocess.run(['docker', 'volume', 'ls'], 
                              capture_output=True, text=True)
        print(result.stdout)
        
        # Verifica se o volume da Evolution existe
        if 'evolution_store' in result.stdout:
            print("✅ Volume evolution_store existe")
        else:
            print("⚠️ Volume evolution_store NÃO existe!")
            print("As instâncias não estão sendo persistidas!")
        
    except Exception as e:
        print(f"❌ Erro ao verificar volumes: {e}")

def diagnostico_completo():
    """Executa diagnóstico completo do ambiente"""
    print("\n🔍 DIAGNÓSTICO COMPLETO DO AMBIENTE\n")
    
    # 1. Verifica containers
    containers_ok = verificar_containers()
    
    if not containers_ok:
        print()
        print("=" * 80)
        print("⚠️ PROBLEMA ENCONTRADO: Evolution API não está rodando")
        print("=" * 80)
        print()
        print("SOLUÇÃO:")
        print("docker-compose up -d")
        return
    
    # 2. Verifica logs da Evolution
    verificar_logs_evolution()
    
    # 3. Testa API
    api_ok = testar_api_evolution()
    
    # 4. Verifica banco
    verificar_banco_dados()
    
    # 5. Verifica volumes
    verificar_volumes()
    
    # Resumo
    print()
    print("=" * 80)
    print("📊 RESUMO DO DIAGNÓSTICO")
    print("=" * 80)
    print()
    
    if containers_ok and api_ok:
        print("✅ Ambiente está operacional")
        print()
        print("⚠️ MAS: As instâncias não estão persistindo!")
        print()
        print("=" * 80)
        print("💡 SOLUÇÃO RECOMENDADA")
        print("=" * 80)
        print()
        print("As instâncias da Evolution estão sendo perdidas quando a API reinicia.")
        print("Isso acontece porque a configuração do banco pode estar incorreta.")
        print()
        print("OPÇÕES:")
        print()
        print("1. CRIAR INSTÂNCIA NOVAMENTE (rápido mas temporário):")
        print("   python3 resetar_instancia.py")
        print()
        print("2. CORRIGIR DOCKER-COMPOSE (permanente):")
        print("   - Verificar se DATABASE_ENABLED=true na Evolution")
        print("   - Verificar se o volume evolution_store está montado")
        print("   - Reiniciar: docker-compose down && docker-compose up -d")
        print()
    else:
        print("❌ Problemas encontrados no ambiente")
        print()
        print("Execute:")
        print("1. docker-compose down")
        print("2. docker-compose up -d")
        print("3. Aguarde 30 segundos")
        print("4. python3 resetar_instancia.py")

if __name__ == "__main__":
    diagnostico_completo()
    
    print()
    print("=" * 80)
    print("Diagnóstico finalizado!")
    print("=" * 80)
    print()
