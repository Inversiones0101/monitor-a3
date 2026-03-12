import requests
import re
import os
import datetime
import pandas as pd
import matplotlib.pyplot as plt

def hackear_precio_preciso(url, nombre, min_val, max_val):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://www.google.com/"
    }
    try:
        r = requests.get(url, headers=headers, timeout=20)
        # Buscamos números con formato 12.345,67 o 123,45
        encontrados = re.findall(r'(\d{1,3}(?:\.\d{3})*,\d{2})', r.text)
        
        for e in encontrados:
            val = float(e.replace('.', '').replace(',', '.'))
            # FILTRO SNIPER: Solo aceptamos el número si cae en el rango lógico del activo
            if min_val <= val <= max_val:
                print(f"🎯 {nombre} encontrado con precisión: {val}")
                return val
        return None
    except: return None

def mision_final():
    # Definimos rangos lógicos para no capturar el volumen (millones)
    # AL30: entre 40k y 120k | AL30D: entre 40 y 150
    p_arv = hackear_precio_preciso("https://www.rava.com/perfil/AL30", "AL30", 40000, 150000)
    p_usd = hackear_precio_preciso("https://www.rava.com/perfil/AL30D", "AL30D", 40, 150)
    
    if p_arv and p_usd:
        mep = p_arv / p_usd
        ahora = datetime.datetime.now().strftime("%H:%M")
        
        # Guardar y Graficar (Igual al anterior pero con datos reales)
        # ... (Tu lógica de gráfico aquí) ...
        
        token, chat = os.getenv('TELEGRAM_TOKEN'), os.getenv('TELEGRAM_CHAT_ID')
        caption = f"✅ *MAMUT DOMADO*\n\n📈 *AL30:* ${p_arv:,.2f}\n📉 *AL30D:* u$s{p_usd:,.2f}\n🔥 *MEP REAL:* ${mep:.2f}"
        
        # Generar gráfico rápido para el ejemplo
        plt.style.use('dark_background')
        plt.figure(figsize=(8, 4))
        plt.plot([mep], marker='o', color='red')
        plt.title(f"MEP ACTUAL: ${mep:.2f}")
        plt.savefig("monitor_real.png")
        
        with open("monitor_real.png", 'rb') as f:
            requests.post(f"https://api.telegram.org/bot{token}/sendPhoto", 
                          data={'chat_id': chat, 'caption': caption, 'parse_mode': 'Markdown'}, files={'photo': f})
        print("🚀 ¡Misión cumplida con datos reales!")

if __name__ == "__main__":
    mision_final()
