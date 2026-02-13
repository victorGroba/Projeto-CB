import datetime
import os.path
from google.oauth2 import service_account
from googleapiclient.discovery import build
import pytz

# --- Configurações ---
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
SERVICE_ACCOUNT_FILE = 'credentials.json'
# Ajuste o email se necessário
CALENDAR_ID = 'victorgroba2@gmail.com' 
TZ_SP = pytz.timezone('America/Sao_Paulo')

def get_calendar_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('calendar', 'v3', credentials=creds)

def buscar_eventos_do_dia(data_str):
    """
    Retorna uma LISTA de horários ocupados.
    Exemplo de retorno: ['14:00', '14:30'] ou [] se livre.
    """
    try:
        service = get_calendar_service()
        # Define horário inicial e final do dia
        data_base = datetime.datetime.strptime(data_str, "%Y-%m-%d")
        inicio_dia = data_base.replace(hour=0, minute=0, second=0).astimezone(TZ_SP)
        fim_dia = data_base.replace(hour=23, minute=59, second=59).astimezone(TZ_SP)

        events_result = service.events().list(
            calendarId=CALENDAR_ID, 
            timeMin=inicio_dia.isoformat(),
            timeMax=fim_dia.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        ocupados = []

        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            # Se for evento de dia inteiro, ignora hora
            if 'T' in start:
                hora = start.split('T')[1][:5]
                ocupados.append(hora)
            else:
                return ["DIA_INTEIRO"] # Código especial para dia cheio

        return ocupados

    except Exception as e:
        print(f"Erro Calendar: {e}")
        return []

def listar_proximos_dias(qtd_dias=3):
    """Gera um resumo rápido para a IA entender a disponibilidade futura."""
    hoje = datetime.datetime.now(TZ_SP)
    resumo = []

    for i in range(qtd_dias):
        data_alvo = hoje + datetime.timedelta(days=i)
        data_str = data_alvo.strftime("%Y-%m-%d")
        # Tradução manual simples dos dias
        dias_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
        dia_semana = dias_semana[data_alvo.weekday()]
        data_fmt = data_alvo.strftime("%d/%m")

        status = buscar_eventos_do_dia(data_str)
        resumo.append(f"- {dia_semana} ({data_fmt}): {status}")

    return "\n".join(resumo)
