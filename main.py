import requests
import os
import json
import datetime
import matplotlib.pyplot as plt

# --- CONFIGURACIÓN DE ACTIVOS (IDs internos de Rava) ---
# Usamos los nombres que Rava usa en su sistema de datos
ACTIVOS_RAVA = {
    "AL30": "AL30",
    "AL30D": "AL30D",
    "GD30": "GD30",
    "GD30D": "GD30D",
    "GGAL": "GGAL",
    "GGAL_US": "GGAL_US"
}

def extraer_datos_directos(ticker):
    # Esta es la URL de la API que alimenta el gráfico intradiario
    url = f"https://www.rava.com/api/v1/instrumentos/perfil/intradia/{ticker}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": f"https://www.rava.com/perfil/{ticker}"
    }
    try:
        r = requests.get(url, headers=headers, timeout=15)
        data = r.json()
        # Extraemos solo los precios de la serie de tiempo
        precios = [float(punto['ultimo']) for punto in data.get('cuerpo', [])]
        print(f"DEBUG {ticker}: {len(precios)} puntos obtenidos de la API.")
        return precios
    except Exception as e:
        print(f"Error en API para {ticker}: {e}")
        return []

def generar_y_enviar():
    tiras = {nombre: extraer_datos_directos(ticker) for nombre, ticker in ACTIVOS_RAVA.items()}
    
    # Verificamos si tenemos los datos base para el MEP
    if len(tiras.get("AL30", [])) > 0 and len(tiras.get("AL30D", [])) > 0:
        p, d = tiras["AL30"], tiras["AL30D"]
        min_l = min(len(p), len(d))
        mep = [p[i]/d[i] for i in range(min_l)]
        
        # Crear Gráfico
        plt.figure(figsize=(10, 6))
        plt.plot(mep, color='red', linewidth=2, label=f'MEP AL30 Actual: {mep[-1]:.2f}')
        plt.fill_between(range(len(mep)), mep, mep[0], color='red', alpha=0.1)
        plt.axhline(y=mep[0], color='black', linestyle='--', label='Apertura')
        plt.title(f"Monitor Colmena - {datetime.datetime.now().strftime('%H:%M')}")
        plt.legend()
        plt.grid(True, alpha=0.2)
        
        img_path = "monitor.png"
        plt.savefig(img_path)
        plt.close()
        
        # Enviar a Telegram
        token = os.getenv('TELEGRAM_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        caption = f"📊 *COLMENA UPDATE*\n• AL30: ${p[-1]:,.2f}\n• AL30D: u$s{d[-1]:,.2f}\n• *MEP: ${mep[-1]:,.2f}*"
        
        url_tg = f"https://api.telegram.org/bot{token}/sendPhoto"
        with open(img_path, 'rb') as f:
            requests.post(url_tg, data={'chat_id': chat_id, 'caption': caption, 'parse_mode': 'Markdown'}, files={'photo': f})
        print("✅ Reporte enviado a Telegram.")
    else:
        print("❌ Datos insuficientes en la API para generar el reporte.")

if __name__ == "__main__":
    generar_y_enviar()
