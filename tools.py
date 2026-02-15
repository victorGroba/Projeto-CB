# tools.py
import datetime
import google.generativeai as genai

# Configuração das ferramentas para o Gemini
tools_config = [
    {
        "function_declarations": [
            {
                "name": "ver_agenda",
                "description": "Verifica os horários disponíveis na agenda do médico.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "data_relativa": {
                            "type": "STRING",
                            "description": "A data para verificar (ex: 'hoje', 'amanhã', 'segunda-feira' ou '2026-02-20')."
                        }
                    },
                    "required": ["data_relativa"]
                }
            },
            {
                "name": "agendar_consulta",
                "description": "Agenda uma consulta para o paciente após confirmar todos os dados.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "nome_paciente": {"type": "STRING", "description": "Nome completo do paciente"},
                        "telefone": {"type": "STRING", "description": "Telefone do paciente com DDD"},
                        "data": {"type": "STRING", "description": "Data da consulta (YYYY-MM-DD)"},
                        "horario": {"type": "STRING", "description": "Horário da consulta (HH:MM)"}
                    },
                    "required": ["nome_paciente", "telefone", "data", "horario"]
                }
            }
        ]
    }
]

# Funções Python reais que a IA vai chamar
def ferramenta_ver_agenda(data_relativa):
    """Simulação de busca na agenda"""
    # Aqui você conectaria com seu Google Calendar ou Banco de Dados real
    print(f"--- TOOL: Verificando agenda para {data_relativa} ---")
    
    # Exemplo estático para teste
    return {
        "status": "sucesso",
        "mensagem": f"Para {data_relativa}, temos horários às 14:00, 15:30 e 17:00.",
        "horarios_livres": ["14:00", "15:30", "17:00"]
    }

def agendar_consulta(nome_paciente, telefone, data, horario):
    """Simulação de agendamento"""
    print(f"--- TOOL: Agendando para {nome_paciente} em {data} às {horario} ---")
    
    # Aqui você salvaria no banco 'pacientes' ou Google Calendar
    return {
        "status": "sucesso",
        "mensagem": f"Confirmado! Consulta agendada para {nome_paciente} no dia {data} às {horario}. Aguardamos você!"
    }
