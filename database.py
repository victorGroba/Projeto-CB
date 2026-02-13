import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Pega a URL do banco das variáveis de ambiente (definiremos no Docker depois)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/medico_db")

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    """Cria as tabelas se não existirem"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Tabela de Pacientes
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pacientes (
            id SERIAL PRIMARY KEY,
            telefone VARCHAR(50) UNIQUE NOT NULL,
            nome VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Tabela de Histórico de Conversas (Para o bot ter memória)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS historico (
            id SERIAL PRIMARY KEY,
            telefone VARCHAR(50) NOT NULL,
            role VARCHAR(10) NOT NULL, -- 'user' ou 'model'
            mensagem TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("--- Banco de Dados Inicializado com Sucesso ---")