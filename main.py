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
        print(f"Infiltración V3.5 - Tamaño: {len(response.text)} caracteres")
        
        # Patrones flexibles para detectar el formato de Rava
        patrones = [
            r'ultimo["\']?\s*:\s*["\']([\d\.]+),(\d+)["\']', 
            r'["\']?([\d\.]+),(\d+)["\']' 
        ]
        
        candidatos = []
        for patron in patrones:
            encontrados = re.findall(patron, response.text)
            for p in encontrados:
                try:
                    # Convertimos el texto "86.920,00" a número 86920.0
                    valor = float(p[0].replace('.', '') + '.' + p[1])
                    # FILTRO DE PUNTERÍA: Solo precios coherentes con el AL30 hoy
                    if 85000 < valor < 92000:
                        candidatos.append(valor)
                except:
                    continue
        
        if candidatos:
            # Ordenamos para asegurar que no sea un dato viejo y tomamos el último del gráfico
            # El gráfico intradiario suele ser la última lista de precios en el HTML
            precio_final = candidatos[-1]
            print(f"✅ PUNTERÍA LÁSER: Encontrados {len(candidatos)} puntos. Usando: ${precio_final}")
            return precio_final
        
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
        if es_nuevo:
            writer.writerow(['Fecha', 'Hora', 'Precio'])
        writer.writerow([fecha, hora, precio])
    
    print(f"💾 ARCHIVADO: ${precio} guardado exitosamente.")

if __name__ == "__main__":
    print("--- EJECUTANDO HORMIGA ATÓMICA V3.5 (PUNTERÍA LÁSER) ---")
    precio = obtener_precio()
    if precio:
        guardar_dato(precio)
    else:
        print("❌ El Mamut ganó esta ronda. No se detectaron precios en el rango esperado.")
