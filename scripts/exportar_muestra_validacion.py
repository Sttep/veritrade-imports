"""
scripts/exportar_muestra_validacion.py
═══════════════════════════════════════
Exporta la muestra aleatoria para la validación manual descrita en la
sección 5 del informe de auditoría comercial (protocolo de muestreo:
95% de confianza, 5% de margen de error).

Semilla fija (42) para que la muestra sea reproducible si hace falta
volver a generarla o auditar el proceso.

Solo lectura sobre camiones.parquet -- escribe un .xlsx nuevo, no toca nada.

Uso:
  uv run python scripts/exportar_muestra_validacion.py
  uv run python scripts/exportar_muestra_validacion.py --n 500   # tamaño custom
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scripts.generar_informe_auditoria_comercial import (  # noqa: E402
    clasificar_segmento, normalizar_carroceria, _num,
)

SEMILLA = 42

COLUMNAS_EXPORT = [
    "dua_dam", "fecha_dua", "importador", "partida",
    "marca_declarada", "marca_norm",
    "modelo", "modelo_match",
    "carroceria", "carroceria_normalizada",
    "peso_bruto_desc", "kg_bruto_col",
    "vin", "chasis", "_descripcion",
]

COLUMNAS_VALIDACION = [
    "Categoría (calculada)", "Categoría Withmory (calculada)",
    "Marca OK? (S/N)", "Modelo OK? (S/N)", "Categoría OK? (S/N)",
    "Categoría Withmory OK? (S/N)", "Observaciones",
]


def tamano_muestra(n_total: int, z: float = 1.96, p: float = 0.5, e: float = 0.05) -> int:
    n = (z**2 * p * (1 - p)) / (e**2)
    n_ajustado = n / (1 + (n - 1) / n_total) if n_total else n
    return round(n_ajustado)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=None,
                     help="Tamaño de muestra (default: calculado con 95%% confianza / 5%% margen)")
    args = ap.parse_args()

    df = pd.read_parquet(ROOT / "data" / "gold" / "camiones.parquet")
    df = df[[c for c in COLUMNAS_EXPORT if c in df.columns]].copy()

    n = args.n or tamano_muestra(len(df))
    n = min(n, len(df))

    muestra = df.sample(n=n, random_state=SEMILLA).reset_index(drop=True)

    pb = _num(muestra["peso_bruto_desc"])
    muestra["Categoría (calculada)"] = muestra["carroceria_normalizada"].apply(normalizar_carroceria)
    muestra["Categoría Withmory (calculada)"] = pb.apply(clasificar_segmento)

    for col in ["Marca OK? (S/N)", "Modelo OK? (S/N)", "Categoría OK? (S/N)",
                "Categoría Withmory OK? (S/N)", "Observaciones"]:
        muestra[col] = ""

    orden_final = [c for c in COLUMNAS_EXPORT if c in muestra.columns] + \
                  ["Categoría (calculada)", "Categoría Withmory (calculada)",
                   "Marca OK? (S/N)", "Modelo OK? (S/N)", "Categoría OK? (S/N)",
                   "Categoría Withmory OK? (S/N)", "Observaciones"]
    muestra = muestra[orden_final]

    out_path = ROOT / "muestra_validacion_manual.xlsx"
    with pd.ExcelWriter(out_path, engine="openpyxl") as xw:
        muestra.to_excel(xw, sheet_name="muestra", index=False)
        resumen = pd.DataFrame([
            {"campo": "Fecha de exportación", "valor": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")},
            {"campo": "Filas totales en camiones.parquet", "valor": len(df)},
            {"campo": "Tamaño de muestra", "valor": n},
            {"campo": "Nivel de confianza", "valor": "95%"},
            {"campo": "Margen de error", "valor": "5%"},
            {"campo": "Semilla aleatoria (para reproducir)", "valor": SEMILLA},
            {"campo": "Instrucciones", "valor": "Para cada fila: abrir el DUA original en Veritrade "
                                                 "y comparar Marca/Modelo/Categoría/Categoría Withmory "
                                                 "contra las columnas '(calculada)'. Marcar S/N en las "
                                                 "columnas OK? y anotar el problema en Observaciones si "
                                                 "hay discrepancia."},
        ])
        resumen.to_excel(xw, sheet_name="instrucciones", index=False)

    print(f"Exportado: {out_path.name}")
    print(f"Muestra: {n} filas de {len(df):,} totales (95% confianza, 5% margen de error, semilla {SEMILLA})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
