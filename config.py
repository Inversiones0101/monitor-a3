# ═══════════════════════════════════════════════════════════════════
#  config.py — Panel de Control · monitor-a3
#  Inversiones & Algoritmos
#
#  ESTE ES EL ÚNICO ARCHIVO QUE NECESITÁS EDITAR para:
#  · Agregar / quitar activos financieros
#  · Cambiar fuentes de datos (URLs de APIs)
#  · Modificar horarios de envío
#  · Ajustar el estilo visual del gráfico
#  · Configurar el Visor ARG y Visor BCRA
# ═══════════════════════════════════════════════════════════════════


# ───────────────────────────────────────────────────────────────────
# 1. FUENTES DE DATOS — URLs de las APIs
# ───────────────────────────────────────────────────────────────────
# Agregá o quitá fuentes aquí. main.py las referencia por clave.

APIS = {
    "BONOS":     "https://data912.com/live/arg_bonds",
    "MEP":       "https://data912.com/live/mep",
    "ACCIONES":  "https://data912.com/live/arg_stocks",
    "ADRS":      "https://data912.com/live/usa_adrs",
    "FERIADOS":  "https://api.argentinadatos.com/v1/feriados/2026",
    "RIESGO_PAIS": "https://api.argentinadatos.com/v1/finanzas/indices/riesgo-pais",
    # ── Futura Fase 2 ──────────────────────────────────────────────
    # "BCRA_BASE": "https://api.bcra.gob.ar/estadisticas/v2.0/datosvariable",
}


# ───────────────────────────────────────────────────────────────────
# 2. ACTIVOS GRÁFICO PRINCIPAL — Bonos AL30 / AL30D / MEP
# ───────────────────────────────────────────────────────────────────
# Fase 1: solo AL30.  Fase 2: agregar GGAL, GD30, etc.
#
# Estructura de cada grupo:
#   "NOMBRE_GRUPO": {
#       "fuente":   clave de APIS (arriba),
#       "pesos":    símbolo del bono en ARS  (campo 'symbol' en la API),
#       "dolares":  símbolo del bono en USD,
#       "label":    texto que aparece en el título del gráfico,
#   }

GRUPOS_BONOS = {
    # ── FASE 1 — activo ───────────────────────────────────────────
    "AL30": {
        "fuente":  "BONOS",
        "pesos":   "AL30",
        "dolares": "AL30D",
        "label":   "AL30  Intradia BYMA",
    },

    # ── FASE 2 — comentados, listos para activar ──────────────────
    # "GD30": {
    #     "fuente":  "BONOS",
    #     "pesos":   "GD30",
    #     "dolares": "GD30D",
    #     "label":   "GD30  Intradia BYMA",
    # },
    # "GGAL_MEP": {
    #     "fuente":  "BONOS",
    #     "pesos":   "GGAL",
    #     "dolares": "GGAL_US",
    #     "label":   "GGAL  MEP",
    # },
}

# Grupo activo para el gráfico principal (clave de GRUPOS_BONOS)
GRUPO_ACTIVO = "AL30"


# ───────────────────────────────────────────────────────────────────
# 3. VISOR ARG — Acciones y ADRs argentinos
# ───────────────────────────────────────────────────────────────────
# Lista plana de tickers para yfinance.
# Agregá/quitá líneas para sumar o sacar activos.
#
# Estructura: "TICKER_YFINANCE": ("Nombre corto", "emoji")
#
# Tickers NYSE/NASDAQ terminan en nada  (ej: "GGAL", "YPF")
# Tickers BYMA  terminan en .BA         (ej: "GGAL.BA", "YPF.BA")

VISOR_ARG_TICKERS = {
    # ── NYSE / NASDAQ ─────────────────────────────────────────────
    "GGAL":  ("Galicia",       "🏦"),
    "YPF":   ("YPF",           "🛢️"),
    "MELI":  ("MercadoLibre",  "🛒"),
    "BMA":   ("Bco Macro",     "🏦"),
    "SUPV":  ("Supervielle",   "🏦"),
    # ── Fase 2 — comentados ───────────────────────────────────────
    # "PAM":   ("Pampa",         "⚡"),
    # "TGS":   ("TGS",           "🔧"),
    # "VITS":  ("Vitalibis",     "💊"),
    # ── BYMA (descomentar cuando se active Fase 2) ─────────────────
    # "GGAL.BA": ("Galicia BA",  "🏦"),
    # "YPF.BA":  ("YPF BA",      "🛢️"),
}


