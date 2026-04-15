"""
main.py — Motor de ejecución · monitor-a3
Inversiones & Algoritmos · GitHub Actions

Arquitectura: cron cada 5 min → script lee la hora AR → ejecuta la tarea
correspondiente → termina. Cada ejecución dura ~15 segundos.

IMPORTANTE: Este archivo NO contiene configuración.
Toda la configuración (URLs, tickers, horarios, colores) está en config.py
"""

import os
import sys
import requests
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from datetime import datetime, date
import pytz

# ── Importar toda la configuración desde config.py ─────────────────
from config import (
    APIS, GRUPOS_BONOS, GRUPO_ACTIVO,
    VISOR_ARG_TICKERS,
    HORARIOS, ARCHIVOS, GRAFICO, MENSAJES,
)


# ═══════════════════════════════════════════════════════════════════
# SECCIÓN 1 — UTILIDADES DE TIEMPO
# ═══════════════════════════════════════════════════════════════════

TZ_AR = pytz.timezone('America/Argentina/Buenos_Aires')


def hora_ar() -> datetime:
    return datetime.now(TZ_AR)


def hhmm(dt: datetime = None) -> str:
    return (dt or hora_ar()).strftime("%H:%M")


def es_dia_habil() -> bool:
    """Retorna True si hoy es lunes-viernes y no es feriado argentino."""
    hoy = hora_ar()
    if hoy.weekday() >= 5:
        print(f"⏸️  Fin de semana ({hoy.strftime('%A')}). Sin operación.")
        return False
    try:
        resp = requests.get(APIS["FERIADOS"], timeout=8)
        resp.raise_for_status()
        fechas = [f['fecha'] for f in resp.json() if 'fecha' in f]
        if hoy.strftime("%Y-%m-%d") in fechas:
            print(f"🗓️  Feriado hoy ({hoy.strftime('%Y-%m-%d')}). Sin operación.")
            return False
    except Exception as e:
        print(f"⚠️  No se pudo verificar feriados: {e}. Continuando de todos modos.")
    return True


def hora_entre(h_ini: str, h_fin: str) -> bool:
    return h_ini <= hhmm() <= h_fin


def es_hora_exacta(h_obj: str, tolerancia: int = 4) -> bool:
    """
    True si la hora actual AR está dentro de ±tolerancia minutos de h_obj.
    Con cron cada 5 min y tolerancia=4, nunca se pierde un envío.
    """
    ahora = hora_ar()
    hh, mm = map(int, h_obj.split(":"))
    objetivo = ahora.replace(hour=hh, minute=mm, second=0, microsecond=0)
    return abs((ahora - objetivo).total_seconds() / 60) <= tolerancia


# ═══════════════════════════════════════════════════════════════════
# SECCIÓN 2 — CONTROL DE DOBLE ENVÍO
# ═══════════════════════════════════════════════════════════════════

def ya_se_envio(clave: str) -> bool:
    """Verifica si la acción 'clave' ya se ejecutó hoy."""
    path = ARCHIVOS["estado_envios"]
    if not os.path.exists(path):
        return False
    try:
        df = pd.read_csv(path, dtype=str)
        hoy = hora_ar().strftime("%Y-%m-%d")
        return ((df['fecha'] == hoy) & (df['clave'] == clave)).any()
    except Exception:
        return False


def marcar_enviado(clave: str):
    """Registra que la acción 'clave' se ejecutó hoy."""
    path = ARCHIVOS["estado_envios"]
    hoy  = hora_ar().strftime("%Y-%m-%d")
    nuevo = pd.DataFrame([{"fecha": hoy, "clave": clave}])
    if not os.path.exists(path):
        nuevo.to_csv(path, index=False)
    else:
        df = pd.read_csv(path, dtype=str)
        pd.concat([df, nuevo], ignore_index=True).to_csv(path, index=False)


