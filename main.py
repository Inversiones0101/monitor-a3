import requests
from bs4 import BeautifulSoup
import re
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# --- CONFIGURACIÓN DE TELEGRAM ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
CSV_FILE = 'datos_dia.csv'

def obtener_precio_titulo(ticker):
    url = f"https://www.rava.com/perfil/{ticker}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            # Leemos la etiqueta <title> que vimos en las DevTools
            texto_titulo = soup.title.text
            print(f"DEBUG: Título capturado para {ticker}: {texto_titulo}")
            
            # Buscamos el patrón de precio (ej: 86.620,00)
            match = re.search(r'(\d{1,3}(\.\d{3})*,\d{2})', texto_titulo)
            
            if match:
                precio_str = match.group(1).replace('.', '').replace(',', '.')
                return float(precio_str)
            else:
                # Plan B: buscar en el cuerpo si el título no tiene el número
                precio_tag = soup.find('span', {'class': 'ultimo'})
                if precio_tag:
                    val = precio_tag.text.replace('.', '').replace(',', '.')
                    return float(val)
                    
        print(f"ERROR: No se obtuvo precio de {ticker}. Status: {r.status_code}")
    except Exception as e:
        print(f"EXCEPCIÓN en {ticker}: {e}")
    return None

def main():
    print(f"--- INICIANDO BOT ({datetime.now().strftime('%H:%M:%S')}) ---")
    
    # Llamamos a la función con el nombre correcto
    al30_ars = obtener_precio_titulo("AL30")
    al30_usd = obtener_precio_titulo("AL30D")
    
    if al30_ars and al30_usd:
        mep = round(al30_ars / al30_usd, 2)
        ahora = datetime.now().strftime('%H:%M')
        
        print(f"RESULTADO: AL30: ${al30_ars} | AL30D: u$s{al30_usd} | MEP: ${mep}")
        
        # Guardar en CSV
        nuevo_dato = pd.DataFrame([{'fecha': ahora, 'mep': mep}])
        nuevo_dato.to_csv(CSV_FILE, mode='a', header=not os.path.exists(CSV_FILE), index=False)
        
        # Generar gráfico
        if os.path.exists(CSV_FILE):
            df = pd.read_csv(CSV_FILE)
            plt.figure(figsize=(10, 5))
            plt.plot(df['fecha'], df['mep'], marker='o', color='#1f77b4', linewidth=2)
            plt.title(f"Evolución Dólar MEP - {datetime.now().strftime('%d/%m/%Y')}")
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.savefig('grafico.png')
            plt.close()
        
            # Enviar a Telegram
            mensaje = f"📊 *Reporte Rava Realtime*\n\n🔹 AL30: ${al30_ars}\n🔹 AL30D: u$s{al30_usd}\n\n💰 *MEP: ${mep}*"
            url_tel = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
            
            with open('grafico.png', 'rb') as foto:
                payload = {'chat_id': CHAT_ID, 'caption': mensaje, 'parse_mode': 'Markdown'}
                files = {'photo': foto}
                requests.post(url_tel, data=payload, files=files)
            
            print("--- PROCESO COMPLETADO EXITOSAMENTE ---")
    else:
        print("--- PROCESO FALLIDO: Faltan datos ---")

if __name__ == "__main__":
    main()
