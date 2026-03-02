import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os

# --- CONFIGURACIÓN ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
MAE_KEY = os.getenv('MAE_API_KEY')
CSV_FILE = 'datos_dia.csv'

# URLs OFICIALES DE A3
URL_RENTA_FIJA = "https://api.mae.com.ar/MarketData/v1/mercado/cotizaciones/rentafija"

def obtener_datos_mae(url):
    """Consulta la API con headers de navegación real para evitar Error 403."""
    try:
        headers = {
            'x-api-key': MAE_KEY,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'es-AR,es;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://marketdata.mae.com.ar/',
            'Origin': 'https://marketdata.mae.com.ar'
        }
        r = requests.get(url, headers=headers, timeout=15)
        
        if r.status_code == 200:
            print("¡Conexión exitosa! Datos recibidos.")
            return r.json()
        else:
            print(f"Error API: Código {r.status_code}. El servidor sigue bloqueando.")
    except Exception as e:
        print(f"Error de conexión: {e}")
    return None

def manejar_datos():
    ahora = datetime.now()
    timestamp = ahora.strftime('%Y-%m-%d %H:%M')
    
    rf_data = obtener_datos_mae(URL_RENTA_FIJA)
    datos = []
    
    if rf_data and isinstance(rf_data, list):
        for item in rf_data:
            ticker = item.get('ticker')
            moneda = item.get('monedaEscrituracion')
            precio = item.get('precioUltimo')
            
            # Filtramos AL30 en ambas monedas
            if ticker == 'AL30' and precio:
                label = f"AL30_{moneda}"
                datos.append([timestamp, label, float(precio)])

    if datos:
        df_nuevos = pd.DataFrame(datos, columns=['timestamp', 'activo', 'valor'])
        df_nuevos.to_csv(CSV_FILE, mode='a', header=not os.path.exists(CSV_FILE), index=False)
        return True
    return False

def generar_y_enviar_reporte():
    if not os.path.exists(CSV_FILE): return
    
    df = pd.read_csv(CSV_FILE)
    if df.empty: return
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()

    # AL30 Pesos
    df_ars = df[df['activo'] == 'AL30_ARS']
    if not df_ars.empty:
        ax1.plot(df_ars['timestamp'], df_ars['valor'], color='gold', label='AL30 ARS ($)', marker='o')
    
    # AL30 Dólares
    df_usd = df[df['activo'] == 'AL30_USD']
    if not df_usd.empty:
        ax2.plot(df_usd['timestamp'], df_usd['valor'], color='green', label='AL30 USD (u$s)', marker='s')

    ax1.set_ylabel('Precio Pesos ($)', color='orange')
    ax2.set_ylabel('Precio Dólares (u$s)', color='green')
    plt.title(f'Monitor AL30 Final de Rueda - {datetime.now().strftime("%H:%M")}')
    
    plt.savefig('reporte.png')
    plt.close()

    # Enviar a Telegram
    url_tel = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open('reporte.png', 'rb') as f:
        caption = f"🏁 *Cierre de Rueda*\nMonitor AL30 con Headers de Navegación."
        requests.post(url_tel, data={'chat_id': CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}, files={'photo': f})

if __name__ == "__main__":
    if manejar_datos():
        generar_y_enviar_reporte()
