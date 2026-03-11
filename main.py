import requests
from bs4 import BeautifulSoup
import csv
import datetime
import os
import time

def obtener_precio():
    url = "https://www.rava.com/perfil/AL30"
    # Usamos un User-Agent de navegador real para que Rava nos deje pasar
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscamos el elemento exacto que descubriste ayer en las DevTools
        # El atributo data-v-3dea96a8 es nuestra llave
        precio_elemento = soup.find('p', {'data-v-3dea96a8': True})
        
        if precio_elemento:
            texto_precio = precio_elemento.get_text().strip()
            # Limpieza: "86.920,00" -> "86920.00"
            precio_limpio = texto_precio.replace('.', '').replace(',', '.')
            return float(precio_limpio)
        else:
            print("No se encontró el elemento del precio. Rava podría haber cambiado el ID.")
            return None
            
    except Exception as e:
        print(f"Error al capturar el dato: {e}")
        return None

def guardar_dato(precio):
    archivo_csv = 'datos_bono.csv'
    ahora = datetime.datetime.now()
    fecha = ahora.strftime('%Y-%m-%d')
    hora = ahora.strftime('%H:%M:%S')
    
    # Si el archivo no existe, lo creamos con cabecera
    es_nuevo = not os.path.exists(archivo_csv)
    
    with open(archivo_csv, mode='a', newline='') as file:
        writer = csv.writer(file)
        if es_nuevo:
            writer.writerow(['Fecha', 'Hora', 'Precio'])
        writer.writerow([fecha, hora, precio])
    print(f"Dato guardado: {hora} -> ${precio}")

# Ejecución principal
if __name__ == "__main__":
    print("Iniciando captura de precisión...")
    precio_actual = obtener_precio()
    if precio_actual:
        guardar_dato(precio_actual)
