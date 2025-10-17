import requests
import time

# Beispiel-Pfad zur Datei
pfad = "C:/Users/farha/AppData/Roaming/MetaQuotes/Terminal/C4CE7E5647DA1EB91E3C2593C03B1A28/MQL4/Files/OOrder.txt"

# Initialisiere die Nachricht
message = ""

try:
    # Datei öffnen und auslesen
    with open(pfad, 'r', encoding='utf-8') as file:
        inhalt = file.read()

    # Überprüfen, ob die Datei leer ist
    if not inhalt:
        message = "Fehler: Die Datei ist leer oder enthält keinen Inhalt."
    else:
        # Den gelesenen Inhalt zur Nachricht hinzufügen
        message = f"Message:\n{inhalt}"

except FileNotFoundError:
    message = f"Fehler: Die Datei '{pfad}' wurde nicht gefunden."
except Exception as e:
    message = f"Ein unerwarteter Fehler ist aufgetreten: {e}"

# Nachricht ausgeben
print(message)

def send_telegram_message(token, chat_id, message):
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    data = {'chat_id': chat_id, 'text': message}
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print("Nachricht erfolgreich gesendet.")
    else:
        print(f"Fehler beim Senden der Nachricht: {response.status_code}")

# Beispiel: Nachricht senden
token = '7520112354:AAF63MXdHYmDg_oCqsuZeaV8MXm1ltYRXC4'  # Dein Bot-Token von BotFather
chat_ids = ['7215156375']  # Liste der Chat-IDs
#chat_id = '7215156375'  # Deine Chat-ID


for chat_id in chat_ids:
    send_telegram_message(token, chat_id, message)
    time.sleep(1)  # 1 Sekunde Pause zwischen den Nachrichten