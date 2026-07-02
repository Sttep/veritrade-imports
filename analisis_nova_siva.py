"""
analisis_nova_siva.py  (v3 — inventario completo)
──────────────────────────────────────────────────
NOVA = NO VA  →  excluir
SIVA = SÍ VA  →  válidos

Genera un inventario COMPLETO de todos los valores únicos de CA: y MARCA:
encontrados en cada pestaña, sin filtrar por frecuencia.
Tú revisas y decides qué va a configuracion.xlsx.

Salida: outputs/analisis_nova_siva.xlsx
  → CA_inventario   : todos los valores CA: de NOVA y SIVA lado a lado
  → MARCA_inventario: todos los valores MARCA: de NOVA y SIVA lado a lado
  → NOVA_completo   : todos los campos extraídos fila por fila
  → SIVA_completo   : todos los campos extraídos fila por fila
"""

from __future__ import annotations
import argparse
import re
from collections import Counter
from pathlib import Path

import pandas as pd

RUTA_DEFAULT = Path("inputs/inforecogida/Primer 1/Data_recogida_intento_1.xlsx")
OUTPUT_DIR   = Path("outputs")

# Códigos Veritrade conocidos
CODIGOS = [
    "MARCA","MODELO","VERSION","AÑO MOD","AÑO","VI","VIN","CH","MO","CO","COMB",
    "C1","COLOR","NC","CC","PM","EJ","FR","TT","CA","AS","PA","PB","PN","CU",
    "LA","AN","AL","DE","KILOMETRAJE","KM","CLASIFICACION","CAJA","NR","NF",
    "SAC","SN","TE","SD","SP","PP","PE","VE",
]

_GROUP   = "|".join(re.escape(c) for c in sorted(CODIGOS, key=len, reverse=True))
_PATTERN = re.compile(
    rf"({_GROUP})\s*[:=]\s*(.*?)(?=\s*(?:{_GROUP})\s*[:=]|$)",
    re.IGNORECASE,
)


def extraer_campos(texto: str) -> dict[str, str]:
    if not isinstance(texto, str):
        return {}
    resultado: dict[str, str] = {}
    for m in _PATTERN.finditer(texto.upper()):
        cod   = m.group(1).strip().upper()
        valor = m.group(2).strip()
        if cod not in resultado and valor:
            resultado[cod] = valor
    return resultado


def extraer_prefijo(texto: str) -> str | None:
    """Texto libre antes del primer código (a menudo es la marca)."""
    if not isinstance(texto, str):
        return None
    texto_up = texto.upper().strip()
    texto_up = re.sub(r"^[LN][1-9]\s*[,\s]*", "", texto_up)
    m = _PATTERN.search(texto_up)
    if m and m.start() > 2:
        prefijo = texto_up[:m.start()].strip(" ,.")
        prefijo = re.sub(r"[,;]+", " ", prefijo).strip()
        if 1 < len(prefijo) < 50:
            return prefijo
    return None


def leer_hoja(xl: pd.ExcelFile, hoja: str) -> pd.Series:
    df      = xl.parse(hoja, header=None, dtype=str)
    primera = str(df.iloc[0, 0]) if len(df) > 0 else ""
    # Si la primera celda tiene códigos Veritrade, no hay header
    if re.search(r"\b(?:CA|MARCA|FR|CO|PM)\s*:", primera, re.I):
        return df.iloc[:, 0].dropna().astype(str).reset_index(drop=True)
    return df.iloc[1:, 0].dropna().astype(str).reset_index(drop=True)


def procesar_hoja(textos: pd.Series) -> pd.DataFrame:
    """Extrae todos los campos de cada descripción → DataFrame fila por fila."""
    rows = []
    for texto in textos:
        campos = extraer_campos(texto)
        prefijo = extraer_prefijo(texto)
        rows.append({
            "descripcion_original": texto,
            "prefijo_libre":        prefijo,
            "CA_carroceria":        campos.get("CA"),
            "MARCA":                campos.get("MARCA"),
            "MODELO":               campos.get("MODELO"),
            "FR_traccion":          campos.get("FR"),
            "CO_combustible":       campos.get("CO") or campos.get("COMB"),
            "PB_peso_bruto":        campos.get("PB"),
            "KM":                   campos.get("KM") or campos.get("KILOMETRAJE"),
            "TT_transmision":       campos.get("TT"),
            "AÑO_MODELO":           campos.get("AÑO MOD") or campos.get("AÑO"),
        })
    return pd.DataFrame(rows)


def inventario(serie: pd.Series, campo: str) -> pd.DataFrame:
    """Tabla de frecuencias de un campo — SIN filtro de frecuencia mínima."""
    cnt = Counter(v for v in serie.dropna() if str(v).strip())
    return pd.DataFrame(
        [{"valor": k, "frecuencia": v} for k, v in cnt.most_common()],
    )


