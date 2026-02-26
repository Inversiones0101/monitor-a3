import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os

# --- CONFIGURACIÓN ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
MAE_KEY = os.getenv('MAE_API_KEY') # Nueva llave
CSV_FILE = 'datos_dia.csv'
URL_CAUCIONES = "https://marketdata.mae.com.ar/api/v1/mercado/cotizaciones/cauciones"
URL_RENTA_FIJA = "https://marketdata.mae.com.ar/api/v1/mercado/cotizaciones/rentafija"

def obtener_precio(url, ticker_buscado, campo_valor):
    try:
        # Agregamos la API Key en el encabezado
        headers = {'X-API-KEY': MAE_KEY} if MAE_KEY else {}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        for item in data:
            if item.get('ticker') == ticker_buscado:
                return float(item.get(campo_valor, 0))
    except Exception as e:
        print(f"Error capturando {ticker_buscado}: {e}")
    return None

def manejar_datos():
    ahora = datetime.now()
    hora_actual = ahora.hour
    timestamp = ahora.strftime('%Y-%m-%d %H:%M')

    # 1. Si son las 18hs o más, limpiamos el archivo para mañana
    if hora_actual >= 18:
        df_vacio = pd.DataFrame(columns=['timestamp', 'activo', 'valor'])
        df_vacio.to_csv(CSV_FILE, index=False)
        print("Cierre de mercado: Archivo limpiado para mañana.")
        return

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

# Ejecución
manejar_datos()
# Aquí podrías poner una condición para que solo envíe el gráfico cada 1 hora
generar_y_enviar_reporte()
