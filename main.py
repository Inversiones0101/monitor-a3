import requests
import re
import os
import datetime
import pandas as pd
import matplotlib.pyplot as plt

ACTIVOS = {
    "AL30": "https://www.rava.com/perfil/AL30",
    "AL30D": "https://www.rava.com/perfil/AL30D"
}

def hackear_precio_rava(url, nombre):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    try:
        # 1. Engañamos al Mamut simulando una visita real desde una Mac
        r = requests.get(url, headers=headers, timeout=20)
        html = r.text
        
        # 2. Búsqueda por patrón numérico financiero (ej: 86.250,00 o 34,50)
        # Este patrón busca números con el formato específico de Rava
        patrones = [
            r'(\d{1,3}(?:\.\d{3})*,\d{2})', # Formato con punto en miles y coma decimal
            r'last_price["\']?:\s*["\']?([\d\.]+)["\']?' # Respaldo por si hay JSON oculto
        ]
        
        candidatos = []
        for p in patrones:
            encontrados = re.findall(p, html)
            for e in encontrados:
                # Limpiamos el formato argentino a float puro
                val = float(e.replace('.', '').replace(',', '.'))
                if val > 10: # Filtro básico para evitar capturar porcentajes de variación
                    candidatos.append(val)
        
        if candidatos:
            # El precio actual suele ser el primer número grande que aparece en el perfil
            precio = candidatos[0]
            print(f"🎯 {nombre} capturado por fuerza bruta: {precio}")
            return precio
            
        print(f"❌ {nombre}: El Mamut escondió el dato bajo tierra.")
        return None
    except Exception as e:
        print(f"⚠️ Error en hack de {nombre}: {e}")
        return None

def mision_colmena():
    precios = {n: hackear_precio_rava(u, n) for n, u in ACTIVOS.items()}
    
    if precios["AL30"] and precios["AL30D"]:
        mep = precios["AL30"] / precios["AL30D"]
        ahora = datetime.datetime.now().strftime("%H:%M")
        
        # Actualizar CSV de la Colmena
        nuevo = pd.DataFrame([{"hora": ahora, "mep": mep}])
        df = pd.concat([pd.read_csv("datos_bono.csv"), nuevo]).tail(30) if os.path.exists("datos_bono.csv") else nuevo
        df.to_csv("datos_bono.csv", index=False)

        # Diseño "Black Mode" de tu tablero
        plt.style.use('dark_background')
        plt.figure(figsize=(10, 5))
        plt.fill_between(range(len(df)), df["mep"], df["mep"].iloc[0], color='#ff0000', alpha=0.2)
        plt.plot(df["mep"].values, color='#ff4444', linewidth=2, marker='o')
        plt.title(f"MEP AL30: ${mep:.2f} | {ahora} ARG", color='white', size=14)
        plt.grid(alpha=0.1)
        
        img = "monitor_hack.png"
        plt.savefig(img, bbox_inches='tight')
        plt.close()

        # Envío a Telegram
        token, chat = os.getenv('TELEGRAM_TOKEN'), os.getenv('TELEGRAM_CHAT_ID')
        caption = f"🚨 *MAMUT HACKEADO*\n\n📈 *AL30:* ${precios['AL30']:,.2f}\n📉 *AL30D:* u$s{precios['AL30D']:,.2f}\n🔥 *MEP:* ${mep:.2f}"
        requests.post(f"https://api.telegram.org/bot{token}/sendPhoto", 
                      data={'chat_id': chat, 'caption': caption, 'parse_mode': 'Markdown'}, 
                      files={'photo': open(img, 'rb')})
        print("✅ Colmena en el aire.")

if __name__ == "__main__":
    mision_colmena()
