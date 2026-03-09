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
    hora_actual = ahora_dt.hour
    minuto_actual = ahora_dt.minute
    dia_semana = ahora_dt.weekday() # 0=Lunes, 4=Viernes

    # --- INTERRUPTOR DE SEGURIDAD Y LIMPIEZA ---
    if dia_semana > 4: # Sábado o Domingo
        print(f"--- MODO DORMIDO ({hora_str}) - Fin de semana ---")
        return
    
    if hora_actual < 10 or (hora_actual >= 18 and minuto_actual > 10):
        # Si es la ventana de las 18:00, limpiamos el historial
        if hora_actual == 18 and 0 <= minuto_actual <= 10:
            if os.path.exists(CSV_FILE):
                os.remove(CSV_FILE)
                print(f"--- LIMPIEZA REALIZADA ({hora_str}) - Preparado para mañana ---")
        else:
            print(f"--- MODO DORMIDO ({hora_str}) - Fuera de mercado ---")
        return

    # --- SI EL BOT LLEGA AQUÍ, ES QUE EL MERCADO ESTÁ ABIERTO ---
    print(f"--- INICIANDO CAPTURA ({hora_str}) ---")

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

    # 5. Lógica de Envío con "Paracaídas"
    horarios_reporte = ["11:00", "11:05", "13:00", "13:05", "15:00", "15:05", "17:00", "17:05"]
    
    # Leemos el archivo para ver si tiene datos suficientes para el gráfico
    df_historico = pd.read_csv(CSV_FILE)
    
    # Verificamos: ¿Es hora de reporte? ¿Y tenemos al menos 2 puntos para dibujar una línea?
    es_hora = any(h in hora_str for h in horarios_reporte)
    tiene_datos = len(df_historico) > 1 and 'mep_al' in df_historico.columns

    if tiene_datos: # Quitamos la validación de hora temporalmente
        generar_y_enviar_reporte(datos)
    else:
        # Esto solo saldrá en los logs de GitHub para que sepas qué está pasando
        razon = "No es horario de reporte" if not es_hora else "Esperando segundo dato para graficar"
        print(f"--- REPORTE OMITIDO: {razon} ---")

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
