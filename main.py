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
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        # Buscamos el precio en el título: "AL30 - 86.380,00 - ..."
        inicio = response.text.find("<title>") + 7
        fin = response.text.find("</title>")
        titulo = response.text[inicio:fin]
        
        # Extraemos solo el número (el segundo elemento después del guion)
        partes = titulo.split("-")
        if len(partes) > 1:
            precio_str = partes[1].strip().replace(".", "").replace(",", ".")
            return float(precio_str)
    except Exception as e:
        print(f"Error capturando {ticker}: {e}")
    return None

def main():
    ahora_dt = datetime.now()
    hora_str = ahora_dt.strftime('%H:%M')
    hora_actual = ahora_dt.hour
    minuto_actual = ahora_dt.minute
    dia_semana = ahora_dt.weekday() 

    # --- INTERRUPTOR DE SEGURIDAD ---
    if dia_semana > 4:
        print(f"--- MODO DORMIDO ({hora_str}) - Fin de semana ---")
        return
    
    if hora_actual < 10 or (hora_actual >= 18 and minuto_actual > 10):
        if hora_actual == 18 and 0 <= minuto_actual <= 10:
            if os.path.exists(CSV_FILE):
                os.remove(CSV_FILE)
                print(f"--- LIMPIEZA REALIZADA ({hora_str}) ---")
        else:
            print(f"--- MODO DORMIDO ({hora_str}) - Fuera de mercado ---")
        return

    print(f"--- INICIANDO CAPTURA ({hora_str}) ---")

    # 2. Captura
    datos = {
        'hora': hora_str,
        'al30': obtener_precio("AL30"),
        'al30d': obtener_precio("AL30D"),
        'gd30': obtener_precio("GD30"),
        'gd30d': obtener_precio("GD30D"),
        'merval': obtener_precio("MERVAL")
    }

    # 3. Cálculos (Solo si hay datos)
    if datos['al30'] and datos['al30d']:
        datos['mep_al'] = round(datos['al30'] / datos['al30d'], 2)
    
    if datos['gd30'] and datos['gd30d']:
        datos['mep_gd'] = round(datos['gd30'] / datos['gd30d'], 2)
        
    if datos['merval'] and 'mep_al' in datos:
        datos['merval_usd'] = round(datos['merval'] / datos['mep_al'], 2)

    # 4. Guardar en CSV
    df_nuevo = pd.DataFrame([datos])
    df_nuevo.to_csv(CSV_FILE, mode='a', header=not os.path.exists(CSV_FILE), index=False)

    # 5. Lógica de Envío Inteligente
    df_historico = pd.read_csv(CSV_FILE)
    
    # Verificamos si las columnas necesarias existen y tienen datos
    tiene_mep = 'mep_al' in df_historico.columns and not df_historico['mep_al'].isnull().all()
    tiene_merval = 'merval_usd' in df_historico.columns and not df_historico['merval_usd'].isnull().all()

    if True and tiene_mep and tiene_merval: # Forzamos para la prueba
        print("🚀 Enviando reporte a Telegram...")
        generar_y_enviar_reporte(datos)
    else:
        print("⚠️ Captura realizada pero faltan datos para el gráfico (Rava devolvió vacío)")

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
