import json
from datetime import datetime, timedelta
import pytz
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Carrega as credenciais do Google Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'credentials.json'

def get_calendar_service():
    """Retorna o serviço da API do Google Calendar"""
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=creds)
    return service

def ferramenta_ver_agenda(data_relativa='hoje'):
    """
    Busca os horários livres/ocupados na agenda do Google Calendar
    
    Args:
        data_relativa (str): 'hoje', 'amanha', ou data no formato 'YYYY-MM-DD'
    
    Returns:
        dict: Informação sobre a agenda no dia especificado
    """
    try:
        # Define o timezone
        tz = pytz.timezone('America/Sao_Paulo')
        
        # Calcula a data baseado no parâmetro
        if data_relativa == 'hoje':
            data = datetime.now(tz).date()
        elif data_relativa == 'amanha':
            data = (datetime.now(tz) + timedelta(days=1)).date()
        else:
            # Tenta parsear como data (YYYY-MM-DD)
            data = datetime.strptime(data_relativa, '%Y-%m-%d').date()
        
        # Define o horário de funcionamento do consultório (8h às 18h)
        inicio_dia = tz.localize(datetime.combine(data, datetime.min.time().replace(hour=8)))
        fim_dia = tz.localize(datetime.combine(data, datetime.min.time().replace(hour=18)))
        
        # Busca eventos do Google Calendar
        service = get_calendar_service()
        
        # Lista eventos no período
        events_result = service.events().list(
            calendarId='primary',
            timeMin=inicio_dia.isoformat(),
            timeMax=fim_dia.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        eventos = events_result.get('items', [])
        
        # Processa os horários ocupados
        horarios_ocupados = []
        for evento in eventos:
            start = evento['start'].get('dateTime', evento['start'].get('date'))
            end = evento['end'].get('dateTime', evento['end'].get('date'))
            summary = evento.get('summary', 'Ocupado')
            
            horarios_ocupados.append({
                'inicio': start,
                'fim': end,
                'titulo': summary
            })
        
        # Calcula horários livres (intervalos de 1 hora)
        horarios_livres = []
        hora_atual = inicio_dia
        
        while hora_atual < fim_dia:
            hora_fim_slot = hora_atual + timedelta(hours=1)
            
            # Verifica se este slot está livre
            slot_livre = True
            for ocupado in horarios_ocupados:
                inicio_ocupado = datetime.fromisoformat(ocupado['inicio'].replace('Z', '+00:00'))
                fim_ocupado = datetime.fromisoformat(ocupado['fim'].replace('Z', '+00:00'))
                
                # Se há sobreposição, o slot está ocupado
                if not (hora_fim_slot <= inicio_ocupado or hora_atual >= fim_ocupado):
                    slot_livre = False
                    break
            
            if slot_livre:
                horarios_livres.append(hora_atual.strftime('%H:%M'))
            
            hora_atual = hora_fim_slot
        
        # Retorna resultado estruturado
        resultado = {
            'data': data.strftime('%d/%m/%Y'),
            'dia_semana': data.strftime('%A'),
            'horarios_livres': horarios_livres,
            'total_livres': len(horarios_livres),
            'horarios_ocupados': [
                {
                    'horario': datetime.fromisoformat(h['inicio'].replace('Z', '+00:00')).strftime('%H:%M'),
                    'titulo': h['titulo']
                } for h in horarios_ocupados
            ]
        }
        
        return resultado
        
    except Exception as e:
        return {
            'erro': str(e),
            'mensagem': 'Não foi possível consultar a agenda no momento.'
        }

def agendar_consulta(nome_paciente, telefone, data, horario):
    """
    Agenda uma consulta no Google Calendar
    
    Args:
        nome_paciente (str): Nome completo do paciente
        telefone (str): Telefone do paciente
        data (str): Data no formato 'YYYY-MM-DD'
        horario (str): Horário no formato 'HH:MM'
    
    Returns:
        dict: Confirmação do agendamento
    """
    try:
        tz = pytz.timezone('America/Sao_Paulo')
        
        # Converte data e horário para datetime
        data_obj = datetime.strptime(data, '%Y-%m-%d').date()
        hora_obj = datetime.strptime(horario, '%H:%M').time()
        
        inicio = tz.localize(datetime.combine(data_obj, hora_obj))
        fim = inicio + timedelta(hours=1)  # Consulta de 1 hora
        
        # Cria o evento no Google Calendar
        service = get_calendar_service()
        
        evento = {
            'summary': f'Consulta - {nome_paciente}',
            'description': f'Paciente: {nome_paciente}\nTelefone: {telefone}',
            'start': {
                'dateTime': inicio.isoformat(),
                'timeZone': 'America/Sao_Paulo',
            },
            'end': {
                'dateTime': fim.isoformat(),
                'timeZone': 'America/Sao_Paulo',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 60},
                    {'method': 'popup', 'minutes': 1440},  # 1 dia antes
                ],
            },
        }
        
        evento_criado = service.events().insert(calendarId='primary', body=evento).execute()
        
        return {
            'sucesso': True,
            'evento_id': evento_criado['id'],
            'data': data_obj.strftime('%d/%m/%Y'),
            'horario': horario,
            'paciente': nome_paciente,
            'mensagem': f'Consulta agendada com sucesso para {nome_paciente} em {data_obj.strftime("%d/%m/%Y")} às {horario}'
        }
        
    except Exception as e:
        return {
            'sucesso': False,
            'erro': str(e),
            'mensagem': 'Não foi possível agendar a consulta. Tente novamente.'
        }

# Configuração das ferramentas para o Gemini
tools_config = [
    {
        "function_declarations": [
            {
                "name": "ver_agenda",
                "description": "Consulta os horários disponíveis na agenda do Dr. Victor para um dia específico. Use esta ferramenta SEMPRE que o paciente perguntar sobre horários disponíveis.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "data_relativa": {
                            "type": "string",
                            "description": "Dia que deseja consultar: 'hoje', 'amanha', ou data no formato 'YYYY-MM-DD' (ex: '2024-03-15')",
                            "enum": ["hoje", "amanha"]
                        }
                    },
                    "required": ["data_relativa"]
                }
            },
            {
                "name": "agendar_consulta",
                "description": "Agenda uma consulta no Google Calendar do Dr. Victor. Use esta ferramenta apenas quando tiver TODAS as informações: nome completo, telefone, data e horário confirmados.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "nome_paciente": {
                            "type": "string",
                            "description": "Nome completo do paciente"
                        },
                        "telefone": {
                            "type": "string",
                            "description": "Telefone do paciente (com DDD)"
                        },
                        "data": {
                            "type": "string",
                            "description": "Data da consulta no formato 'YYYY-MM-DD'"
                        },
                        "horario": {
                            "type": "string",
                            "description": "Horário da consulta no formato 'HH:MM' (ex: '14:00')"
                        }
                    },
                    "required": ["nome_paciente", "telefone", "data", "horario"]
                }
            }
        ]
    }
]