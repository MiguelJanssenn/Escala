# database.py

import sqlite3
import pandas as pd

DB_NAME = "escalas.db"

def conectar_db():
    """Conecta ao banco de dados SQLite e retorna a conexão e o cursor."""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    cursor = conn.cursor()
    return conn, cursor

def criar_tabelas():
    """Cria as tabelas do banco de dados se elas não existirem."""
    conn, cursor = conectar_db()
    
    # Tabela para armazenar as atividades de uma escala
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS atividades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            escala_nome TEXT NOT NULL,
            tipo TEXT NOT NULL,
            data TEXT NOT NULL,
            horario TEXT NOT NULL,
            vagas INTEGER NOT NULL
        )
    ''')
    
    # Tabela para armazenar as escolhas dos participantes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS escolhas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            escala_nome TEXT NOT NULL,
            atividade_id INTEGER NOT NULL,
            participante_nome TEXT NOT NULL,
            FOREIGN KEY (atividade_id) REFERENCES atividades (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def adicionar_atividade(escala_nome, tipo, data, horario, vagas):
    """Adiciona uma nova atividade ao banco de dados."""
    conn, cursor = conectar_db()
    cursor.execute(
        "INSERT INTO atividades (escala_nome, tipo, data, horario, vagas) VALUES (?, ?, ?, ?, ?)",
        (escala_nome, tipo, data, horario, vagas)
    )
    conn.commit()
    conn.close()

def buscar_atividades(escala_nome):
    """Busca todas as atividades de uma determinada escala e retorna como DataFrame."""
    conn, _ = conectar_db()
    query = "SELECT * FROM atividades WHERE escala_nome = ?"
    df = pd.read_sql_query(query, conn, params=(escala_nome,))
    conn.close()
    return df

def buscar_escala_completa(escala_nome):
    """Busca a escala com os nomes dos participantes."""
    conn, _ = conectar_db()
    query = """
        SELECT
            a.tipo,
            a.data,
            a.horario,
            GROUP_CONCAT(e.participante_nome, ', ') AS participantes
        FROM atividades a
        LEFT JOIN escolhas e ON a.id = e.atividade_id
        WHERE a.escala_nome = ?
        GROUP BY a.id
        ORDER BY a.data, a.horario
    """
    df = pd.read_sql_query(query, conn, params=(escala_nome,))
    conn.close()
    return df

# Inicializa o banco de dados e as tabelas ao iniciar o app
criar_tabelas()
