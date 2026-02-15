import subprocess
import re
import os

def pegar_ip_chatwoot():
    print("🔍 Buscando IP do Chatwoot...")
    try:
        # Executa o comando docker inspect
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}", "chatwoot_base"],
            capture_output=True, text=True
        )
        ip = result.stdout.strip()
        
        # Validação simples de IP (deve ter pontos e números)
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
            print(f"✅ IP Encontrado: {ip}")
            return ip
        else:
            print(f"❌ IP inválido encontrado: '{ip}'")
            return None
    except Exception as e:
        print(f"❌ Erro ao buscar IP: {e}")
        return None

def atualizar_script_conexao(ip):
    arquivo = "conectar_final.py"
    
    if not os.path.exists(arquivo):
        print(f"❌ Arquivo {arquivo} não encontrado!")
        return False
        
    print(f"📝 Atualizando {arquivo}...")
    
    with open(arquivo, "r") as f:
        conteudo = f.read()
    
    # Nova URL com o IP correto e porta 3000
    nova_url = f'CHATWOOT_DOCKER_URL = "http://{ip}:3000/"'
    
    # Substitui qualquer linha que comece com CHATWOOT_DOCKER_URL
    novo_conteudo = re.sub(
        r'CHATWOOT_DOCKER_URL\s*=\s*".*"', 
        nova_url, 
        conteudo
    )
    
    if conteudo == novo_conteudo:
        # Se o regex falhar, tenta adicionar no final ou substituir manualmente
        print("⚠️ Não encontrei a linha para substituir, tentando forçar...")
        novo_conteudo = conteudo.replace(
            'CHATWOOT_DOCKER_URL = "http://chatwoot_base:3000/"', 
            nova_url
        )
    
    with open(arquivo, "w") as f:
        f.write(novo_conteudo)
        
    print("✅ Arquivo atualizado com sucesso!")
    return True

if __name__ == "__main__":
    print("="*50)
    print("🛠️ CORRETOR AUTOMÁTICO DE IP")
    print("="*50)
    
    ip = pegar_ip_chatwoot()
    
    if ip:
        if atualizar_script_conexao(ip):
            print("\n🚀 Executando a integração agora...\n")
            os.system("python3 conectar_final.py")
    else:
        print("\n❌ Não foi possível corrigir automaticamente.")
        print("Verifique se o container 'chatwoot_base' está rodando com 'docker ps'")