def main(ruta: Path):
    OUTPUT_DIR.mkdir(exist_ok=True)

    if not ruta.exists():
        print(f"\n  ❌ No encontrado: {ruta.resolve()}")
        return 1

    xl = pd.ExcelFile(ruta)
    print(f"  Hojas: {xl.sheet_names}")

    if "NOVA" not in xl.sheet_names or "SIVA" not in xl.sheet_names:
        print(f"  ❌ Faltan NOVA y/o SIVA. Disponibles: {xl.sheet_names}")
        return 1

    textos_nova = leer_hoja(xl, "NOVA")
    textos_siva = leer_hoja(xl, "SIVA")
    print(f"\n  NOVA: {len(textos_nova):,} descripciones")
    print(f"  SIVA: {len(textos_siva):,} descripciones")

    # Extraer campos fila por fila
    print("  Extrayendo campos...")
    df_nova = procesar_hoja(textos_nova)
    df_siva = procesar_hoja(textos_siva)

    # Inventario completo de CA: y MARCA:
    inv_ca_nova   = inventario(df_nova["CA_carroceria"],  "CA").rename(columns={"valor":"CA","frecuencia":"frec_NOVA"})
    inv_ca_siva   = inventario(df_siva["CA_carroceria"],  "CA").rename(columns={"valor":"CA","frecuencia":"frec_SIVA"})
    inv_m_nova    = inventario(df_nova["MARCA"],          "MARCA").rename(columns={"valor":"MARCA","frecuencia":"frec_NOVA"})
    inv_m_siva    = inventario(df_siva["MARCA"],          "MARCA").rename(columns={"valor":"MARCA","frecuencia":"frec_SIVA"})
    inv_pref_nova = inventario(df_nova["prefijo_libre"],  "prefijo").rename(columns={"valor":"prefijo","frecuencia":"frec_NOVA"})
    inv_pref_siva = inventario(df_siva["prefijo_libre"],  "prefijo").rename(columns={"valor":"prefijo","frecuencia":"frec_SIVA"})

    # Cruzar NOVA y SIVA en una sola tabla para comparar
    ca_cruzado = (
        inv_ca_nova.merge(inv_ca_siva, on="CA", how="outer")
        .fillna(0)
        .assign(frec_NOVA=lambda d: d["frec_NOVA"].astype(int),
                frec_SIVA=lambda d: d["frec_SIVA"].astype(int))
        .assign(sugerencia=lambda d: d.apply(
            lambda r: "→ EXCLUIR"   if r["frec_NOVA"] > 0 and r["frec_SIVA"] == 0
            else      "→ VÁLIDO"    if r["frec_SIVA"] > 0 and r["frec_NOVA"] == 0
            else      "⚠ REVISAR",
            axis=1))
        .sort_values(["sugerencia","frec_NOVA","frec_SIVA"], ascending=[True,False,False])
        .reset_index(drop=True)
    )

    marca_cruzado = (
        inv_m_nova.merge(inv_m_siva, on="MARCA", how="outer")
        .fillna(0)
        .assign(frec_NOVA=lambda d: d["frec_NOVA"].astype(int),
                frec_SIVA=lambda d: d["frec_SIVA"].astype(int))
        .assign(sugerencia=lambda d: d.apply(
            lambda r: "→ EXCLUIR" if r["frec_NOVA"] > 0 and r["frec_SIVA"] == 0
            else      "→ VÁLIDO"  if r["frec_SIVA"] > 0 and r["frec_NOVA"] == 0
            else      "⚠ REVISAR",
            axis=1))
        .sort_values(["sugerencia","frec_NOVA","frec_SIVA"], ascending=[True,False,False])
        .reset_index(drop=True)
    )

    pref_cruzado = (
        inv_pref_nova.merge(inv_pref_siva, on="prefijo", how="outer")
        .fillna(0)
        .assign(frec_NOVA=lambda d: d["frec_NOVA"].astype(int),
                frec_SIVA=lambda d: d["frec_SIVA"].astype(int))
        .assign(sugerencia=lambda d: d.apply(
            lambda r: "→ EXCLUIR" if r["frec_NOVA"] > 0 and r["frec_SIVA"] == 0
            else      "→ VÁLIDO"  if r["frec_SIVA"] > 0 and r["frec_NOVA"] == 0
            else      "⚠ REVISAR",
            axis=1))
        .sort_values(["sugerencia","frec_NOVA","frec_SIVA"], ascending=[True,False,False])
        .reset_index(drop=True)
    )

    # Consola — resumen rápido
    excluir_ca = ca_cruzado[ca_cruzado["sugerencia"]=="→ EXCLUIR"]
    valido_ca  = ca_cruzado[ca_cruzado["sugerencia"]=="→ VÁLIDO"]
    revisar_ca = ca_cruzado[ca_cruzado["sugerencia"]=="⚠ REVISAR"]

    print("\n  ── CA: (carrocería) ─────────────────────────────────────────")
    print(f"  Solo en NOVA (→ excluir):  {len(excluir_ca)}")
    print(f"  Solo en SIVA (→ válido):   {len(valido_ca)}")
    print(f"  En ambas     (⚠ revisar):  {len(revisar_ca)}")

    print("\n  Muestra → EXCLUIR:")
    for _, r in excluir_ca.head(8).iterrows():
        print(f"    {r['CA']:<35} NOVA:{int(r['frec_NOVA']):>5}")

    print("\n  Muestra → VÁLIDO:")
    for _, r in valido_ca.head(8).iterrows():
        print(f"    {r['CA']:<35} SIVA:{int(r['frec_SIVA']):>5}")

    # Exportar
    out = OUTPUT_DIR / "analisis_nova_siva.xlsx"
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        ca_cruzado.to_excel(w,      sheet_name="CA_inventario",    index=False)
        marca_cruzado.to_excel(w,   sheet_name="MARCA_inventario", index=False)
        pref_cruzado.to_excel(w,    sheet_name="PREFIJO_inventario", index=False)
        df_nova.to_excel(w,         sheet_name="NOVA_completo",    index=False)
        df_siva.to_excel(w,         sheet_name="SIVA_completo",    index=False)

    print(f"\n  ✅ {out}")
    print(f"     CA_inventario    — {len(ca_cruzado)} valores únicos de carrocería")
    print(f"     MARCA_inventario — {len(marca_cruzado)} valores únicos de marca")
    print("     NOVA/SIVA_completo — extracción campo por campo\n")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ruta", default=str(RUTA_DEFAULT))
    args = ap.parse_args()
    raise SystemExit(main(Path(args.ruta)))