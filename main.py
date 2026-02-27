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

def obtener_precio(url, ticker_buscado, campo_valor):
    """Captura datos de la API del MAE usando la API KEY."""
    try:
        if not MAE_KEY:
            print("Error: MAE_API_KEY no configurada en Secrets")
            return None

        headers = {
            'X-API-KEY': MAE_KEY,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"Error API MAE para {ticker_buscado}: Código {response.status_code}")
            return None
            
        data = response.json()
        if isinstance(data, list):
            for item in data:
                if item.get('ticker') == ticker_buscado:
                    valor = item.get(campo_valor)
                    return float(valor) if valor is not None else None
    except Exception as e:
        print(f"Error capturando {ticker_buscado}: {e}")
    return None

def manejar_datos():
    """Gestiona la captura de precios y el guardado en el archivo CSV."""
    ahora = datetime.now()
    hora_actual_utc = ahora.hour
    timestamp = ahora.strftime('%Y-%m-%d %H:%M')

    # 1. Limpieza automática al cierre (21hs UTC = 18hs Argentina)
    if hora_actual_utc >= 21: 
        if os.path.exists(CSV_FILE):
            os.remove(CSV_FILE)
            print("Cierre de mercado: Archivo eliminado para limpieza.")
        return

    # 2. Captura de datos reales
    datos = []
    
    # Caución 1D
    tasa = obtener_precio(URL_CAUCIONES, "CAARS", "ultimaTasa")
    if tasa: 
        datos.append([timestamp, 'Caucion_1D', tasa])
    
    # Bonos AL30 y GD30
    for bono in ["AL30", "GD30"]:
        precio = obtener_precio(URL_RENTA_FIJA, bono, "precioUltimo")
        if precio: 
            datos.append([timestamp, bono, precio])

    # 3. Guardar en CSV si hay datos nuevos
    if datos:
        df_nuevos = pd.DataFrame(datos, columns=['timestamp', 'activo', 'valor'])
        df_nuevos.to_csv(CSV_FILE, mode='a', header=not os.path.exists(CSV_FILE), index=False)
        print(f"Datos guardados a las {timestamp}")
    else:
        print("No se obtuvieron datos de la API (Mercado cerrado o sin operaciones).")

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
