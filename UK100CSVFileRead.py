import csv
import os

def clean_and_convert(value, type):
    value = value.replace('â€¯', '').replace('â€', '').replace('”', '0').replace('USD', '').replace('âˆ’', '-').replace('%', '').strip()
    value = value.replace('â€¯', '').replace('GBP', '').replace('âˆ’', '-').replace('%', '').strip()
    value = value.replace(',', '.')  # Einheitliche Behandlung des Dezimaltrennzeichens
    
    if type == 'currency':
        # Prüfe und konvertiere gemäß des Suffixes
        if 'M' in value:
            return float(value.replace('M', '')) * 0.001 # Millionen
        elif 'B' in value:
            return float(value.replace('B', '')) * 1  # Milliarden
        elif 'T' in value:
            return float(value.replace('T', '')) * 1000  # Billionen
        return float(value)
    elif type == 'percentage':
        return float(value) / 100

# Hauptteil des Skripts
total_currency = 0  # Akkumulator für die Summe der Währungswerte
total_product = 0   # Akkumulator für die Summe der Produkte von Spalte 2 und Spalte 5
row_count = 0       # Zähler für die Anzahl der Zeilen

with open('ausgewaehlte_spaltenuk.csv', 'r') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for line in csv_reader:
        # Extrahiere und konvertiere Werte aus beiden Spalten
        currency_value = clean_and_convert(line['Spalte 5'], 'currency')
        percentage_value = clean_and_convert(line['Spalte 2'], 'percentage')
        
        # Addiere den konvertierten Währungswert zur Gesamtsumme
        total_currency += currency_value
        
        # Berechne das Produkt der Werte aus Spalte 2 und Spalte 5 und addiere es zur Gesamtsumme der Produkte
        product = currency_value * percentage_value
        total_product += product
        
        # Zähle die verarbeitete Zeile
        row_count += 1
        
        #print(f"Currency: {currency_value}, Percentage: {percentage_value}, Product: {product}")

# Berechne den Durchschnitt des Produkts
average_product = round(total_product / row_count, 4) if row_count else 0
print(f"Total Rows : {row_count}")

# Gib die Gesamtsumme der Spalte 5, das Gesamtprodukt und den Durchschnitt aus
#print(f"Total Currency Value in Spalte 5: {total_currency}")
#print(f"Total Product of Spalte 2 and Spalte 5: {total_product}")
print(f"Average Product per Row: {average_product}")

# Definieren Sie mehrere Pfade als Liste
file_paths = [
    "C:/Users/Fawad/AppData/Roaming/MetaQuotes/Terminal/FB52B33C7584E2EEADD1C5E58004AD52/MQL5/Files/TVuk1.txt",
    "C:/Users/fawad/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075/MQL5/Files/TVuk1.txt",
    "C:/Users/farha/AppData/Roaming/MetaQuotes/Terminal/C4CE7E5647DA1EB91E3C2593C03B1A28/MQL4/Files/TVuk1.txt",
    "C:/Ein/Weiterer/Pfad/TVdax.txt"  # Hier können Sie weitere Pfade hinzufügen
]

# Variable zum Überprüfen, ob mindestens ein Pfad existiert
written_to_file = False

# Schreibe die Zahl in alle existierenden Pfade und melde fehlende Pfade
for file_path in file_paths:
    if os.path.exists(os.path.dirname(file_path)):  # Überprüfen, ob der Ordner existiert
        with open(file_path, "w") as file:
            file.write(str(average_product))
            print(f"Die Zahl {average_product} wurde in die Datei {file_path} geschrieben.")
        written_to_file = True
    else:
        print(f"Fehler: Der Pfad {file_path} existiert nicht und wurde übersprungen.")