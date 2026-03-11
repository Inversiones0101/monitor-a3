import requests
import csv
import datetime
import os
import json
import re

def obtener_precio():
    url = "https://www.rava.com/perfil/AL30"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        # Buscamos el bloque de datos que alimenta al gráfico (el que vimos en la captura)
        # Usamos una expresión regular para encontrar el array de precios
        match = re.search(r'this\.datos\s*=\s*(\[.*?\]);', response.text)
        
        if match:
            datos_json = match.group(1)
            datos = json.loads(datos_json)
            # El último elemento del array es el precio más actual del gráfico
            ultimo_precio = datos[-1]['ultimo']
            return float(ultimo_precio)
        else:
            print("No se encontró el array de datos del gráfico.")
            return None
            
    except Exception as e:
        print(f"Error en la captura V3: {e}")
        return None

def guardar_dato(precio):
    archivo_csv = 'datos_bono.csv'
    ahora = datetime.datetime.now()
    fecha = ahora.strftime('%Y-%m-%d')
    hora = ahora.strftime('%H:%M:%S')
    es_nuevo = not os.path.exists(archivo_csv)
    
    with open(archivo_csv, mode='a', newline='') as file:
        writer = csv.writer(file)
        if es_nuevo:
            writer.writerow(['Fecha', 'Hora', 'Precio'])
        writer.writerow([fecha, hora, precio])
    print(f"Hormiga V3 - Dato guardado: {hora} -> ${precio}")

if __name__ == "__main__":
    print("Iniciando captura V3 (Directo al Gráfico)...")
    precio_actual = obtener_precio()
    if precio_actual:
        guardar_dato(precio_actual)
