def extraer_datos_rofex():
    # URL limpia
    url_base = "https://rofex.primary.ventures/api/v2/series/securities/rx_DDF_DLR_MAR26"
    
    # Calculamos el rango de hoy dinámicamente
    ahora = datetime.datetime.now()
    hace_24h = ahora - datetime.timedelta(days=1)
    
    params = {
        "resolution": "5",
        "from": hace_24h.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "to": ahora.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": "https://rofex.primary.ventures/"
    }
    
    try:
        print(f"🛰️ Consultando Rofex (Rango: {params['from']} - {params['to']})...")
        r = requests.get(url_base, params=params, headers=headers, timeout=20)
        
        if r.status_code == 200:
            data = r.json()
            precios = data.get('c', [])
            if precios:
                print(f"✅ ¡DATOS CAPTURADOS! {len(precios)} puntos.")
                tiempos = [datetime.datetime.fromtimestamp(t).strftime('%H:%M') for t in data.get('t', [])]
                return pd.DataFrame({"hora": tiempos, "precio": precios})
            else:
                print("⚠️ La respuesta llegó vacía (mercado cerrado o sin trades).")
        else:
            print(f"❌ Error {r.status_code}. Respuesta: {r.text[:100]}")
            
        return None
    except Exception as e:
        print(f"⚠️ Error técnico: {e}")
        return None
