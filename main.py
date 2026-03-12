import requests
import re
import os
import json
import datetime
import pandas as pd
import matplotlib.pyplot as plt

ACTIVOS = {
    "AL30": "https://www.rava.com/perfil/AL30",
    "AL30D": "https://www.rava.com/perfil/AL30D",
    "GD30": "https://www.rava.com/perfil/GD30",
    "GD30D": "https://www.rava.com/perfil/GD30D",
    "GGAL": "https://www.rava.com/perfil/GGAL",
    "GGAL_US": "https://www.rava.com/perfil/GGAL_US",
    "CAUCION": "https://www.rava.com/perfil/CAUCION%201D"
}

def obtener_memoria():
    if os.path.exists('referencia_cierre.json'):
        try:
            with open('referencia_cierre.json', 'r') as f:
                return json.load(f)
        except: return {}
    return {}

def extraer_tira_robusta(url, nombre):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        html = r.text
        
        # PATRÓN 1: El clásico de Rava (ultimo:"123,45")
        patrones = [
            r'ultimo["\']?\s*:\s*["\']?([\d\.]+),(\d+)["\']?',
            r'cierre["\']?\s*:\s*["\']?([\d\.]+),(\d+)["\']?',
            r'["\']?value["\']?\s*:\s*([\d\.]+)' # Plan C para otros activos
        ]
        
        precios = []
        for p in patrones:
            encontrados = re.findall(p, html)
            if encontrados:
                for e in encontrados:
                    if isinstance(e, tuple):
                        precios.append(float(e[0].replace('.', '') + '.' + e[1]))
                    else:
                        precios.append(float(e))
                if precios: break # Si encontramos con un patrón, no seguimos buscando

        print(f"DEBUG {nombre}: {len(precios)} puntos detectados.")
        return precios
    except:
        return []

def generar_grafico(tiras, memoria):
    # Usamos AL30 como ejemplo principal para el reporte
    if not tiras.get("AL30") or not tiras.get("AL30D"): return None
    
    plt.figure(figsize=(10, 6))
    p, d = tiras["AL30"], tiras["AL30D"]
    min_l = min(len(p), len(d))
    mep = [p[i]/d[i] for i in range(min_l)]
    
    ref = memoria.get("cierre_AL30", mep[0])
    plt.fill_between(range(len(mep)), mep, ref, color='red', alpha=0.2)
    plt.plot(mep, color='red', label=f'MEP AL30: {mep[-1]:.2f}')
    plt.axhline(y=ref, color='black', linestyle='--', alpha=0.5)
    
    plt.title(f"Monitor MEP - {datetime.datetime.now().strftime('%H:%M')}")
    plt.legend()
    path = "monitor.png"
    plt.savefig(path)
    plt.close()
    return path

def enviar_telegram(img, tiras):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if not img or not token: return
    
    txt = "📊 *PRECIOS ACTUALES*\n"
    for k, v in tiras.items():
        if v: txt += f"• {k}: ${v[-1]:,.2f}\n"
        
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    with open(img, 'rb') as f:
        requests.post(url, data={'chat_id': chat_id, 'caption': txt, 'parse_mode': 'Markdown'}, files={'photo': f})

if __name__ == "__main__":
    mem = obtener_memoria()
    tiras = {n: extraer_tira_robusta(u, n) for n, u in ACTIVOS.items()}
    
    img = generar_grafico(tiras, mem)
    if img:
        enviar_telegram(img, tiras)
        # Guardar cierre si es hora
        if datetime.datetime.now().hour >= 17:
            with open('referencia_cierre.json', 'w') as f:
                json.dump({"cierre_AL30": tiras["AL30"][-1]/tiras["AL30D"][-1]}, f)
