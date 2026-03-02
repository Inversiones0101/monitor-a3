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
URL_CAUCIONES = "https://marketdata.mae.com.ar/api/v1/mercado/cotizaciones/cauciones"
URL_RENTA_FIJA = "https://marketdata.mae.com.ar/api/v1/mercado/cotizaciones/rentafija"

def obtener_precio(url, ticker_buscado, moneda_buscada):
    """Captura datos filtrando por Ticker y Moneda (ARS o USD)."""
    try:
        if not MAE_KEY: return None
        headers = {'X-API-KEY': MAE_KEY, 'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            for item in data:
                # Filtramos por Ticker y por Moneda
                if item.get('ticker') == ticker_buscado and item.get('monedaEscrituracion') == moneda_buscada:
                    valor = item.get('precioUltimo')
                    return float(valor) if valor is not None else None
    except Exception as e:
        print(f"Error en API para {ticker_buscado} {moneda_buscada}: {e}")
    return None

def manejar_datos():
    ahora = datetime.now()
    timestamp = ahora.strftime('%Y-%m-%d %H:%M')

    # 1. Captura de datos específicos
    datos = []
    
    # AL30 en Pesos
    p_ars = obtener_precio(URL_RENTA_FIJA, "AL30", "ARS")
    if p_ars: datos.append([timestamp, 'AL30_ARS', p_ars])
    
    # AL30 en Dólares
    p_usd = obtener_precio(URL_RENTA_FIJA, "AL30", "USD")
    if p_usd: datos.append([timestamp, 'AL30_USD', p_usd])
    
    # Caución
    tasa = obtener_precio(URL_CAUCIONES, "CAARS", "ARS") # Las cauciones suelen ser ARS
    if tasa: datos.append([timestamp, 'Caucion', tasa])

    # 2. Guardar en CSV
    if datos:
        df_nuevos = pd.DataFrame(datos, columns=['timestamp', 'activo', 'valor'])
        df_nuevos.to_csv(CSV_FILE, mode='a', header=not os.path.exists(CSV_FILE), index=False)
        print(f"Datos guardados: {datos}")
    else:
        print("API MAE no devolvió datos para los filtros seleccionados.")
        
def generar_y_enviar_reporte():
    """Genera el gráfico y lo envía al grupo de Telegram."""
    if not os.path.exists(CSV_FILE) or os.stat(CSV_FILE).st_size == 0:
        print("No hay datos suficientes para graficar.")
        return

    df = pd.read_csv(CSV_FILE)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    activos = df['activo'].unique()
    
    # Configuramos el diseño del gráfico
    fig, axes = plt.subplots(len(activos), 1, figsize=(10, 5 * len(activos)))
    if len(activos) == 1: axes = [axes]

    for i, activo in enumerate(activos):
        sub_df = df[df['activo'] == activo]
        color = 'green' if '30' in activo else 'blue'
        
        axes[i].plot(sub_df['timestamp'], sub_df['valor'], marker='o', linestyle='-', color=color, linewidth=2)
        axes[i].set_title(f'Evolución Intradiaria: {activo}', fontsize=14, fontweight='bold', pad=15)
        axes[i].grid(True, linestyle='--', alpha=0.6)
        axes[i].set_ylabel('Precio / Tasa')
        axes[i].tick_params(axis='x', rotation=30)

    plt.tight_layout()
    plt.savefig('reporte.png', dpi=100)
    plt.close()
    
    # Enviar a Telegram con verificación
    url_tel = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    try:
        with open('reporte.png', 'rb') as f:
            caption_text = f'📈 Monitor A3 - {datetime.now().strftime("%d/%m %H:%M")}'
            payload = {'chat_id': CHAT_ID, 'caption': caption_text}
            files = {'photo': f}
            r = requests.post(url_tel, data=payload, files=files, timeout=25)
            
            if r.status_code == 200:
                print("¡Reporte enviado exitosamente!")
            else:
                print(f"Error de Telegram: {r.status_code} - {r.text}")
                # Reintento de emergencia solo con texto si falla la imagen
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                             data={'chat_id': CHAT_ID, 'text': f"⚠️ Error enviando imagen: {r.text}"})
    except Exception as e:
        print(f"Error crítico en el proceso de envío: {e}")

# --- INICIO DEL SCRIPT ---
if __name__ == "__main__":
    manejar_datos()
    generar_y_enviar_reporte()