# ───────────────────────────────────────────────────────────────────
# 4. VISOR BCRA — Variables del Banco Central
# ───────────────────────────────────────────────────────────────────
# Cada ítem tiene: ID de variable bcra-wrapper, nombre a mostrar,
# columna (T0 = hoy / T2 = 48hs rezago), y si es calculado.
#
# IDs según documentación bcra-wrapper (Jaldekoa):
#   1  = Reservas Internacionales
#   4  = USD Oficial (Com. A 3500)
#   6  = Base Monetaria
#   10 = CER
#   2  = BADLAR (TNA Bancos Privados)
#   11 = Depósitos totales del sector privado
#   12 = Préstamos al sector privado
#   13 = TAMAR

VISOR_BCRA_ITEMS = [
    # ( ID_bcra,  "Etiqueta",            columna,  calculado )
    ( None,        "RIESGO PAIS",        "T0",     False ),   # argentinadatos.com
    ( 4,           "USD A3500",          "T0",     False ),
    ( 10,          "CER",                "T0",     False ),
    ( 2,           "BADLAR",             "T0",     False ),
    ( 13,          "TAMAR",              "T0",     False ),
    ( 1,           "RESERVAS INTER",     "T2",     False ),
    ( 6,           "BASE MONETARIA",     "T2",     False ),
    ( "6/1",       "B.MON / R.IN",       "T2",     True  ),   # ID6 / ID1
    ( "6/4",       "B.MON / USD.OF",     "T2",     True  ),   # ID6 / ID4
    ( "12/11*100", "PREST / DEPOS",      "T2",     True  ),   # (ID12/ID11)*100
]


# ───────────────────────────────────────────────────────────────────
# 5. HORARIOS DE EJECUCIÓN (hora Argentina)
# ───────────────────────────────────────────────────────────────────
# Modificá aquí para cambiar cuándo se ejecuta cada acción.
# Formato "HH:MM". La tolerancia de detección es ±4 minutos
# (el cron dispara cada 5 min, nunca se pierde un envío).

HORARIOS = {
    "apertura_mercado":  "10:30",   # primer precio del día
    "cierre_captura":    "17:05",   # último precio capturado
    "grafico_1":         "12:00",   # 1er gráfico → "Mercado Abierto"
    "visor_arg_1":       "13:00",   # 1er Visor ARG
    "grafico_2":         "15:00",   # 2do gráfico → "Mercado Abierto"
    "visor_arg_2":       "15:30",   # 2do Visor ARG
    "grafico_cierre":    "17:05",   # gráfico final → "Mercado Cerrado"
    "visor_bcra":        "17:10",   # Visor BCRA (único envío del día)
    "visor_arg_cierre":  "17:30",   # Visor ARG final
    "limpiar_csv":       "18:00",   # limpiar datos_al30.csv
}


# ───────────────────────────────────────────────────────────────────
# 6. ARCHIVOS DEL REPOSITORIO
# ───────────────────────────────────────────────────────────────────

ARCHIVOS = {
    "csv":           "datos_al30.csv",        # precios intradiarios
    "grafico":       "grafico_al30.png",       # último gráfico generado
    "estado_envios": "estado_envios.csv",      # control anti-doble-envío
    "visor_bcra":    "visor_bcra_hoy.png",     # imagen Visor BCRA
}


# ───────────────────────────────────────────────────────────────────
# 7. ESTILO DEL GRÁFICO — Tema TradingView Dark
# ───────────────────────────────────────────────────────────────────

GRAFICO = {
    # Dimensiones
    "figsize":       (13, 6.5),
    "dpi":           130,

    # Colores
    "bg":            "#131722",    # fondo oscuro
    "grid":          "#1e2230",    # líneas de grid
    "text":          "#d1d4dc",    # texto general
    "footer_bg":     "#363c4e",    # fondo del footer

    # Líneas de activos
    "color_pesos":   "#FFD700",    # AL30 en ARS  → amarillo dorado
    "color_dolares": "#26a69a",    # AL30D en USD → verde teal
    "color_mep":     "#ef5350",    # MEP/AL30     → rojo

    # Grosor de líneas
    "lw_principal":  2.2,
    "lw_mep":        1.5,
}


# ───────────────────────────────────────────────────────────────────
# 8. MENSAJES A TELEGRAM
# ───────────────────────────────────────────────────────────────────

MENSAJES = {
    "mercado_abierto":  "🟢 Mercado Abierto",
    "mercado_cerrado":  "🔴 Mercado Cerrado",
    "visor_arg_header": "🇦🇷 VISOR ARG",
    "visor_bcra_header": "🏦 VISOR BCRA",
    "fuente_bonos":     "Fuente: data912.com",
    "fuente_acciones":  "Fuente: yfinance | NYSE",
    "fuente_bcra":      "Fuente: BCRA / argentinadatos.com",
}
