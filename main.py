import requests
import os
import datetime
import matplotlib.pyplot as plt

ACTIVOS_RAVA = {
    "AL30": "AL30",
    "AL30D": "AL30D",
    "GD30": "GD30",
    "GD30D": "GD30D",
    "GGAL": "GGAL",
    "GGAL_US": "GGAL_US"
}

def extraer_datos_api(ticker):
    # Intentamos entrar por la puerta de datos con credenciales de navegador
    url = f"https://www.rava.com/api/v1/instrumentos/perfil/intradia/{ticker}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.rava.com",
        "Referer": f"https://www.rava.com/perfil/{ticker}"
    }
    
    try:
        # Usamos una sesión para mantener cookies básicas
        session = requests.Session()
        r = session.get(url, headers=headers, timeout=15)
        
        if r.status_code == 200:
            data = r.json()
            precios = [float(p['ultimo']) for p in data.get('cuerpo', [])]
            print(f"DEBUG {ticker}: {len(precios)} puntos capturados.")
            return precios
        else:
            print(f"DEBUG {ticker}: Error de acceso (Status {r.status_code})")
            return []
    except Exception as e:
        print(f"Error técnico en {ticker}: {e}")
        return []

def ejecutar_colmena():
    tiras = {n: extraer_datos_api(t) for n, t in ACTIVOS_RAVA.items()}
    
    # Verificamos si logramos entrar al menos a AL30
    if len(tiras.get("AL30", [])) > 5:
        p, d = tiras["AL30"], tiras["AL30D"]
        min_l = min(len(p), len(d))
        mep = [p[i]/d[i] for i in range(min_l)]
        
        plt.figure(figsize=(10, 6))
        plt.plot(mep, color='#d62728', linewidth=2, label=f'MEP AL30: ${mep[-1]:.2f}')
        plt.fill_between(range(len(mep)), mep, mep[0], color='red', alpha=0.1)
        plt.axhline(y=mep[0], color='black', linestyle='--', alpha=0.6, label=f'Apertura: ${mep[0]:.2f}')
        
        plt.title(f"MONITOR COLMENA - {datetime.datetime.now().strftime('%H:%M')} ARG", fontweight='bold')
        plt.grid(True, alpha=0.2)
        plt.legend()
        
        img = "monitor_final.png"
        plt.savefig(img, bbox_inches='tight')
        plt.close()
        
        # Enviar a Telegram
        token = os.getenv('TELEGRAM_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        caption = f"🚀 *COLMENA INFILTRADA*\n\n💰 *AL30:* ${p[-1]:,.2f}\n💵 *AL30D:* u$s{d[-1]:,.2f}\n🎯 *MEP:* ${mep[-1]:,.2f}"
        
        url_tg = f"https://api.telegram.org/bot{token}/sendPhoto"
        with open(img, 'rb') as f:
            requests.post(url_tg, data={'chat_id': chat_id, 'caption': caption, 'parse_mode': 'Markdown'}, files={'photo': f})
        print("✅ ÉXITO: Datos enviados a Telegram.")
    else:
        print("❌ El Mamut sigue bloqueando. Necesitamos cambiar de estrategia de acceso.")

if __name__ == "__main__":
    ejecutar_colmena()
