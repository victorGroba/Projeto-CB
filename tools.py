import datetime
from calendar_service import buscar_eventos_do_dia

# Dicionário de dias da semana para ajudar a IA
DIAS_SEMANA = {
    0: "Segunda-feira", 1: "Terça-feira", 2: "Quarta-feira",
    3: "Quinta-feira", 4: "Sexta-feira", 5: "Sábado", 6: "Domingo"
}

def ferramenta_ver_agenda(data_relativa):
    """
    Função que a IA vai chamar.
    data_relativa: 'hoje', 'amanha', ou data 'YYYY-MM-DD'
    """
    hoje = datetime.datetime.now()
    
    if data_relativa == 'hoje':
        data_alvo = hoje
    elif data_relativa == 'amanha':
        data_alvo = hoje + datetime.timedelta(days=1)
    elif data_relativa == 'depois de amanha':
        data_alvo = hoje + datetime.timedelta(days=2)
    else:
        try:
            data_alvo = datetime.datetime.strptime(data_relativa, "%Y-%m-%d")
        except:
            return "Erro: Formato de data inválido. Use AAAA-MM-DD."

    data_str = data_alvo.strftime("%Y-%m-%d")
    dia_semana = DIAS_SEMANA[data_alvo.weekday()]
    
    # Chama o calendar service modificado na Tarefa 3
    ocupados = buscar_eventos_do_dia(data_str)
    
    return {
        "data": data_str,
        "dia_semana": dia_semana,
        "horarios_ocupados": ocupados,
        "status": "Livre" if not ocupados else "Parcialmente Ocupado"
    }

# Configuração para o Gemini saber que essa função existe
tools_config = [
    {
        "function_declarations": [
            {
                "name": "ver_agenda",
                "description": "Verifica a disponibilidade na agenda do médico para uma data específica.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "data_relativa": {
                            "type": "STRING",
                            "description": "A data desejada. Pode ser 'hoje', 'amanha' ou uma data no formato YYYY-MM-DD."
                        }
                    },
                    "required": ["data_relativa"]
                }
            }
        ]
    }
]