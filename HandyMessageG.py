import requests
import time


message = "Error in MainScript!"

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
token = '7520112354:AAEDNYR-g1Umrw700SRp1EWkzShh0fDAWn8'  # Dein Bot-Token von BotFather
chat_ids = ['7215156375']  # Liste der Chat-IDs
#chat_id = '7215156375'  # Deine Chat-ID


for chat_id in chat_ids:
    send_telegram_message(token, chat_id, message)
    time.sleep(1)  # 1 Sekunde Pause zwischen den Nachrichten