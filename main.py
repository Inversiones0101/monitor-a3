import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os

# --- CONFIGURACIÓN TELEGRAM ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
CSV_FILE = 'datos_dia.csv'

# --- FUENTES DE DATOS (JSON de Gráficos) ---
URL_AL30_ARS = "https://mercados.ambito.com/al30/grafico/intradiario"
URL_AL30_USD = "https://mercados.ambito.com/al30d/grafico/intradiario"

def obtener_ultimo_del_grafico(url):
    """Extrae el último punto [hora, precio] de la tira del gráfico."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            datos = r.json() # Formato: [["HH:mm", precio], ...]
            if len(datos) > 1:
                # El primer elemento suele ser encabezado, tomamos el último real
                ultimo_punto = datos[-1]
                return float(ultimo_punto[1])
    except Exception as e:
        print(f"Error extrayendo de {url}: {e}")
    return None

def obtener_datos_grafico(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            return r.json() # Devuelve la lista completa [[hora, precio], ...]
    except:
        return []

def manejar_datos():
    ahora = datetime.now()
    # Capturamos las tiras completas
    datos_ars = obtener_datos_grafico(URL_AL30_ARS)
    datos_usd = obtener_datos_grafico(URL_AL30_USD)
    
    if not datos_ars or not datos_usd:
        print("Aún no hay datos en la fuente. Reintentando en la próxima corrida.")
        return False

    # Armamos un DataFrame con lo que haya
    # Usamos el último precio disponible de la tira
    p_ars = float(datos_ars[-1][1])
    p_usd = float(datos_usd[-1][1])
    mep = round(p_ars / p_usd, 2)
    
    timestamp = ahora.strftime('%Y-%m-%d %H:%M')
    nuevos = [
        {'timestamp': timestamp, 'activo': 'AL30_ARS', 'valor': p_ars},
        {'timestamp': timestamp, 'activo': 'AL30_USD', 'valor': p_usd},
        {'timestamp': timestamp, 'activo': 'MEP', 'valor': mep}
    ]
    
    df_nuevos = pd.DataFrame(nuevos)
    df_nuevos.to_csv(CSV_FILE, mode='a', header=not os.path.exists(CSV_FILE), index=False)
    return True

def generar_y_enviar_reporte():
    if not os.path.exists(CSV_FILE): return
    
    df = pd.read_csv(CSV_FILE)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Creamos el gráfico con Doble Eje Y
    fig, ax1 = plt.subplots(figsize=(12, 7))
    ax2 = ax1.twinx() # Eje para Dólares/MEP
    
    # --- LÍNEA AMARILLA: AL30 PESOS ---
    df_ars = df[df['activo'] == 'AL30_ARS']
    if not df_ars.empty:
        ax1.plot(df_ars['timestamp'], df_ars['valor'], color='#FFD700', label='AL30 Pesos ($)', linewidth=3, marker='o', markersize=4)
    
    # --- LÍNEA VERDE: AL30 USD ---
    df_usd = df[df['activo'] == 'AL30_USD']
    if not df_usd.empty:
        ax2.plot(df_usd['timestamp'], df_usd['valor'], color='#228B22', label='AL30 USD (u$s)', linewidth=2, linestyle='--')
    
    # --- LÍNEA ROJA: MEP ---
    df_mep = df[df['activo'] == 'MEP']
    if not df_mep.empty:
        ax2.plot(df_mep['timestamp'], df_mep['valor'], color='#FF0000', label='Dólar MEP', linewidth=2)

    # Configuración visual
    ax1.set_ylabel('Precio Pesos ($)', color='orange', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Dólar MEP / Bono USD', color='green', fontsize=12, fontweight='bold')
    plt.title(f'Monitor AL30 Multimoneda - {datetime.now().strftime("%d/%m %H:%M")}', fontsize=14, pad=20)
    ax1.grid(True, alpha=0.2)
    
    # Leyendas unificadas
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc='upper left', frameon=True)

    plt.tight_layout()
    plt.savefig('reporte.png', dpi=120)
    plt.close()

    # Envío a Telegram
    try:
        url_tel = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        with open('reporte.png', 'rb') as f:
            mep_val = df_mep['valor'].iloc[-1] if not df_mep.empty else "N/A"
            caption = f"📊 *Actualización Realtime*\n💵 MEP: ${mep_val}\n🕒 {datetime.now().strftime('%H:%M hs')}"
            requests.post(url_tel, data={'chat_id': CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}, files={'photo': f})
    except Exception as e:
        print(f"Error envío: {e}")

if __name__ == "__main__":
    # 1. Siempre intentamos capturar datos y guardarlos cada 5 minutos
    datos_guardados_ok = manejar_datos()
    
    if datos_guardados_ok:
        ahora = datetime.now()
        
        # 2. SOLO envía a Telegram si estamos cerca de la "hora en punto"
        # Esto disparará el reporte a las 11:00, 12:00, 13:00, etc.
        if ahora.minute < 5: 
            print("Es hora del reporte horario. Generando gráfico...")
            generar_y_enviar_reporte()
        else:
            print(f"Dato guardado a las {ahora.strftime('%H:%M')}. El próximo gráfico se enviará a la hora en punto.")
            
