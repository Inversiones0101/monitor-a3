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
    try:
        # IMPORTANTE: Asegúrate de que MAE_KEY no esté vacío
        if not MAE_KEY:
            print("Error: MAE_API_KEY no configurada en Secrets")
            return None

        headers = {
            'X-API-KEY': MAE_KEY,
            'User-Agent': 'Mozilla/5.0' # Algunos servidores bloquean si no hay User-Agent
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"Error API MAE para {ticker_buscado}: Código {response.status_code}")
            # Si el código es 401 o 403, la API KEY está mal o expiró
            return None
            
        data = response.json()
        # Verificamos que 'data' sea una lista
        if isinstance(data, list):
            for item in data:
                if item.get('ticker') == ticker_buscado:
                    valor = item.get(campo_valor)
                    return float(valor) if valor is not None else None
    except Exception as e:
        print(f"Error capturando {ticker_buscado}: {e}")
    return None

def manejar_datos():
    ahora = datetime.now()
    hora_actual = ahora.hour
    timestamp = ahora.strftime('%Y-%m-%d %H:%M')

    # 1. Si son las 18hs o más, limpiamos el archivo para mañana
    #if hora_actual >= 18:
    #    df_vacio = pd.DataFrame(columns=['timestamp', 'activo', 'valor'])
    #   df_vacio.to_csv(CSV_FILE, index=False)
    #    print("Cierre de mercado: Archivo limpiado para mañana.")
    #    return

    # 2. Captura de datos
    datos = []
    # Caución 1D (usamos 'ultimaTasa')
    tasa = obtener_precio(URL_CAUCIONES, "CAARS", "ultimaTasa")
    if tasa: datos.append([timestamp, 'Caucion_1D', tasa])
    
    # Bonos (usamos 'precioUltimo')
    for bono in ["AL30", "GD30"]:
        precio = obtener_precio(URL_RENTA_FIJA, bono, "precioUltimo")
        if precio: datos.append([timestamp, bono, precio])

    # 3. Guardar en CSV
    if datos:
        df_nuevos = pd.DataFrame(datos, columns=['timestamp', 'activo', 'valor'])
        df_nuevos.to_csv(CSV_FILE, mode='a', header=not os.path.exists(CSV_FILE), index=False)
        print(f"Datos guardados a las {timestamp}")

def generar_y_enviar_reporte():
    if not os.path.exists(CSV_FILE) or os.stat(CSV_FILE).st_size == 0:
        return

    df = pd.read_csv(CSV_FILE)
    if df.empty: return
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    activos = df['activo'].unique()
    
    fig, axes = plt.subplots(len(activos), 1, figsize=(10, 5 * len(activos)))
    if len(activos) == 1: axes = [axes]

    for i, activo in enumerate(activos):
        sub_df = df[df['activo'] == activo]
        axes[i].plot(sub_df['timestamp'], sub_df['valor'], marker='s', color='green' if '30' in activo else 'blue')
        axes[i].set_title(f'Evolución Intradiaria: {activo}')
        axes[i].grid(True)

    plt.tight_layout()
    plt.savefig('reporte.png')
    
    # Enviar a Telegram
    url_tel = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open('reporte.png', 'rb') as f:
        requests.post(url_tel, data={'chat_id': CHAT_ID, 'caption': f'📈 Monitor A3 - Actualizado {datetime.now().strftime("%H:%M")}'}, files={'photo': f})

# Enviar a Telegram con verificación
    url_tel = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open('reporte.png', 'rb') as f:
        r = requests.post(url_tel, data={'chat_id': CHAT_ID, 'caption': f'📈 Monitor A3 - {datetime.now().strftime("%H:%M")}'}, files={'photo': f})
        if r.status_code != 200:
            # Si la foto falla, intentamos mandar un texto para saber que el bot está vivo
            url_text = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            requests.post(url_text, data={'chat_id': CHAT_ID, 'text': f"Error enviando imagen: {r.text}"})
            

# Al final del archivo, forzamos el reporte aunque falle la captura de hoy
manejar_datos()
print("Intentando generar reporte con datos acumulados...") # Para ver en el log
generar_y_enviar_reporte()
