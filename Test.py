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
#options.add_argument("--headless=new")  # optional
options.add_argument(f"--user-data-dir={user_data_dir}")
driver = webdriver.Chrome(options=options)  # kein Service(driver_path)! Selenium Manager nimmt passenden Treiber
wait = WebDriverWait(driver, 30)

driver.get(website)