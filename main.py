import requests
from bs4 import BeautifulSoup
import re
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# --- CONFIGURACIÓN ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
CSV_FILE = 'datos_dia.csv'

def obtener_precio(ticker):
    url = f"https://www.rava.com/perfil/{ticker}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            texto_titulo = soup.title.text
            # Buscamos el precio (formato 86.620,00 o 1.250.000,00)
            match = re.search(r'(\d{1,3}(\.\d{3})*,\d{2})', texto_titulo)
            if match:
                return float(match.group(1).replace('.', '').replace(',', '.'))
    except: pass
    return None

def main():
    ahora_dt = datetime.now()
    hora_str = ahora_dt.strftime('%H:%M')
    print(f"--- INICIANDO CAPTURA ({hora_str}) ---")

    # 1. Limpieza a las 18:00hs
    if ahora_dt.hour >= 18 and os.path.exists(CSV_FILE):
        os.remove(CSV_FILE)
        print("Historial diario borrado. Preparado para mañana.")
        return

    # 2. Captura de datos
    datos = {
        'hora': hora_str,
        'al30': obtener_precio("AL30"),
        'al30d': obtener_precio("AL30D"),
        'gd30': obtener_precio("GD30"),
        'gd30d': obtener_precio("GD30D"),
        'merval': obtener_precio("MERVAL")
    }

    # 3. Cálculos
    if datos['al30'] and datos['al30d']:
        datos['mep_al'] = round(datos['al30'] / datos['al30d'], 2)
    if datos['gd30'] and datos['gd30d']:
        datos['mep_gd'] = round(datos['gd30'] / datos['gd30d'], 2)
    if datos['merval'] and 'mep_al' in datos:
        datos['merval_usd'] = round(datos['merval'] / datos['mep_al'], 2)

    # 4. Guardar en CSV
    df_nuevo = pd.DataFrame([datos])
    df_nuevo.to_csv(CSV_FILE, mode='a', header=not os.path.exists(CSV_FILE), index=False)
    
    # 5. Lógica de Envío (Solo en horarios específicos)
    horarios_reporte = ["11:00", "11:05", "13:00", "13:05", "15:00", "15:05", "17:00", "17:05"]
    
    # Para probar ahora, si querés forzar el envío, podés comentar el 'if'
    if any(h in hora_str for h in horarios_reporte) or True: # Quitá el 'or True' para producción
        generar_y_enviar_reporte(datos)

def generar_y_enviar_reporte(datos):
    df = pd.read_csv(CSV_FILE)
    plt.style.use('dark_background') # ¡Estética Dark!
    
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # Eje Izquierdo (Dólares/MEP)
    ax1.plot(df['hora'], df['mep_al'], color='#ff4444', linewidth=3, label='MEP AL30 (Eje Izq)')
    ax1.set_ylabel('Precio Dólar ($)', color='#ff4444')
    
    # Eje Derecho (Merval USD o Bonos Pesos)
    ax2 = ax1.twinx()
    ax2.plot(df['hora'], df['merval_usd'], color='#00ff00', linewidth=2, label='Merval USD (Eje Der)')
    ax2.set_ylabel('Merval USD', color='#00ff00')

    plt.title(f"MONITOR REALTIME - {datetime.now().strftime('%d/%m/%Y')}")
    fig.tight_layout()
    plt.savefig('reporte.png')
    plt.close()

    # Enviar a Telegram
    mensaje = (f"🚀 *REPORTE FINANCIERO*\n\n"
               f"💰 *MEP AL30:* ${datos.get('mep_al')}\n"
               f"💰 *MEP GD30:* ${datos.get('mep_gd')}\n"
               f"📈 *Merval USD:* u$s{datos.get('merval_usd')}\n\n"
               f"🕒 Datos actualizados a las {datos['hora']}")
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open('reporte.png', 'rb') as f:
        requests.post(url, data={'chat_id': CHAT_ID, 'caption': mensaje, 'parse_mode': 'Markdown'}, files={'photo': f})

if __name__ == "__main__":
    main()
