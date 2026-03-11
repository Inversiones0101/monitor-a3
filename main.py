import requests
import re
import os
import json
import datetime
import pandas as pd
import matplotlib.pyplot as plt

# Configuración de Activos y Rangos (Ajustables según referencia)
ACTIVOS = {
    "AL30": {"url": "https://www.rava.com/perfil/AL30", "color": "yellow", "label": "AL30 ($)"},
    "AL30D": {"url": "https://www.rava.com/perfil/AL30D", "color": "green", "label": "AL30D (u$d)"},
    "GGAL": {"url": "https://www.rava.com/perfil/GGAL", "color": "yellow", "label": "GGAL ($)"},
    "GGAL_US": {"url": "https://www.rava.com/perfil/GGAL_US", "color": "green", "label": "GGAL (u$d)"}
}

def obtener_referencia():
    if os.path.exists('referencia_cierre.json'):
        with open('referencia_cierre.json', 'r') as f:
            return json.load(f)
    return {}

def guardar_referencia(datos_cierre):
    with open('referencia_cierre.json', 'w') as f:
        json.dump(datos_cierre, f)
    print("💾 Referencia de cierre guardada para mañana.")

def extraer_tira_profesional(url, nombre):
    try:
        response = requests.get(url, timeout=15)
        # Buscamos el array de datos del gráfico en el HTML
        patron = r'ultimo["\']?\s*:\s*["\']([\d\.]+),(\d+)["\']'
        encontrados = re.findall(patron, response.text)
        
        precios = []
        for p in encontrados:
            valor = float(p[0].replace('.', '') + '.' + p[1])
            precios.append(valor)
        
        return precios
    except Exception as e:
        print(f"Error en {nombre}: {e}")
        return []

def generar_dashboard_mep(tiras, referencia):
    # Lógica para crear el gráfico con área roja central (MEP) 
    # y líneas de Pesos/Dólares como tu Paint
    plt.figure(figsize=(12, 6))
    
    # Ejemplo AL30/AL30D
    if tiras['AL30'] and tiras['AL30D']:
        mep_hoy = [p/d for p, d in zip(tiras['AL30'], tiras['AL30D'])]
        mep_ref = referencia.get('MEP_AL30', mep_hoy[0])
        
        plt.fill_between(range(len(mep_hoy)), mep_hoy, mep_ref, color='red', alpha=0.3, label='Variación MEP')
        plt.plot(mep_hoy, color='darkred', linewidth=1)
        
    plt.title(f"Monitor Financiero - {datetime.datetime.now().strftime('%H:%M')}")
    plt.legend()
    plt.savefig("monitor_output.png")
    plt.close()

def enviar_telegram(imagen_path):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if not token or not chat_id: return
    
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    with open(imagen_path, 'rb') as photo:
        requests.post(url, data={'chat_id': chat_id}, files={'photo': photo})

if __name__ == "__main__":
    ref = obtener_referencia()
    tiras_dia = {}
    
    for nombre, info in ACTIVOS.items():
        tiras_dia[nombre] = extraer_tira_profesional(info['url'], nombre)
    
    generar_dashboard_mep(tiras_dia, ref)
    enviar_telegram("monitor_output.png")
    
    # Si son las 17:00, guardamos para mañana
    ahora = datetime.datetime.now()
    if ahora.hour == 17:
        cierre = {
            "MEP_AL30": tiras_dia['AL30'][-1] / tiras_dia['AL30D'][-1] if tiras_dia['AL30'] else 0
            # ... agregar más cierres
        }
        guardar_referencia(cierre)
