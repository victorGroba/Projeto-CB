import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    """Conecta ao PostgreSQL"""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgres_db"),
        database=os.getenv("POSTGRES_DB", "medico_db"),
        user=os.getenv("POSTGRES_USER", "user"),
        password=os.getenv("POSTGRES_PASSWORD", "password")
    )

def init_db():
    """Cria as tabelas se não existirem"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 1. Tabela de Histórico (Para o bot ter memória da conversa)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS historico (
            id SERIAL PRIMARY KEY,
            telefone VARCHAR(50) NOT NULL,
            role VARCHAR(10) NOT NULL,
            mensagem TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 2. Tabela de Pacientes (Para agendamentos)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pacientes (
            id SERIAL PRIMARY KEY,
            telefone VARCHAR(50) UNIQUE NOT NULL,
            nome VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # 3. Tabela de mapeamento @lid -> número real (MEMÓRIA AUTOMÁTICA)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS lid_mapping (
            lid_jid VARCHAR(100) PRIMARY KEY,
            numero_real VARCHAR(100) NOT NULL,
            push_name VARCHAR(200),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    print("--- Banco de Dados Inicializado com Sucesso ---")

# --- FUNÇÕES DE MENSAGENS E HISTÓRICO ---

def salvar_mensagem(telefone, role, mensagem):
    """Salva a mensagem no histórico"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO historico (telefone, role, mensagem) VALUES (%s, %s, %s)",
            (telefone, role, mensagem)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Erro ao salvar mensagem: {e}")

def buscar_historico(telefone, limite=10):
    """Recupera as últimas mensagens para dar contexto à IA"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT role, mensagem FROM historico WHERE telefone = %s ORDER BY created_at DESC LIMIT %s",
            (telefone, limite)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        # O banco retorna do mais recente para o antigo, precisamos inverter para a IA ler na ordem certa
        historico = []
        for row in reversed(rows):
            role = "user" if row[0] == "user" else "model"
            historico.append({"role": role, "parts": [row[1]]})
            
        return historico
    except Exception as e:
        print(f"Erro ao buscar histórico: {e}")
        return []

# --- FUNÇÕES DE PACIENTES ---

def salvar_ou_atualizar_paciente(telefone, nome):
    """Salva paciente para agendamentos"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO pacientes (telefone, nome) 
            VALUES (%s, %s)
            ON CONFLICT (telefone) 
            DO UPDATE SET nome = EXCLUDED.nome
        """, (telefone, nome))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Erro ao salvar paciente: {e}")

# --- FUNÇÕES NOVAS (RESOLUÇÃO DE @LID) ---

def salvar_lid_mapping(lid_jid, numero_real, push_name):
    """Memoriza quem é o dono do @lid"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Upsert: Se já existe, atualiza. Se não, cria.
        cur.execute("""
            INSERT INTO lid_mapping (lid_jid, numero_real, push_name, updated_at)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (lid_jid) 
            DO UPDATE SET numero_real = %s, push_name = %s, updated_at = CURRENT_TIMESTAMP
        """, (lid_jid, numero_real, push_name, numero_real, push_name))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Erro ao salvar mapeamento LID: {e}")
        return False

def buscar_lid_mapping(lid_jid):
    """Consulta a memória para ver se já conhecemos esse @lid"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT numero_real FROM lid_mapping WHERE lid_jid = %s", (lid_jid,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        print(f"Erro ao buscar mapeamento LID: {e}")
        return None
