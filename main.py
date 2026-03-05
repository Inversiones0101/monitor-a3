import requests
import pandas as pd
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
from datetime import datetime
import os

# --- CONFIGURACIÓN ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
CSV_FILE = 'datos_dia.csv'

def obtener_precio_rava(ticker):
    url = f"https://www.rava.com/perfil/{ticker}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        session = requests.Session()
        r = session.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # Intentamos 3 formas distintas de encontrar el precio
            # 1. Por clase 'ultimo'
            tag = soup.find('span', {'class': 'ultimo'})
            
            # 2. Si falla, buscamos por el formato de número grande de Rava
            if not tag:
                tag = soup.select_one('span.precio-grande')
            
            # 3. Si sigue fallando, buscamos cualquier span que tenga un número con coma
            if not tag:
                for span in soup.find_all('span'):
                    if ',' in span.text and len(span.text) < 15:
                        # Verificamos que sea un número
                        test_str = span.text.replace('.', '').replace(',', '').strip()
                        if test_str.isdigit():
                            tag = span
                            break

            if tag:
                val = tag.text.replace('.', '').replace(',', '.').strip()
                print(f"DEBUG: {ticker} capturado con éxito: {val}")
                return float(val)
                
        print(f"DEBUG: Rava respondió 200 pero no hallamos el precio de {ticker}")
    except Exception as e:
        print(f"DEBUG: Error técnico en {ticker}: {e}")
    return None

def ejecutar_prueba():
    print("--- INICIANDO PRUEBA DE CAPTURA ---")
    p_ars = obtener_precio_rava("AL30")
    p_usd = obtener_precio_rava("AL30D")
    
    if p_ars and p_usd:
        mep = round(p_ars / p_usd, 2)
        ahora = datetime.now().strftime('%H:%M')
        print(f"LOG: AL30: {p_ars} | AL30D: {p_usd} | MEP: {mep}")
        
        # Guardar en CSV para tener historial
        df = pd.DataFrame([{'timestamp': datetime.now(), 'activo': 'MEP', 'valor': mep}])
        df.to_csv(CSV_FILE, mode='a', header=not os.path.exists(CSV_FILE), index=False)
        
        # Generar gráfico de prueba (aunque sea un punto)
        plt.figure(figsize=(10, 5))
        plt.plot([ahora], [mep], marker='o', color='red', label='Dólar MEP')
        plt.title(f"Prueba de Conexión Rava - {ahora}")
        plt.legend()
        plt.savefig('prueba.png')
        plt.close()
        
        # Enviar a Telegram
        url_tel = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        with open('prueba.png', 'rb') as f:
            caption = f"✅ Prueba Exitosa\nAL30: ${p_ars}\nMEP: ${mep}"
            requests.post(url_tel, data={'chat_id': CHAT_ID, 'caption': caption}, files={'photo': f})
        print("--- PRUEBA FINALIZADA: REVISÁ TELEGRAM ---")
    else:
        print("--- PRUEBA FALLIDA: NO SE OBTUVIERON PRECIOS ---")

if __name__ == "__main__":
    ejecutar_prueba()
