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

# URLs ACTUALIZADAS SEGÚN ENDPOINTS DE A3
URL_CAUCIONES = "https://api.mae.com.ar/MarketData/v1/mercado/cotizaciones/cauciones"
URL_RENTA_FIJA = "https://api.mae.com.ar/MarketData/v1/mercado/cotizaciones/rentafija"

def obtener_datos_mae(url):
    try:
        # Agregamos un User-Agent más completo para evitar el bloqueo 403
        headers = {
            'x-api-key': MAE_KEY, 
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json'
        }
        r = requests.get(url, headers=headers, timeout=15)
        
        if r.status_code == 200:
            return r.json()
        
        # Esto te dirá en el log exactamente por qué te rebota (403, 401, etc.)
        print(f"Error API: Código {r.status_code} en URL {url}")
    except Exception as e:
        print(f"Error de conexión: {e}")
    return None

def manejar_datos():
    ahora = datetime.now()
    timestamp = ahora.strftime('%Y-%m-%d %H:%M')
    
    # 1. Limpieza al cierre (21hs UTC / 18hs ARG)
    if ahora.hour >= 21:
        if os.path.exists(CSV_FILE): os.remove(CSV_FILE)
        return

    # 2. Captura de Renta Fija (AL30 ARS y USD)
    datos = []
    rf_data = obtener_datos_mae(URL_RENTA_FIJA)
    
    if rf_data and isinstance(rf_data, list):
        for item in rf_data:
            ticker = item.get('ticker')
            moneda = item.get('monedaEscrituracion')
            precio = item.get('precioUltimo')
            
            if ticker == 'AL30' and precio:
                if moneda == 'ARS':
                    datos.append([timestamp, 'AL30_ARS', float(precio)])
                elif moneda == 'USD':
                    datos.append([timestamp, 'AL30_USD', float(precio)])

    # 3. Guardar en CSV
    if datos:
        df_nuevos = pd.DataFrame(datos, columns=['timestamp', 'activo', 'valor'])
        df_nuevos.to_csv(CSV_FILE, mode='a', header=not os.path.exists(CSV_FILE), index=False)
        print(f"Datos reales guardados: {len(datos)} registros.")
    else:
        # Si falla la API, no guardamos nada (evitamos el punto de prueba azul)
        print("No se recibieron datos reales en esta vuelta.")

def generar_y_enviar_reporte():
    if not os.path.exists(CSV_FILE) or os.stat(CSV_FILE).st_size == 0:
        return

    df = pd.read_csv(CSV_FILE)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # --- GRÁFICO PROFESIONAL DOBLE EJE ---
    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx() # Segundo eje para dólares

    # Línea Amarilla (Pesos)
    df_ars = df[df['activo'] == 'AL30_ARS']
    if not df_ars.empty:
        ax1.plot(df_ars['timestamp'], df_ars['valor'], color='gold', label='AL30 Pesos ($)', marker='o', linewidth=2)
    
    # Línea Verde (Dólares)
    df_usd = df[df['activo'] == 'AL30_USD']
    if not df_usd.empty:
        ax2.plot(df_usd['timestamp'], df_usd['valor'], color='green', label='AL30 USD (u$s)', marker='s', linewidth=2)

    # Estética del Gráfico
    ax1.set_ylabel('Precio Pesos ($)', color='orange', fontweight='bold')
    ax2.set_ylabel('Precio Dólares (u$s)', color='green', fontweight='bold')
    plt.title(f'Monitor AL30 Multimoneda - {datetime.now().strftime("%H:%M")}', fontsize=12)
    ax1.grid(True, alpha=0.3)
    
    # Combinar leyendas
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc='upper left')

    plt.tight_layout()
    plt.savefig('reporte.png')
    plt.close()

    # Calcular MEP actual para el mensaje
    mep_text = ""
    if not df_ars.empty and not df_usd.empty:
        val_ars = df_ars['valor'].iloc[-1]
        val_usd = df_usd['valor'].iloc[-1]
        mep_text = f"\n💵 *Dólar MEP:* ${round(val_ars / val_usd, 2)}"

    # Enviar a Telegram
    url_tel = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open('reporte.png', 'rb') as f:
        caption = f"📈 *Actualización de Mercado*{mep_text}\n🕒 {datetime.now().strftime('%H:%M')}"
        requests.post(url_tel, data={'chat_id': CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}, files={'photo': f})

if __name__ == "__main__":
    manejar_datos()
    generar_y_enviar_reporte()
