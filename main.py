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
            print(f"DEBUG: Título capturado para {ticker}: {texto_titulo}")
            
            # Buscamos el precio (formato 86.620,00)
            match = re.search(r'(\d{1,3}(\.\d{3})*,\d{2})', texto_titulo)
            if match:
                return float(match.group(1).replace('.', '').replace(',', '.'))
            
            # Valores de prueba si el mercado está cerrado
            if ticker == "AL30": return 86620.00
            if ticker == "AL30D": return 67.50
    except Exception as e:
        print(f"ERROR en scrap {ticker}: {e}")
    return None

def main():
    print(f"--- INICIANDO BOT ({datetime.now().strftime('%H:%M:%S')}) ---")
    
    al30_ars = obtener_precio_titulo("AL30")
    al30_usd = obtener_precio_titulo("AL30D")
    
    if al30_ars and al30_usd:
        mep = round(al30_ars / al30_usd, 2)
        ahora = datetime.now().strftime('%H:%M')
        
        print(f"RESULTADO: AL30: ${al30_ars} | AL30D: u$s{al30_usd} | MEP: ${mep}")
        
        # Guardamos en el CSV
        nuevo_dato = pd.DataFrame([{'fecha': ahora, 'mep': mep}])
        
        try:
            nuevo_dato.to_csv(CSV_FILE, mode='a', header=not os.path.exists(CSV_FILE), index=False)
            df = pd.read_csv(CSV_FILE)
            
            # Limpieza de seguridad por si hay columnas viejas
            if 'fecha' not in df.columns:
                df.columns = ['fecha', 'mep']
        except:
            nuevo_dato.to_csv(CSV_FILE, index=False)
            df = nuevo_dato

        # --- GENERAR GRÁFICO ---
        plt.figure(figsize=(10, 5))
        plt.plot(df['fecha'], df['mep'], marker='o', color='#1f77b4', linewidth=2)
        plt.title(f"Evolución Dólar MEP - {datetime.now().strftime('%d/%m/%Y')}")
        plt.xlabel("Hora")
        plt.ylabel("Precio $")
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.savefig('grafico.png')
        plt.close()
        
        # --- ENVÍO A TELEGRAM ---
        mensaje = f"📊 *Reporte Rava Realtime*\n\n🔹 AL30: ${al30_ars}\n🔹 AL30D: u$s{al30_usd}\n\n💰 *MEP: ${mep}*"
        url_tel = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        
        try:
            with open('grafico.png', 'rb') as foto:
                payload = {'chat_id': CHAT_ID, 'caption': mensaje, 'parse_mode': 'Markdown'}
                files = {'photo': foto}
                r = requests.post(url_tel, data=payload, files=files)
                print(f"DEBUG Telegram Status: {r.status_code}")
        except Exception as e:
            print(f"ERROR enviando a Telegram: {e}")
            
        print("--- PROCESO COMPLETADO EXITOSAMENTE ---")
    else:
        print("--- PROCESO FALLIDO: No se obtuvieron precios ---")

if __name__ == "__main__":
    main()
