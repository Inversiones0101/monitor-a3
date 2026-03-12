import requests
import os
import datetime
import pandas as pd
import matplotlib.pyplot as plt

# La URL mágica que encontraste en Network
API_URL = "https://rofex.primary.ventures/api/v2/series/securities/rx_DDF_DLR_MAR26"

def extraer_datos_rofex():
    # Usamos los headers que me pasaste en el cURL
    params = {
        "resolution": "5", # Intervalo de 5 minutos como en la web
        "from": (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%dT00:00:00.000Z"),
        "to": datetime.datetime.now().strftime("%Y-%m-%dT23:59:59.000Z")
    }
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "referer": "https://rofex.primary.ventures/security/rx_DDF_DLR_MAR26?interval=5"
    }
    
    try:
        r = requests.get(API_URL, params=params, headers=headers, timeout=20)
        data = r.json()
        
        # Extraemos los precios de cierre (c) y el tiempo (t)
        # La API de Rofex devuelve listas bajo 'c', 'h', 'l', 'o', 't'
        precios = data.get('c', [])
        tiempos = data.get('t', [])
        
        if not precios:
            print("❌ No hay datos en la respuesta de la API.")
            return None
            
        # Convertimos UNIX timestamp a hora legible
        horas = [datetime.datetime.fromtimestamp(t).strftime('%H:%M') for t in tiempos]
        
        df = pd.DataFrame({"hora": horas, "precio": precios})
        print(f"✅ Capturados {len(df)} puntos de DLR MAR26")
        return df
    except Exception as e:
        print(f"⚠️ Error al conectar con Rofex: {e}")
        return None

def ejecutar_mision():
    df = extraer_datos_rofex()
    if df is not None and not df.empty:
        # Guardar en CSV
        df.to_csv("datos_futuro.csv", index=False)
        
        ultimo_precio = df['precio'].iloc[-1]
        apertura = df['precio'].iloc[0]

        # Graficador Profesional (Estilo el que viste en la web)
        plt.style.use('dark_background')
        plt.figure(figsize=(10, 5))
        plt.fill_between(range(len(df)), df["precio"], apertura, color='#00ff00', alpha=0.15)
        plt.plot(df["precio"].values, color='#00ff00', linewidth=2, label=f'DLR MAR26: ${ultimo_precio:,.2f}')
        plt.axhline(y=apertura, color='white', linestyle='--', alpha=0.3, label='Apertura')
        
        plt.title(f"MATBA ROFEX - DLR/MAR26 - ${ultimo_precio:,.2f}", color='#00ff00', fontweight='bold')
        plt.grid(alpha=0.1)
        plt.legend()
        
        img = "rofex_monitor.png"
        plt.savefig(img, bbox_inches='tight')
        plt.close()

        # Enviar a Telegram
        token = os.getenv('TELEGRAM_TOKEN')
        chat = os.getenv('TELEGRAM_CHAT_ID')
        caption = f"📈 *DÓLAR FUTURO MAR/26*\n\n💎 *Precio:* ${ultimo_precio:,.2f}\n⏱ *Hora:* {df['hora'].iloc[-1]}\n📊 *Variación Rueda:* {((ultimo_precio/apertura)-1)*100:.2f}%"
        
        with open(img, 'rb') as f:
            requests.post(f"https://api.telegram.org/bot{token}/sendPhoto", 
                          data={'chat_id': chat, 'caption': caption, 'parse_mode': 'Markdown'}, files={'photo': f})
        print("🚀 Monitor enviado con éxito.")

if __name__ == "__main__":
    ejecutar_mision()
