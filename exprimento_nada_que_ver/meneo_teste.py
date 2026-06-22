"""
Meta Ads Insights Downloader
============================
Descarga datos de Ads Manager via API sin depender del export manual.
Soporta breakdowns de age/gender y desglose diario.

Requisitos:
    pip install requests pandas openpyxl

Cómo obtener tu Access Token:
    1. Ve a https://developers.facebook.com/tools/explorer/
    2. Selecciona tu app de negocio (o crea una en developers.facebook.com)
    3. Agrega permisos: ads_read, read_insights
    4. Genera el token y pégalo abajo
    Nota: los tokens de usuario expiran en ~60 días.
    Para producción, usa un System User Token desde Meta Business Settings.
"""

import requests
import pandas as pd
import time
from datetime import datetime

# ─────────────────────────────────────────
# CONFIGURACIÓN — edita estos valores
# ─────────────────────────────────────────

ACCESS_TOKEN = "TOKEN_DE_ACCESO_AQUI"  # Reemplaza con tu token real

ACCOUNT_ID   = "1331797103822666"   # sin el "act=" prefix
AD_IDS       = ["120247361128520182"]  # puedes agregar más IDs separados por coma

DATE_START   = "2025-08-01"
DATE_END     = "2026-06-21"

# Métricas a descargar (agrega o quita según necesites)
FIELDS = [
    "ad_id",
    "ad_name",
    "adset_name",
    "campaign_name",
    "date_start",
    "date_stop",
    "impressions",
    "reach",
    "clicks",
    "unique_clicks",
    "spend",
    "cpm",
    "cpc",
    "ctr",
    "frequency",
    "actions",          # conversiones, mensajes, etc.
    "cost_per_action_type",
]

BREAKDOWNS   = ["age", "gender"]  # quita si no necesitas demografía
TIME_INCREMENT = 1                  # 1 = diario | "monthly" | "all_days"

API_VERSION  = "v19.0"
OUTPUT_FILE  = f"meta_insights_{DATE_START}_{DATE_END}.xlsx"

# ─────────────────────────────────────────
# FUNCIONES PRINCIPALES
# ─────────────────────────────────────────

def build_params(ad_id: str) -> dict:
    return {
        "fields": ",".join(FIELDS),
        "time_range": f'{{"since":"{DATE_START}","until":"{DATE_END}"}}',
        "time_increment": TIME_INCREMENT,
        "breakdowns": ",".join(BREAKDOWNS) if BREAKDOWNS else None,
        "level": "ad",
        "filtering": f'[{{"field":"ad.id","operator":"IN","value":["{ad_id}"]}}]',
        "limit": 500,  # máximo por página
        "access_token": ACCESS_TOKEN,
    }


def fetch_all_pages(url: str, params: dict) -> list[dict]:
    """Maneja paginación automáticamente."""
    all_data = []
    page_num = 1

    while url:
        print(f"  → Página {page_num}...", end=" ")
        response = requests.get(url, params=params if page_num == 1 else {})
        
        if response.status_code != 200:
            print(f"\n❌ Error {response.status_code}: {response.text}")
            break

        result = response.json()

        if "error" in result:
            print(f"\n❌ Error de API: {result['error']['message']}")
            break

        data = result.get("data", [])
        all_data.extend(data)
        print(f"{len(data)} filas")

        # Siguiente página
        paging = result.get("paging", {})
        url = paging.get("next")
        params = {}  # la URL "next" ya incluye todos los params
        page_num += 1

        # Respeto rate limits de Meta (600 puntos/hora por app)
        if url:
            time.sleep(0.5)

    return all_data


def flatten_actions(row: dict) -> dict:
    """
    Convierte la columna 'actions' de lista a columnas individuales.
    Ej: actions=[{"action_type":"link_click","value":"5"}]
        → action_link_click: 5
    """
    actions = row.pop("actions", []) or []
    for action in actions:
        col = f"action_{action['action_type']}"
        row[col] = int(action.get("value", 0))

    cost_actions = row.pop("cost_per_action_type", []) or []
    for ca in cost_actions:
        col = f"cpa_{ca['action_type']}"
        row[col] = float(ca.get("value", 0))

    return row


def download_insights() -> pd.DataFrame:
    all_rows = []

    for ad_id in AD_IDS:
        print(f"\n📥 Descargando Ad ID: {ad_id}")
        url = f"https://graph.facebook.com/{API_VERSION}/act_{ACCOUNT_ID}/insights"
        params = build_params(ad_id)

        rows = fetch_all_pages(url, params)
        rows = [flatten_actions(r) for r in rows]
        all_rows.extend(rows)
        print(f"  ✅ Total filas para este ad: {len(rows)}")

    if not all_rows:
        print("\n⚠️  No se obtuvieron datos. Verifica el token y permisos.")
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)

    # Tipado de columnas numéricas
    numeric_cols = ["impressions", "reach", "clicks", "unique_clicks",
                    "spend", "cpm", "cpc", "ctr", "frequency"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["date_start"] = pd.to_datetime(df["date_start"])
    df["spend"]      = df["spend"].round(2)

    return df


def export_to_excel(df: pd.DataFrame):
    """Exporta con formato: una hoja principal + resumen por mes."""
    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:

        # Hoja 1: Datos completos
        df.to_excel(writer, sheet_name="Detalle Diario", index=False)

        # Hoja 2: Resumen mensual por género y edad
        if "age" in df.columns and "gender" in df.columns:
            resumen = (
                df.assign(mes=df["date_start"].dt.to_period("M"))
                .groupby(["mes", "age", "gender"], as_index=False)
                .agg(
                    impresiones=("impressions", "sum"),
                    alcance=("reach", "sum"),
                    clics=("clicks", "sum"),
                    gasto_usd=("spend", "sum"),
                    cpm_prom=("cpm", "mean"),
                    ctr_prom=("ctr", "mean"),
                )
            )
            resumen["mes"] = resumen["mes"].astype(str)
            resumen["gasto_usd"] = resumen["gasto_usd"].round(2)
            resumen["cpm_prom"]  = resumen["cpm_prom"].round(2)
            resumen["ctr_prom"]  = resumen["ctr_prom"].round(4)
            resumen.to_excel(writer, sheet_name="Resumen Mensual", index=False)

        # Hoja 3: Totales por ad
        totales = (
            df.groupby(["ad_id", "ad_name"], as_index=False)
            .agg(
                impresiones=("impressions", "sum"),
                alcance=("reach", "sum"),
                clics=("clicks", "sum"),
                gasto_total_usd=("spend", "sum"),
            )
        )
        totales.to_excel(writer, sheet_name="Totales por Ad", index=False)

    print(f"\n💾 Archivo guardado: {OUTPUT_FILE}")
    print(f"   Filas totales: {len(df):,}")
    print(f"   Rango: {df['date_start'].min().date()} → {df['date_start'].max().date()}")


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("Meta Ads Insights Downloader")
    print(f"Período: {DATE_START} → {DATE_END}")
    print(f"Ads: {AD_IDS}")
    print("=" * 50)

    if ACCESS_TOKEN == "PEGA_TU_TOKEN_AQUI":
        print("\n⛔ ERROR: Reemplaza ACCESS_TOKEN con tu token real antes de ejecutar.")
        exit(1)

    start = datetime.now()
    df = download_insights()

    if not df.empty:
        export_to_excel(df)
        elapsed = (datetime.now() - start).seconds
        print(f"⏱️  Tiempo total: {elapsed}s")