"""
scripts/reparar_anio_modelo.py
═══════════════════════════════════════
Repara el bug de parseo de "Año YYYY" colado dentro de `modelo` (ver
pipeline/silver.py::ANIO_SUELTO_PATTERN, corregido el 2026-07-08).

Contexto: algunas descripciones traen el año como texto libre ("Año 2026"
sin ":") en vez del código "AÑO MOD:2026". El parser viejo no reconocía el
límite de campo sin ":", así que el año quedaba pegado al final de `modelo`
(ej. "CARRYING PLUS,  AÑO 2023") y `anio_modelo` quedaba vacío. El fix en
silver.py ya corrige esto para archivos bronze nuevos, pero los .xlsx
crudos de los meses ya procesados (26 de 28 archivos silver) ya no están
en disco -- no se pueden reprocesar desde bronze.

Esta reparación re-extrae el año directamente desde la columna `modelo` ya
persistida en data/gold/camiones.parquet, sin necesitar el bronze original.

Alcance -- por qué es seguro tocar `modelo_match` sin pasar por el LLM:
Se verificó que el 100% de las filas afectadas tienen `modelo_flag ==
"reglas_alta"` (pipeline/gold.py:135-147): ese atajo determinístico copia
`modelo` de silver directo a `modelo_match` cuando `confianza == "ALTA"`,
sin invocar el LLM. O sea, para estas filas `modelo_match` YA ES una copia
literal de `modelo` -- limpiar `modelo` y reflejar el mismo valor limpio en
`modelo_match` reproduce exactamente lo que el pipeline produciría si se
re-corriera. Filas con otro `modelo_flag` (pasaron por LLM) que igual
tuvieran el patrón NO se tocan en `modelo_match` -- solo se limpia
`modelo`/`anio_modelo` y se marcan para revisión aparte (fase gold).

Uso:
  uv run python scripts/reparar_anio_modelo.py              # dry-run, solo reporta
  uv run python scripts/reparar_anio_modelo.py --apply       # escribe el fix en camiones.parquet
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PARQUET_PATH = ROOT / "data" / "gold" / "camiones.parquet"

# Cubre ambas variantes vistas en el crudo -- "AÑO 2026" y "AÑO MOD 2026"/
# "AÑO MOD.:2026" -- ancladas al final del valor de `modelo`, que es donde
# queda pegado el año suelto. Verificado contra los 499 valores únicos
# afectados en el repo: cobertura 100%. El caso raro de "AÑO FABR.:YYYY"
# seguido de "AÑO MOD.:YYYY" en la misma descripción (~8 filas) deja el
# "AÑO FABR." pegado en `modelo` a propósito -- ver nota en
# pipeline/silver.py::ANIO_MOD_SUELTO_PATTERN.
ANIO_COLADO_PATTERN = re.compile(
    r"^(?P<modelo>.*?)\s*,\s*A[ÑN]O\s*(?:MOD\.?|FABR\.?)?\s*[:.]?\s*(?P<anio>\d{4})\s*$",
    re.IGNORECASE,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                     help="Escribe el fix en data/gold/camiones.parquet (default: dry-run)")
    args = ap.parse_args()

    df = pd.read_parquet(PARQUET_PATH)
    modelo = df["modelo"].astype("string")

    extraido = modelo.str.extract(ANIO_COLADO_PATTERN)
    afectadas = extraido["modelo"].notna()

    n_afectadas = int(afectadas.sum())
    if n_afectadas == 0:
        print("No se encontraron filas con AÑO colado en `modelo`. Nada que reparar.")
        return 0

    modelo_limpio = extraido.loc[afectadas, "modelo"].str.strip()
    anio_extraido = extraido.loc[afectadas, "anio"].astype("Int64")

    # anio_modelo se persiste como string (dtype 'str' en este parquet, no numérico
    # -- formato dominante existente es "YYYY.0"). Solo completar donde está vacío,
    # sin pisar un valor real existente.
    anio_extraido_str = (anio_extraido.astype("string") + ".0")
    anio_actual = df.loc[afectadas, "anio_modelo"]
    anio_a_escribir = anio_actual.where(anio_actual.notna(), anio_extraido_str)
    n_anio_poblado = int((anio_actual.isna() & anio_extraido.notna()).sum())

    # modelo_match: solo se corrige donde el pipeline lo copió literal de
    # `modelo` sin pasar por LLM (modelo_flag == "reglas_alta"). Fuera de
    # ese caso, no se toca -- pasó por LLM y requiere revisión en fase gold.
    flag = df.loc[afectadas, "modelo_flag"].astype("string")
    match_es_copia_directa = (
        df.loc[afectadas, "modelo_match"].astype("string") == modelo.loc[afectadas]
    )
    tocar_modelo_match = afectadas.copy()
    tocar_modelo_match[afectadas] = (flag == "reglas_alta") & match_es_copia_directa
    n_modelo_match = int(tocar_modelo_match.sum())
    n_requiere_revision_gold = n_afectadas - n_modelo_match

    print(f"Filas con AÑO colado en `modelo`:            {n_afectadas:,}")
    print(f"  -> anio_modelo se completa (estaba vacío):  {n_anio_poblado:,}")
    print(f"  -> modelo_match se corrige (reglas_alta):   {n_modelo_match:,}")
    print(f"  -> requieren revisión en fase gold (LLM):   {n_requiere_revision_gold:,}")

    if n_requiere_revision_gold:
        print("\n  [AVISO] Estas filas pasaron por LLM y modelo_match no es una copia")
        print("  literal de modelo -- no se tocan acá. Revisar en el siguiente paso (gold).")
        print(df.loc[tocar_modelo_match.index[~tocar_modelo_match & afectadas],
                      ["marca_norm", "modelo", "modelo_match", "modelo_flag"]].head(10).to_string())

    if not args.apply:
        print("\nDry-run -- no se escribió nada. Volver a correr con --apply para aplicar el fix.")
        return 0

    df.loc[afectadas, "modelo"] = modelo_limpio
    df.loc[afectadas, "anio_modelo"] = anio_a_escribir
    df.loc[tocar_modelo_match, "modelo_match"] = modelo_limpio.loc[
        tocar_modelo_match[afectadas]
    ]

    df.to_parquet(PARQUET_PATH, index=False)
    print(f"\nEscrito: {PARQUET_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
