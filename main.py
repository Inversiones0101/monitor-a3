def extraer_datos_rofex():
    # URL base sin parámetros extras para evitar ruidos
    url_base = "https://rofex.primary.ventures/api/v2/series/securities/rx_DDF_DLR_MAR26"
    
    # Parámetros simplificados: pedimos solo el día de hoy
    params = {
        "resolution": "5",
        "from": "2026-03-12T00:00:00.000Z", # Forzamos la fecha de hoy
        "to": "2026-03-12T23:59:59.000Z"
    }
    
    # Headers limpios (sin cookies viejas que causen el 401)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": "https://rofex.primary.ventures/"
    }
    
    try:
        print(f"🛰️ Intentando conexión anónima a Rofex...")
        r = requests.get(url_base, params=params, headers=headers, timeout=20)
        
        if r.status_code == 200:
            data = r.json()
            precios = data.get('c', [])
            if precios:
                print(f"✅ ¡INFILTRACIÓN EXITOSA! {len(precios)} puntos obtenidos.")
                # Convertimos a DataFrame
                tiempos = [datetime.datetime.fromtimestamp(t).strftime('%H:%M') for t in data.get('t', [])]
                return pd.DataFrame({"hora": tiempos, "precio": precios})
        
        print(f"❌ Error {r.status_code}: El servidor sigue pidiendo credenciales.")
        return None
    except Exception as e:
        print(f"⚠️ Error técnico: {e}")
        return None
