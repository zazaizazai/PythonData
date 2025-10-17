from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

# =========================
# Konfiguration
# =========================
website = "https://de.tradingview.com/screener/"

# Nutze ein separates, frisches Profil (empfohlen), NICHT dein Alltagsprofil.
# Falls du dein Profil erzwingen willst, ersetze den Pfad unten durch deinen.
user_data_dir = r"D:\Selenium\ChromeProfile_TV"  # lege diesen Ordner neu an

# =========================
# Browser starten
# =========================
options = Options()
options.add_argument("--headless=new")  # optional
options.add_argument(f"--user-data-dir={user_data_dir}")
driver = webdriver.Chrome(options=options)  # kein Service(driver_path)! Selenium Manager nimmt passenden Treiber
wait = WebDriverWait(driver, 30)

driver.get(website)

actions = [
    "(//div[@class='primaryText-Du_FoeNz primary-Ms2EU9Vx'][normalize-space()='Markt'])[1]",
    "(//div[contains(text(),'Weitere Märkte…')])[1]",
    "(//div[normalize-space()='USA'])[1]",
    "(//span[normalize-space()='Anwenden'])[1]",
    "(//div[normalize-space()='Index'])[1]",
    "(//span[@class='box-ywH2tsV_ check-ywH2tsV_ disableActiveStyles-ywH2tsV_'])[2]"
]

for xpath in actions:
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath))).click()

# Finde das erste <table>-Element auf der Seite
table = driver.find_element(By.TAG_NAME, "table")
parent_container = driver.execute_script("return arguments[0].parentNode;", table)
grandparent_container = driver.execute_script("return arguments[0].parentNode;", parent_container)

# Anzahl der Wiederholungen
scroll_anzahl = 5
for _ in range(scroll_anzahl):
    driver.execute_script("arguments[0].scrollTop += 4000;", grandparent_container)
    time.sleep(1) 
    
# Daten extrahieren und speichern
rows = driver.find_elements(By.TAG_NAME, 'tr')
data = [
    [cells[2].text.strip(), cells[5].text.strip()]
    for row in rows if (cells := row.find_elements(By.TAG_NAME, 'td')) and len(cells) >= 5
]

if data:
    pd.DataFrame(data, columns=['Spalte 2', 'Spalte 5']).to_csv('ausgewaehlte_spaltenna.csv', index=False)
    df = pd.DataFrame(data, columns=['Spalte 2', 'Spalte 5'])
    #print(df)
    

driver.quit()