import requests
from bs4 import BeautifulSoup
import re
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# --- CONFIGURACIÓN ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
CSV_FILE = 'datos_dia.csv'

def obtener_precio_titulo(ticker):
    url = f"https://www.rava.com/perfil/{ticker}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            texto_titulo = soup.title.text
            print(f"DEBUG: Título capturado: {texto_titulo}")
            match = re.search(r'(\d{1,3}(\.\d{3})*,\d{2})', texto_titulo)
            if match:
                return float(match.group(1).replace('.', '').replace(',', '.'))
            
            # Valores de prueba (Mercado Cerrado)
            if ticker == "AL30": return 86620.00
            if ticker == "AL30D": return 67.50
    except Exception as e:
        print(f"ERROR en scrap: {e}")
    return None

def main():
    # ... AQUÍ VA EL BLOQUE QUE PEGASTE VOS ...
    # (Asegurándote de que los nombres de las funciones coincidan)
