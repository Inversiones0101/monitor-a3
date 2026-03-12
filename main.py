import requests
import os
import datetime
import pandas as pd
import matplotlib.pyplot as plt

# Diccionario de activos en Google Finance
# Formato: "BCBA:TICKER" para Argentina
ACTIVOS = {
    "AL30": "BCBA:AL30",
    "AL30D": "BCBA:AL30D",
    "GD30": "BCBA:GD30",
    "GD30D": "BCBA:GD30D",
    "GGAL": "BCBA:GGAL"
}

def obtener_precio_google(ticker):
    url = f"https://www.google.com/finance/quote/{ticker}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        # Buscamos el precio en el meta-tag de Google
        patron = r'data-last-price="([\d\.]+)"'
        import re
        match = re.search(patron, r.text)
        if match:
            precio = float(match.group(1))
            print(f"✅ {ticker}: ${precio}")
            return precio
        return None
    except:
        return None

def ejecutar_colmena():
    precios = {n: obtener_precio_google(t) for n, t in ACTIVOS.items()}
    
    # Si tenemos AL30 y AL30D, calculamos MEP
    if precios["AL30"] and precios["AL30D"]:
        mep_actual = precios["AL30"] / precios["AL30D"]
        
        # Guardamos en un CSV para empezar a crear el historial de la tira
        df_nuevo = pd.DataFrame([{
            "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "mep": mep_actual
        }])
        
        if os.path.exists("datos_bono.csv"):
            df_hist = pd.read_csv("datos_bono.csv")
            df_final = pd.concat([df_hist, df_nuevo]).tail(50) # Mantenemos los últimos 50 puntos
        else:
            df_final = df_nuevo
            
        df_final.to_csv("datos_bono.csv", index=False)

        # Generar Gráfico
        plt.figure(figsize=(10, 5))
        plt.plot(df_final["mep"].values, color='red', marker='o', label=f'MEP AL30: ${mep_actual:.2f}')
        plt.fill_between(range(len(df_final)), df_final["mep"], df_final["mep"].iloc[0], color='red', alpha=0.1)
        plt.title(f"Monitor Colmena (Google Engine) - {df_nuevo['fecha'].iloc[0]}")
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        img = "monitor.png"
        plt.savefig(img)
        plt.close()

        # Enviar a Telegram
        token = os.getenv('TELEGRAM_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        caption = f"🐝 *COLMENA V5 (Google Engine)*\n\n💰 *AL30:* ${precios['AL30']}\n💵 *AL30D:* u$s{precios['AL30D']}\n🎯 *MEP:* ${mep_actual:.2f}"
        
        url_tg = f"https://api.telegram.org/bot{token}/sendPhoto"
        with open(img, 'rb') as f:
            requests.post(url_tg, data={'chat_id': chat_id, 'caption': caption, 'parse_mode': 'Markdown'}, files={'photo': f})
        print("🚀 Reporte enviado con éxito.")

if __name__ == "__main__":
    ejecutar_colmena()