def limpiar_estado():
    """Elimina registros de estado con más de 3 días."""
    path = ARCHIVOS["estado_envios"]
    if not os.path.exists(path):
        return
    try:
        df  = pd.read_csv(path, dtype=str)
        hoy = hora_ar().date()
        df  = df[df['fecha'].apply(
            lambda f: (hoy - date.fromisoformat(f)).days <= 3
        )]
        df.to_csv(path, index=False)
    except Exception as e:
        print(f"⚠️  Error limpiando estado: {e}")


# ═══════════════════════════════════════════════════════════════════
# SECCIÓN 3 — CAPTURA DE PRECIOS Y CSV
# ═══════════════════════════════════════════════════════════════════

def capturar_precio() -> dict | None:
    """
    Consulta la API de bonos y devuelve el precio del grupo activo.
    Lee el símbolo de los activos desde config.GRUPOS_BONOS[GRUPO_ACTIVO].
    """
    grupo = GRUPOS_BONOS[GRUPO_ACTIVO]
    url   = APIS[grupo["fuente"]]

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        sym_p = grupo["pesos"]
        sym_d = grupo["dolares"]

        bono_ars = next((x for x in data if x.get('symbol') == sym_p), None)
        bono_usd = next((x for x in data if x.get('symbol') == sym_d), None)

        if not bono_ars or not bono_usd:
            print(f"⚠️  No se encontraron {sym_p}/{sym_d} en la respuesta.")
            return None

        p_ars = float(bono_ars['c'])
        p_usd = float(bono_usd['c'])

        if p_usd == 0:
            print("⚠️  Precio USD es 0. No se puede calcular MEP.")
            return None

        mep = round(p_ars / p_usd, 2)
        ts  = hhmm()

        print(f"✅ {ts} | {sym_p}: ${p_ars:,.2f} | {sym_d}: u$s{p_usd:.2f} | MEP: ${mep:,.2f}")
        return {"hora": ts, sym_p: round(p_ars, 2), sym_d: round(p_usd, 2), "mep": mep}

    except Exception as e:
        print(f"⚠️  Error capturando precio: {e}")
        return None


def guardar_en_csv(dato: dict):
    path = ARCHIVOS["csv"]
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        pd.DataFrame([dato]).to_csv(path, index=False)
        print("📄 CSV inicializado con primer dato.")
        return
    df = pd.read_csv(path)
    if not df.empty and df.iloc[-1]['hora'] == dato['hora']:
        print(f"ℹ️  Dato {dato['hora']} ya existe. Omitiendo duplicado.")
        return
    pd.DataFrame([dato]).to_csv(path, mode='a', header=False, index=False)
    print(f"💾 CSV: {len(df) + 1} filas.")


def leer_csv():
    path = ARCHIVOS["csv"]
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    return df if not df.empty else None


def limpiar_csv():
    grupo     = GRUPOS_BONOS[GRUPO_ACTIVO]
    cabeceras = f"hora,{grupo['pesos']},{grupo['dolares']},mep\n"
    with open(ARCHIVOS["csv"], 'w') as f:
        f.write(cabeceras)
    print("🧹 CSV limpiado. Listo para mañana.")


# ═══════════════════════════════════════════════════════════════════
# SECCIÓN 4 — GENERACIÓN DEL GRÁFICO
# ═══════════════════════════════════════════════════════════════════

