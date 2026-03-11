import requests
import csv
import datetime
import os
import re

def obtener_precio():
    url = "https://www.rava.com/perfil/AL30"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Referer": "https://www.google.com/"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"Infiltración V3.3 - Tamaño: {len(response.text)} caracteres")
        
        # BUSQUEDA ULTRA-FLEXIBLE: 
        # Buscamos cualquier par de: "ultimo" : "87.140,00" o 'ultimo' : '87.140,00'
        # Incluso si no hay comillas en la palabra ultimo.
        patrones = [
            r'ultimo["\']?\s*:\s*["\']([\d\.]+),(\d+)["\']', 
            r'curese["\']?\s*:\s*["\']([\d\.]+),(\d+)["\']'  # Respaldo por si usan 'cierre'
        ]
        
        for patron in patrones:
            precios = re.findall(patron, response.text)
            if precios:
                # Tomamos el último precio encontrado (el más reciente del gráfico)
                ultimo = precios[-1]
                num_str = ultimo[0].replace('.', '') + '.' + ultimo[1]
                print(f"¡HORMIGA ATÓMICA! Encontró el dato usando patrón: {patron}")
                return float(num_str)
        
        # Si todo falla, buscamos el primer número grande que parezca el precio del AL30
        # Buscamos algo como 86.950,00
        emergencia = re.search(r'(\d{2}\.\d{3}),(\d{2})', response.text)
        if emergencia:
            num_str = emergencia.group(1).replace('.', '') + '.' + emergencia.group(2)
            print("Éxito por búsqueda de emergencia (Fuerza Bruta).")
            return float(num_str)

        return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

def guardar_dato(precio):
    archivo_csv = 'datos_bono.csv'
    ahora = datetime.datetime.now()
    fecha = ahora.strftime('%Y-%m-%d')
    hora = ahora.strftime('%H:%M:%S')
    es_nuevo = not os.path.exists(archivo_csv)
    with open(archivo_csv, mode='a', newline='') as file:
        writer = csv.writer(file)
        if es_nuevo: writer.writerow(['Fecha', 'Hora', 'Precio'])
        writer.writerow([fecha, hora, precio])
    print(f"✅ DATO CAPTURADO: ${precio} a las {hora}")

if __name__ == "__main__":
    print("--- EJECUTANDO HORMIGA ATÓMICA V3.3 ---")
    precio = obtener_precio()
    if precio:
        guardar_dato(precio)
    else:
        print("❌ El Mamut sigue escondiendo el precio. Necesitamos otra estrategia.")
