import datetime
import os.path
from google.oauth2 import service_account
from googleapiclient.discovery import build
import pytz

# Configurações
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
SERVICE_ACCOUNT_FILE = 'credentials.json'
# Se a agenda não for a principal da conta de serviço, coloque o email dela aqui
# Caso contrário, deixe 'primary'
CALENDAR_ID = 'victorgroba2@gmail.com' 

def get_calendar_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('calendar', 'v3', credentials=creds)

def buscar_eventos_do_dia(data_str):
    """
    data_str: string no formato 'YYYY-MM-DD'
    Retorna uma string descrevendo os horários ocupados.
    """
    try:
        service = get_calendar_service()
        tz = pytz.timezone('America/Sao_Paulo')
        
        # Converte a string YYYY-MM-DD para datetime
        data_base = datetime.datetime.strptime(data_str, "%Y-%m-%d")
        
        # Define inicio e fim do dia no fuso horário correto
        inicio_dia = data_base.replace(hour=0, minute=0, second=0).astimezone(tz)
        fim_dia = data_base.replace(hour=23, minute=59, second=59).astimezone(tz)
        
        # Formata para ISO exigido pelo Google (ex: 2023-10-01T00:00:00-03:00)
        time_min = inicio_dia.isoformat()
        time_max = fim_dia.isoformat()

        print(f"Buscando eventos de {time_min} até {time_max}...") # Log para debug

        events_result = service.events().list(
            calendarId=CALENDAR_ID, 
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])

        if not events:
            return "A agenda está totalmente livre neste dia."

        resultado = "Horários OCUPADOS neste dia:\n"
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            # Pega só a hora HH:MM
            hora = start.split('T')[1][:5] if 'T' in start else "Dia todo"
            resultado += f"- {hora} (Ocupado)\n"
            
        return resultado

    except Exception as e:
        return f"Erro ao acessar agenda: {str(e)}"
