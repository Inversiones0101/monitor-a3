import requests
from bs4 import BeautifulSoup
import os
import datetime
import pandas as pd
import matplotlib.pyplot as plt

ACTIVOS = {
    "AL30": "https://www.rava.com/perfil/AL30",
    "AL30D": "https://www.rava.com/perfil/AL30D",
    "GD30": "https://www.rava.com/perfil/GD30",
    "GD30D": "https://www.rava.com/perfil/GD30D"
}

def infiltrar_rava(url, nombre):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "es-ES,es;q=0.9"
    }
    try:
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Buscamos el precio en la clase específica que usa Rava para el "Último"
        # Si cambiaron la API, el dato sigue estando en el HTML para el usuario
        elemento = soup.find("span", {"class": "ultimo"}) or soup.find("div", {"class": "precio-actual"})
        
        if elemento:
            # Limpiamos el texto: "34.500,00" -> 34500.00
            texto = elemento.text.strip().replace('.', '').replace(',', '.')
            precio = float(''.join(c for c in texto if c.isdigit() or c == '.'))
            print(f"✅ {nombre} capturado: {precio}")
            return precio
        
        print(f"⚠️ {nombre}: No se encontró el tag. El Mamut cambió el HTML.")
        return None
    except Exception as e:
        print(f"❌ Error en {nombre}: {e}")
        return None

def ejecutar_mision():
    precios = {n: infiltrar_rava(u, n) for n, u in ACTIVOS.items()}
    
    if precios["AL30"] and precios["AL30D"]:
        mep = precios["AL30"] / precios["AL30D"]
        ahora = datetime.datetime.now().strftime("%H:%M")
        
        # --- Lógica de Gráfico de Área (Tu diseño original) ---
        # Guardamos el punto para construir la tira
        nuevo_punto = pd.DataFrame([{"hora": ahora, "mep": mep}])
        if os.path.exists("datos_bono.csv"):
            df = pd.concat([pd.read_csv("datos_bono.csv"), nuevo_punto]).tail(40)
        else:
            df = nuevo_punto
        df.to_csv("datos_bono.csv", index=False)

        plt.figure(figsize=(10, 6), facecolor='#1a1a1a')
        ax = plt.gca()
        ax.set_facecolor('#1a1a1a')
        
        # Dibujamos el área roja de tu diseño
        plt.fill_between(range(len(df)), df["mep"], df["mep"].iloc[0], color='red', alpha=0.3)
        plt.plot(df["mep"].values, color='#ff4d4d', linewidth=3, marker='o', markersize=4)
        
        plt.title(f"MONITOR COLMENA - MEP AL30: ${mep:.2f}", color='white', fontweight='bold')
        plt.xticks(range(len(df)), df["hora"], rotation=45, color='gray')
        plt.yticks(color='gray')
        plt.grid(alpha=0.1, color='white')
        
        img = "monitor.png"
        plt.savefig(img, bbox_inches='tight', facecolor='#1a1a1a')
        plt.close()

        # Enviar a Telegram
        token = os.getenv('TELEGRAM_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        url_tg = f"https://api.telegram.org/bot{token}/sendPhoto"
        caption = f"🎯 *INFILTRACIÓN EXITOSA*\n\n💰 *AL30:* ${precios['AL30']:,.2f}\n💵 *AL30D:* u$s{precios['AL30D']:,.2f}\n🔥 *MEP:* ${mep:.2f}"
        
        with open(img, 'rb') as f:
            requests.post(url_tg, data={'chat_id': chat_id, 'caption': caption, 'parse_mode': 'Markdown'}, files={'photo': f})
        print("🚀 Reporte enviado.")

if __name__ == "__main__":
    ejecutar_mision()
