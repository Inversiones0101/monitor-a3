import requests
import csv
import datetime
import os
import re
import json

def obtener_precio():
    url = "https://www.rava.com/perfil/AL30"
    
    # Camuflaje reforzado: parecemos un humano entrando desde Google
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3",
        "Referer": "https://www.google.com/",
        "Connection": "keep-alive",
        "DNT": "1"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        # Log para debug: nos dice si recibimos una página real o un error pequeño
        print(f"Infiltración V3.1 - Tamaño de respuesta: {len(response.text)} caracteres")
        
        # ESTRATEGIA A: Buscar el array de datos del gráfico (JSON)
        # Buscamos patrones como 'datos: [...]' o 'this.datos = [...]'
        match = re.search(r'datos\s*:\s*(\[.*?\])', response.text)
        if not match:
            match = re.search(r'this\.datos\s*=\s*(\[.*?\]);', response.text)

        if match:
            datos_json = match.group(1)
            datos = json.loads(datos_json)
            # Extraemos el último precio del array (el más reciente)
            ultimo_precio = datos[-1]['ultimo']
            print("Éxito: Dato extraído del array del gráfico.")
            return float(ultimo_precio)
        
        # ESTRATEGIA B: Respaldo (Búsqueda de texto plano si el JS no está disponible)
        else:
            print("Array no encontrado. Iniciando búsqueda de respaldo en texto plano...")
            # Buscamos el patrón "ultimo":"87.140,00"
            respaldo = re.search(r'"ultimo":"([\d\.]+),(\d+)"', response.text)
            if respaldo:
                # Convertimos "87.140,00" -> "87140.00"
                num_str = respaldo.group(1).replace('.', '') + '.' + respaldo.group(2)
                print("Éxito: Dato extraído de los metadatos de respaldo.")
                return float(num_str)
            
            print("El Mamut bloqueó todos los accesos. No se encontró el precio.")
            return None
            
    except Exception as e:
        print(f"Error crítico en la infiltración: {e}")
        return None

def guardar_dato(precio):
    archivo_csv = 'datos_bono.csv'
    ahora = datetime.datetime.now()
    fecha = ahora.strftime('%Y-%m-%d')
    hora = ahora.strftime('%H:%M:%S')
    
    # Verificamos si hay que escribir cabecera
    es_nuevo = not os.path.exists(archivo_csv)
    
    with open(archivo_csv, mode='a', newline='') as file:
        writer = csv.writer(file)
        if es_nuevo:
            writer.writerow(['Fecha', 'Hora', 'Precio'])
        writer.writerow([fecha, hora, precio])
    
    print(f"✅ HORMIGA VICTORIOSA: Guardado ${precio} a las {hora}")

if __name__ == "__main__":
    print("--- INICIANDO OPERACIÓN HORMIGA V3.1 ---")
    precio_actual = obtener_precio()
    
    if precio_actual:
        guardar_dato(precio_actual)
    else:
        print("❌ Operación fallida. El Mamut ganó esta ronda.")
