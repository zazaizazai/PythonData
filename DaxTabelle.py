import requests
from bs4 import BeautifulSoup

# Schritt 1: Abrufen der Webseite
url = 'https://www.finanznachrichten.de/aktienkurse-index/dj-industrial.htm'
response = requests.get(url)

# Überprüfen, ob die Anfrage erfolgreich war
if response.status_code == 200:
    # Schritt 2: Parsen der Webseite mit BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Schritt 3: Extrahieren der gewünschten Daten
    table_rows = soup.find_all('tr')
    
    # Listen zum Speichern der gewünschten Werte
    changes = []
    second_column_values = []
    
    for row in table_rows:
        columns = row.find_all('td')
        if len(columns) >= 5:  # Sicherstellen, dass die Reihe genug Spalten hat
            second_column = columns[1].text.strip()  # 2. Spalte (Index 1)
            change_column = columns[3].text.strip()  # 5. Spalte (Index 4) ist die "+/-" Spalte
            
            second_column_values.append(second_column)
            changes.append(change_column)
    
    # Ausgabe der extrahierten Daten
    print("Werte der 2. Spalte:")
    for value in second_column_values:
        print(value)
    
    print("\nWerte der '+/-' Spalte:")
    for change in changes:
        print(change)
else:
    print("Fehler beim Abrufen der Seite:", response.status_code)