def generar_grafico(df: pd.DataFrame, estado: str = "Abierto") -> str:
    """
    Gráfico intradiario estilo TradingView (fondo oscuro).
    · Línea amarilla → bono en ARS (eje derecho)
    · Línea verde    → bono en USD (eje izquierdo)
    · Área roja      → MEP centrado (indicador de sensibilidad)
    """
    G     = GRAFICO
    grupo = GRUPOS_BONOS[GRUPO_ACTIVO]
    col_p = grupo["pesos"]
    col_d = grupo["dolares"]

    hoy_str = hora_ar().strftime("%d/%m/%Y")
    horas   = df['hora'].tolist()
    pesos   = df[col_p].tolist()
    dolares = df[col_d].tolist()
    mep     = df['mep'].tolist()
    x       = list(range(len(horas)))

    fig = plt.figure(figsize=G["figsize"], facecolor=G["bg"])
    ax1 = fig.add_subplot(111)
    ax1.set_facecolor(G["bg"])
    ax2 = ax1.twinx()
    ax2.set_facecolor(G["bg"])

    # Bono USD — eje izquierdo
    ax1.plot(x, dolares, color=G["color_dolares"], linewidth=G["lw_principal"], zorder=3)
    ax1.set_ylabel(f"{col_d}  u$s", color=G["color_dolares"], fontsize=10, labelpad=8)
    ax1.tick_params(axis='y', labelcolor=G["color_dolares"])

    # Bono ARS — eje derecho
    ax2.plot(x, pesos, color=G["color_pesos"], linewidth=G["lw_principal"], zorder=3)
    ax2.set_ylabel(f"{col_p}  $", color=G["color_pesos"], fontsize=10, labelpad=8)
    ax2.tick_params(axis='y', labelcolor=G["color_pesos"])

    # MEP como área centrada
    mep_arr   = np.array(mep)
    usd_arr   = np.array(dolares)
    mep_dev   = mep_arr - (mep_arr.max() + mep_arr.min()) / 2
    mid_usd   = (usd_arr.max() + usd_arr.min()) / 2
    rango_usd = max(usd_arr.max() - usd_arr.min(), 0.01)
    rango_mep = max(mep_arr.max() - mep_arr.min(), 0.01)
    mep_plot  = mid_usd + mep_dev * (rango_usd * 0.6 / rango_mep)
    mep_base  = np.full_like(mep_plot, mid_usd)

    ax1.fill_between(x, mep_base, mep_plot, color=G["color_mep"] + "55", alpha=0.65, zorder=2)
    ax1.plot(x, mep_plot, color=G["color_mep"], linewidth=G["lw_mep"],
             linestyle='--', alpha=0.9, zorder=2)
    ax1.axhline(y=mid_usd, color=G["color_mep"], linewidth=0.5, linestyle=':', alpha=0.4)

    # Grid y ejes
    ax1.grid(True, color=G["grid"], linewidth=0.7, alpha=0.8)
    ax1.set_axisbelow(True)
    step = max(1, len(horas) // 8)
    ax1.set_xticks(range(0, len(horas), step))
    ax1.set_xticklabels([horas[i] for i in range(0, len(horas), step)],
                        color=G["text"], fontsize=8)
    ax1.set_xlim(-0.5, len(horas) - 0.5)
    for ax in (ax1, ax2):
        for sp in ax.spines.values():
            sp.set_edgecolor(G["grid"])
        ax.tick_params(axis='x', colors=G["text"])

    # Título
    fig.suptitle(f"{grupo['label']}  —  {hoy_str}",
                 color=G["text"], fontsize=13, fontweight='bold', y=0.97)

    # Leyenda
    handles = [
        mpatches.Patch(color=G["color_dolares"], label=f"{col_d}  u$s {dolares[-1]:.2f}"),
        mpatches.Patch(color=G["color_pesos"],   label=f"{col_p}  ${pesos[-1]:,.0f}"),
        mpatches.Patch(color=G["color_mep"],     label=f"MEP  ${mep[-1]:,.0f}"),
    ]
    ax1.legend(handles=handles, loc='upper left', fontsize=8.5,
               facecolor='#1e2230', edgecolor=G["grid"],
               labelcolor=G["text"], framealpha=0.85)

    # Footer
    fig.text(
        0.5, 0.01,
        f"Rueda {horas[-1]}  ·  {col_p}: ${pesos[-1]:,.0f}  |  "
        f"{col_d}: u$s {dolares[-1]:.2f}  |  MEP: ${mep[-1]:,.0f}",
        ha='center', va='bottom', color=G["text"], fontsize=8.5,
        bbox=dict(boxstyle='round,pad=0.4', facecolor=G["footer_bg"],
                  edgecolor=G["grid"], alpha=0.9)
    )

    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    path = ARCHIVOS["grafico"]
    plt.savefig(path, dpi=G["dpi"], facecolor=G["bg"], bbox_inches='tight')
    plt.close()
    print(f"📊 Gráfico: {path}")
    return path


# ═══════════════════════════════════════════════════════════════════
# SECCIÓN 5 — ENVÍOS A TELEGRAM
# ═══════════════════════════════════════════════════════════════════

TOKEN   = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


def _tg_foto(img_path: str, caption: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    try:
        with open(img_path, 'rb') as f:
            resp = requests.post(
                url,
                data={'chat_id': CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'},
                files={'photo': f},
                timeout=30
            )
        print(f"{'📨' if resp.status_code == 200 else '⚠️ '} Telegram foto {resp.status_code}")
        if resp.status_code != 200:
            print(resp.text[:200])
    except Exception as e:
        print(f"⚠️  Excepción foto: {e}")


def _tg_texto(mensaje: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        resp = requests.post(
            url,
            json={'chat_id': CHAT_ID, 'text': mensaje, 'parse_mode': 'Markdown'},
            timeout=20
        )
        print(f"{'📨' if resp.status_code == 200 else '⚠️ '} Telegram texto {resp.status_code}")
        if resp.status_code != 200:
            print(resp.text[:200])
    except Exception as e:
        print(f"⚠️  Excepción texto: {e}")


def enviar_grafico_telegram(img_path: str, estado: str = "Abierto"):
    df   = leer_csv()
    grp  = GRUPOS_BONOS[GRUPO_ACTIVO]
    ts   = hhmm()
    hoy  = hora_ar().strftime("%d/%m/%Y")
    titulo = MENSAJES["mercado_abierto"] if estado == "Abierto" else MENSAJES["mercado_cerrado"]

    if df is not None:
        u = df.iloc[-1]
        caption = (
            f"{titulo} — {ts} AR\n📅 {hoy}\n\n"
            f"🔹 {grp['pesos']} (ARS):  `${u[grp['pesos']]:,.2f}`\n"
            f"🔹 {grp['dolares']} (USD): `u$s {u[grp['dolares']]:.2f}`\n"
            f"💵 MEP/{grp['pesos']}:    `${u['mep']:,.2f}`\n\n"
            f"_{MENSAJES['fuente_bonos']}_"
        )
    else:
        caption = f"{titulo} — {ts} AR"

    _tg_foto(img_path, caption)


# ═══════════════════════════════════════════════════════════════════
# SECCIÓN 6 — VISOR ARG
# ═══════════════════════════════════════════════════════════════════

def enviar_visor_arg():
    """
    Lee VISOR_ARG_TICKERS desde config.py.
    Descarga todos los tickers en una sola llamada a yfinance (eficiente).
    """
    try:
        import yfinance as yf
    except ImportError:
        print("⚠️  yfinance no instalado.")
        return

    ts = hhmm()
    print(f"📋 Visor ARG ({ts})...")

    tickers_list = list(VISOR_ARG_TICKERS.keys())
    datos_yf     = None

    try:
        # Una sola llamada para todos los tickers — mínimo consumo de red
        datos_yf = yf.download(
            tickers_list, period="1d", interval="1m",
            progress=False, auto_adjust=True, group_by='ticker'
        )
    except Exception as e:
        print(f"⚠️  Error descargando batch: {e}")

    lineas = [
        f"🇦🇷 *{MENSAJES['visor_arg_header']} — {ts} AR*",
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
    ]

    for ticker, (nombre, emo) in VISOR_ARG_TICKERS.items():
        try:
            if datos_yf is not None and len(tickers_list) > 1:
                precio = float(datos_yf[ticker]['Close'].dropna().iloc[-1])
                open_p = float(datos_yf[ticker]['Open'].dropna().iloc[0])
            else:
                fi     = yf.Ticker(ticker).fast_info
                precio = float(fi.last_price)
                open_p = float(fi.open)

            var   = ((precio - open_p) / open_p * 100) if open_p else 0.0
            color = "🟢" if var >= 0 else "🔴"
            signo = "+" if var >= 0 else ""
            lineas.append(f"{color} {emo} `{ticker:<7}` ${precio:.3f}   `{signo}{var:.2f}%`")

        except Exception as e:
            print(f"⚠️  {ticker}: {e}")
            lineas.append(f"▪️ `{ticker:<7}` ❌ Sin dato")

    lineas += ["▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", f"_{MENSAJES['fuente_acciones']}_"]
    _tg_texto("\n".join(lineas))


# ═══════════════════════════════════════════════════════════════════
# SECCIÓN 7 — LÓGICA PRINCIPAL (RELOJ INTELIGENTE)
# ═══════════════════════════════════════════════════════════════════

def main():
    ahora = hora_ar()
    ts    = hhmm(ahora)

    print(f"\n{'═'*52}")
    print(f"  monitor-a3  ·  {ahora.strftime('%Y-%m-%d  %H:%M:%S')} AR")
    print(f"{'═'*52}")

    # 1 · Día hábil
    if not es_dia_habil():
        sys.exit(0)

    # 2 · Fuera de horario
    if ts < "09:00" or ts > "18:05":
        print(f"⏰ Fuera de horario ({ts}).")
        sys.exit(0)

    # 3 · LIMPIAR CSV — 18:00
    if es_hora_exacta(HORARIOS["limpiar_csv"]) and not ya_se_envio("limpiar"):
        limpiar_csv()
        limpiar_estado()
        marcar_enviado("limpiar")
        sys.exit(0)

    # 4 · CAPTURAR PRECIO — 10:30 a 17:05
    if hora_entre(HORARIOS["apertura_mercado"], HORARIOS["cierre_captura"]):
        dato = capturar_precio()
        if dato:
            guardar_en_csv(dato)

    # 5 · GRÁFICO 12:00
    if es_hora_exacta(HORARIOS["grafico_1"]) and not ya_se_envio("grafico_1"):
        df = leer_csv()
        if df is not None:
            enviar_grafico_telegram(generar_grafico(df, "Abierto"), "Abierto")
            marcar_enviado("grafico_1")

    # 6 · VISOR ARG 13:00
    if es_hora_exacta(HORARIOS["visor_arg_1"]) and not ya_se_envio("visor_arg_1"):
        enviar_visor_arg()
        marcar_enviado("visor_arg_1")

    # 7 · GRÁFICO 15:00
    if es_hora_exacta(HORARIOS["grafico_2"]) and not ya_se_envio("grafico_2"):
        df = leer_csv()
        if df is not None:
            enviar_grafico_telegram(generar_grafico(df, "Abierto"), "Abierto")
            marcar_enviado("grafico_2")

    # 8 · VISOR ARG 15:30
    if es_hora_exacta(HORARIOS["visor_arg_2"]) and not ya_se_envio("visor_arg_2"):
        enviar_visor_arg()
        marcar_enviado("visor_arg_2")

    # 9 · GRÁFICO CIERRE 17:05
    if es_hora_exacta(HORARIOS["grafico_cierre"]) and not ya_se_envio("grafico_cierre"):
        df = leer_csv()
        if df is not None:
            enviar_grafico_telegram(generar_grafico(df, "Cerrado"), "Cerrado")
            marcar_enviado("grafico_cierre")

    # 10 · VISOR ARG 17:30
    if es_hora_exacta(HORARIOS["visor_arg_cierre"]) and not ya_se_envio("visor_arg_cierre"):
        enviar_visor_arg()
        marcar_enviado("visor_arg_cierre")

    print(f"✅ Completado — {hhmm()}")


if __name__ == "__main__":
    main()
