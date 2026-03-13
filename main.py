import requests
import time
import pandas as pd
import matplotlib.pyplot as plt
import os

# Configuración (Reemplazá con tus datos de Telegram)
TOKEN = "TU_TELEGRAM_TOKEN"
CHAT_ID = "TU_CHAT_ID"
URL_BONDS = "https://data912.com/live/arg_bonds"
CSV_FILE = "prueba_cierre_al30.csv"

def get_data():
    try:
        response = requests.get(URL_BONDS)
        data = response.json()
        
        # Extraemos AL30 y AL30D
        al30 = next(item for item in data if item['symbol'] == 'AL30')
        al30d = next(item for item in data if item['symbol'] == 'AL30D')
        
        precio_ars = al30['c']
        precio_usd = al30d['c']
        mep = precio_ars / precio_usd
        timestamp = time.strftime("%H:%M:%S")
        
        return {"hora": timestamp, "al30": precio_ars, "al30d": precio_usd, "mep": mep}
    except Exception as e:
        print(f"Error capturando datos: {e}")
        return None

def enviar_grafico(df):
    plt.figure(figsize=(10, 6))
    
    # Eje para Precios
    ax1 = plt.gca()
    ax1.plot(df['hora'], df['al30'], color='blue', label='AL30 (ARS)')
    ax1.set_xlabel('Hora')
    ax1.set_ylabel('Precio ARS', color='blue')
    
    # Eje para MEP
    ax2 = ax1.twinx()
    ax2.plot(df['hora'], df['mep'], color='green', linestyle='--', label='Dólar MEP')
    ax2.set_ylabel('Dólar MEP', color='green')
    
    plt.title(f"Monitor AL30 vs MEP - Cierre de Mercado\n{time.strftime('%d/%m/%Y')}")
    plt.savefig("grafico_prueba.png")
    
    # Envío a Telegram
    with open("grafico_prueba.png", 'rb') as photo:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", 
                      data={'chat_id': CHAT_ID, 'caption': "📊 Reporte de 20 min - AL30 & MEP"}, 
                      files={'photo': photo})

# --- CICLO DE PRUEBA ---
puntos = []
print("🚀 Iniciando monitor de 20 minutos...")

while len(puntos) < 20:
    nuevo_punto = get_data()
    if nuevo_punto:
        puntos.append(nuevo_punto)
        print(f"📍 Punto {len(puntos)}/20: MEP ${nuevo_punto['mep']:.2f}")
        
        # Guardar en CSV
        df = pd.DataFrame(puntos)
        df.to_csv(CSV_FILE, index=False)
        
    time.sleep(60) # Esperar 1 minuto

print("📈 Generando y enviando gráfico...")
enviar_grafico(df)
print("✅ Prueba finalizada.")
