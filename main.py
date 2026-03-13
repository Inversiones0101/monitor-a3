import requests
import time
import pandas as pd
import matplotlib.pyplot as plt
import os

# 1. Configuración vía Variables de Entorno (GitHub Secrets)
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
URL_BONDS = "https://data912.com/live/arg_bonds"
CSV_FILE = "prueba_cierre_al30.csv"

def get_data():
    try:
        # Agregamos un timeout para que el script no se cuelgue si la web tarda
        response = requests.get(URL_BONDS, timeout=10)
        data = response.json()
        
        # Buscamos AL30 y AL30D en el JSON de Data912
        al30 = next(item for item in data if item['symbol'] == 'AL30')
        al30d = next(item for item in data if item['symbol'] == 'AL30D')
        
        precio_ars = float(al30['c'])
        precio_usd = float(al30d['c'])
        mep = precio_ars / precio_usd
        # Hora local Argentina
        timestamp = time.strftime("%H:%M")
        
        return {"hora": timestamp, "al30": precio_ars, "al30d": precio_usd, "mep": mep}
    except Exception as e:
        print(f"⚠️ Error capturando datos: {e}")
        return None

def enviar_telegram(imagen_path, df_final):
    last_mep = df_final['mep'].iloc[-1]
    caption = f"📊 *Reporte Cierre de Rueda*\n\n🔹 **AL30:** ${df_final['al30'].iloc[-1]:.2f}\n🔹 **AL30D:** u$s {df_final['al30d'].iloc[-1]:.2f}\n\n💵 **Dólar MEP:** ${last_mep:.2f}"
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open(imagen_path, 'rb') as photo:
        payload = {'chat_id': CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}
        files = {'photo': photo}
        requests.post(url, data=payload, files=files)

def generar_grafico(df):
    plt.style.use('ggplot') # Estilo más limpio
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Eje 1: Precio del Bono
    ax1.set_xlabel('Hora del Mercado')
    ax1.set_ylabel('Precio AL30 (ARS)', color='tab:blue', fontweight='bold')
    ax1.plot(df['hora'], df['al30'], color='tab:blue', marker='o', label='AL30 (Pesos)')
    ax1.tick_params(axis='y', labelcolor='tab:blue')

    # Eje 2: Dólar MEP (Doble eje)
    ax2 = ax1.twinx()
    ax2.set_ylabel('Dólar MEP ($)', color='tab:green', fontweight='bold')
    ax2.plot(df['hora'], df['mep'], color='tab:green', linestyle='--', linewidth=2, label='Dólar MEP')
    ax2.tick_params(axis='y', labelcolor='tab:green')

    plt.title(f"Monitor AL30 vs MEP - Sprint de Cierre\n{time.strftime('%d/%m/%Y')}", fontsize=14)
    fig.tight_layout()
    
    path_grafico = "grafico_prueba.png"
    plt.savefig(path_grafico)
    plt.close()
    return path_grafico

# --- EJECUCIÓN PRINCIPAL ---
if __name__ == "__main__":
    puntos = []
    print(f"🚀 Iniciando captura de 20 puntos (1 por minuto)... {time.strftime('%H:%M:%S')}")

    for i in range(20):
        dato = get_data()
        if dato:
            puntos.append(dato)
            print(f"✅ Punto {i+1}/20: MEP ${dato['mep']:.2f}")
            
            # Guardamos progreso en CSV por seguridad
            pd.DataFrame(puntos).to_csv(CSV_FILE, index=False)
        
        # Esperar 60 segundos excepto en el último punto
        if i < 19:
            time.sleep(60)

    if len(puntos) > 0:
        df_final = pd.DataFrame(puntos)
        ruta_img = generar_grafico(df_final)
        enviar_telegram(ruta_img, df_final)
        print("🏁 Proceso completado y enviado a Telegram.")
    else:
        print("❌ No se pudieron recolectar datos.")
