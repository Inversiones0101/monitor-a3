import requests
import re
import os
import json
import datetime
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

# --- CONFIGURACIÓN DE ACTIVOS ---
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

def extraer_tira(url, nombre):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        patron = r'ultimo["\']?\s*:\s*["\']([\d\.]+),(\d+)["\']'
        encontrados = re.findall(patron, r.text)
        precios = [float(p[0].replace('.', '') + '.' + p[1]) for p in encontrados]
        return precios if precios else []
    except:
        return []

def generar_reporte_grafico(tiras, memoria):
    # Grupos para graficar: (Pesos, Dolares, Nombre)
    grupos = [
        ('AL30', 'AL30D', 'MEP AL30'),
        ('GD30', 'GD30D', 'MEP GD30'),
        ('GGAL', 'GGAL_US', 'MEP GGAL (ADR)')
    ]
    
    fig, axes = plt.subplots(len(grupos), 1, figsize=(12, 15), facecolor='#f0f0f0')
    plt.subplots_adjust(hspace=0.4)
    ahora_str = datetime.datetime.now().strftime('%H:%M')

    for i, (p_key, d_key, titulo) in enumerate(grupos):
        ax = axes[i]
        t_p, t_d = tiras.get(p_key, []), tiras.get(d_key, [])
        
        if len(t_p) > 0 and len(t_d) > 0:
            # Sincronizar longitudes mínimas para evitar errores de cálculo
            min_len = min(len(t_p), len(t_d))
            mep_tira = [t_p[j] / (t_d[j] if t_d[j] != 0 else 1) for j in range(min_len)]
            
            # Si es GGAL US, ajustar por ratio (1 ADR = 10 Locales aprox, verificar ratio actual)
            if p_key == "GGAL": mep_tira = [x * 10 for x in mep_tira]

            ref_cierre = memoria.get(f"cierre_{titulo}", mep_tira[0])
            
            # Eje MEP (Área Roja Suave)
            ax.fill_between(range(len(mep_tira)), mep_tira, ref_cierre, color='red', alpha=0.15, label='Variación MEP')
            ax.axhline(y=ref_cierre, color='black', linestyle='--', alpha=0.5, label=f'Cierre: {ref_cierre:.2f}')
            ax.plot(mep_tira, color='red', linewidth=1.5, label=f'MEP Implícito: {mep_tira[-1]:.2f}')
            
            # Ejes secundarios para Pesos y Dólares
            ax_p = ax.twinx()
            ax_p.plot(t_p[-min_len:], color='orange', alpha=0.6, label=f'{p_key} ($)')
            
            ax.set_title(f"{titulo} | Ref: {ref_cierre:.2f} | Actual: {mep_tira[-1]:.2f}", fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend(loc='upper left', fontsize='small')

    plt.suptitle(f"MONITOR COLMENA - Reporte {ahora_str}\nMercado Argentino Intradiario", fontsize=16)
    path_img = "monitor_reporte.png"
    plt.savefig(path_img, bbox_inches='tight')
    plt.close()
    return path_img

def enviar_telegram(imagen_path, tiras):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if not token or not chat_id: return

    # Construir visor de precios (texto)
    caption = "📊 *VISOR DE PRECIOS*\n"
    for k, v in tiras.items():
        if v: caption += f"• {k}: ${v[-1]:,.2f}\n"
    
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    with open(imagen_path, 'rb') as photo:
        requests.post(url, data={'chat_id': chat_id, 'caption': caption, 'parse_mode': 'Markdown'}, files={'photo': photo})

if __name__ == "__main__":
    print("--- INICIANDO COLMENA MONITOR V4.2 ---")
    memoria = obtener_memoria()
    tiras_capturadas = {}
    
    for nombre, url in ACTIVOS.items():
        print(f"Scrapeando {nombre}...")
        tiras_capturadas[nombre] = extraer_tira(url, nombre)
    
    # Generar y enviar si hay datos
    if any(tiras_capturadas.values()):
        img = generar_reporte_grafico(tiras_capturadas, memoria)
        enviar_telegram(img, tiras_capturadas)
        
        # Lógica de guardado de cierre (17:00 ART / 20:00 UTC)
        ahora = datetime.datetime.now()
        if ahora.hour == 17 or ahora.hour == 20:
            nuevos_cierres = {}
            if tiras_capturadas['AL30'] and tiras_capturadas['AL30D']:
                nuevos_cierres["cierre_MEP AL30"] = tiras_capturadas['AL30'][-1] / tiras_capturadas['AL30D'][-1]
            if tiras_capturadas['GD30'] and tiras_capturadas['GD30D']:
                nuevos_cierres["cierre_MEP GD30"] = tiras_capturadas['GD30'][-1] / tiras_capturadas['GD30D'][-1]
            
            with open('referencia_cierre.json', 'w') as f:
                json.dump(nuevos_cierres, f)
            print("✅ Memoria de cierre actualizada.")
    else:
        print("❌ No se obtuvieron datos suficientes.")
