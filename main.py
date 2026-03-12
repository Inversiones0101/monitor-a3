def extraer_datos_rofex():
    # Iniciamos una sesión de requests para mantener las cookies automáticamente
    session = requests.Session()
    
    # URL de la web y de la API
    url_web = "https://rofex.primary.ventures/security/rx_DDF_DLR_MAR26?interval=5"
    url_api = "https://rofex.primary.ventures/api/v2/series/securities/rx_DDF_DLR_MAR26"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": url_web
    }
    
    try:
        # PASO 1: Visita fantasma para capturar cookies
        print("🕵️‍♂️ Obteniendo credenciales de sesión...")
        session.get(url_web, headers=headers, timeout=15)
        
        # PASO 2: Pedir los datos usando las cookies capturadas
        ahora = datetime.datetime.now()
        params = {
            "resolution": "5",
            "from": (ahora - datetime.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "to": ahora.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        }
        
        print(f"🛰️ Consultando API con sesión activa...")
        r = session.get(url_api, params=params, headers=headers, timeout=20)
        
        if r.status_code == 200:
            data = r.json()
            precios = data.get('c', [])
            if precios:
                print(f"✅ ¡INFILTRACIÓN EXITOSA! {len(precios)} puntos.")
                tiempos = [datetime.datetime.fromtimestamp(t).strftime('%H:%M') for t in data.get('t', [])]
                return pd.DataFrame({"hora": tiempos, "precio": precios})
        
        print(f"❌ Error {r.status_code}: El Mamut bloqueó la sesión.")
        return None
    except Exception as e:
        print(f"⚠️ Error técnico: {e}")
        return None
