import subprocess
import time

def run_script(script_path, error_script_path):
    try:
        # Führe das Python-Skript synchron aus und überprüfe auf Fehler
        subprocess.run(['python', script_path], check=True)
        print(f"{script_path} wurde erfolgreich ausgeführt.")
    except subprocess.CalledProcessError as e:
        # Fehlerbehandlung, falls das Skript einen Fehler erzeugt
        print(f"Fehler bei der Ausführung von {script_path}: {e}")
        # Führe das Fehlerbehandlungs-Skript aus
        try:
            print(f"Starte das Fehlerbehandlungs-Skript: {error_script_path}")
            subprocess.run(['python', error_script_path], check=True)
            print(f"{error_script_path} wurde erfolgreich ausgeführt.")
        except subprocess.CalledProcessError as error_in_error_script:
            print(f"Fehler bei der Ausführung von {error_script_path}: {error_in_error_script}")

# Liste der Skripte
scripts = [
    'S&P500Data.py', 'S&P500CSVFileRead.py', 'DOWData.py', 'DOWCSVFileRead.py',
    'NASData.py', 'NASCSVFileRead.py', 'NIKKEIData.py', 'NIKKEICSVFileRead.py',
    'DAXData.py', 'DAXCSVFileRead.py', 'UK100Data.py', 'UK100CSVFileRead.py',
    'HSI80Data.py', 'HSI80CSVFileRead.py', 'FRENCH40Data.py', 'FRENCH40CSVFileRead.py',
    'ES35Data.py', 'ES35CSVFileRead.py', 'ITA40Data.py', 'ITA40CSVFileRead.py', 'EURX50Data.py', 
    'EURX50CSVFileRead.py', 'N25Data.py', 'N25CSVFileRead.py', 'SUI20Data.py', 'SUI20CSVFileRead.py'
]

# Pfad des Fehlerbehandlungs-Skripts
error_script = 'HandymessageG.py'

while True:
    for script in scripts:
        run_script(script, error_script)
    print("Warte bis zum nächsten Lauf...")
    time.sleep(5)  # Warte 
