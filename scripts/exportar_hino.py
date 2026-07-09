"""
scripts/exportar_hino.py
═══════════════════════════════════════
Exporta todas las filas de marca_norm=HINO en data/gold/camiones.parquet a un
xlsx para revisión, con contexto de los 2 hallazgos ya conocidos del informe
de auditoría comercial (informe_auditoria_comercial.md, secciones 4 y 5):

- "HINO STANDARD" (1,290 filas) queda fuera del catálogo conocido
  (configuracion.xlsx hoja "modelos") -- puede ser un modelo legítimo no
  agregado aún, no necesariamente un error.
- 3,853 de 3,863 filas HINO no tienen peso_bruto_desc porque el código
  "PB:" nunca aparece en la descripción comercial cruda -- no es un bug del
  parser, es un vacío del dato de origen.

Solo lectura sobre camiones.parquet -- escribe un .xlsx nuevo, no toca nada.

Uso:
  uv run python scripts/exportar_hino.py
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

COLUMNAS_EXPORT = [
    "dua_dam", "fecha_dua", "importador", "partida",
    "marca_declarada", "marca_norm",
    "modelo", "modelo_match",
    "carroceria", "carroceria_normalizada",
    "peso_bruto_desc", "kg_bruto_col",
    "vin", "chasis", "_descripcion",
]


def main() -> int:
    df = pd.read_parquet(ROOT / "data" / "gold" / "camiones.parquet")

    marca = df["marca_norm"].astype("string").str.upper().str.strip()
    hino = df[marca == "HINO"][[c for c in COLUMNAS_EXPORT if c in df.columns]].copy()

    pb = pd.to_numeric(hino["peso_bruto_desc"], errors="coerce") if "peso_bruto_desc" in hino.columns else pd.Series(dtype=float)
    n_sin_pb = int(pb.isna().sum())
    n_standard = int((hino["modelo_match"].astype("string").str.upper().str.strip() == "STANDARD").sum()) \
        if "modelo_match" in hino.columns else 0

    out_path = ROOT / "hino.xlsx"
    with pd.ExcelWriter(out_path, engine="openpyxl") as xw:
        hino.to_excel(xw, sheet_name="hino", index=False)
        resumen = pd.DataFrame([
            {"campo": "Fecha de exportación", "valor": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")},
            {"campo": "Filas totales HINO", "valor": len(hino)},
            {"campo": "Filas totales camiones.parquet", "valor": len(df)},
            {"campo": "Hallazgo 1", "valor": f"HINO STANDARD: {n_standard} filas fuera del catálogo "
                                              "conocido (configuracion.xlsx hoja 'modelos'). No implica "
                                              "error -- puede ser un modelo legítimo no agregado aún."},
            {"campo": "Hallazgo 2", "valor": f"{n_sin_pb} de {len(hino)} filas ({n_sin_pb/len(hino)*100:.1f}%) "
                                              "sin peso_bruto_desc -- confirmado que el código 'PB:' nunca "
                                              "aparece en la descripción comercial cruda de esas filas. No "
                                              "es un bug del parser, es un vacío del dato de origen."},
            {"campo": "Instrucciones", "valor": "Estos 2 hallazgos ya están investigados y documentados en "
                                                 "informe_auditoria_comercial.md (secciones 4 y 5) -- no hace "
                                                 "falta re-derivarlos, solo tenerlos de contexto al revisar."},
        ])
        resumen.to_excel(xw, sheet_name="resumen", index=False)

    print(f"Exportado: {out_path.name}")
    print(f"HINO: {len(hino):,} filas de {len(df):,} totales")
    print(f"  Sin peso_bruto_desc: {n_sin_pb:,} ({n_sin_pb/len(hino)*100:.1f}%)")
    print(f"  HINO STANDARD (fuera de catálogo): {n_standard:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
