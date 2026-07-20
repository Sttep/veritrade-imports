"""Script de una sola corrida: migra marcas/modelos de camion desde
configuracion.xlsx (fuente ya curada, usada por silver.py) hacia
data/vocab_extra.json (vocabulario que ve el LLM en gold.py).

No es parte del pipeline — se corre una vez, se revisa el diff de
vocab_extra.json, se commitea. Ver plan de sesion 2026-07-08 (hallazgo #2:
el vocab del LLM solo tenia marcas de maquinaria, 0 de camion).
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "configuracion.xlsx"
VOCAB_PATH = ROOT / "data" / "vocab_extra.json"


def main() -> None:
    xl = pd.ExcelFile(CONFIG_PATH)
    marcas_df = xl.parse("marcas", dtype=str)
    modelos_df = xl.parse("modelos", dtype=str)

    marcas_norm = sorted(marcas_df["marca_normalizada"].dropna().str.strip().unique())

    # La columna "marca" del sheet modelos tiene variantes sucias (espacios,
    # comas colgantes) que colisionan con la marca limpia tras strip() — se
    # fusiona (no se sobreescribe) para no perder modelos de la variante
    # "correcta" cuando una variante sucia se procesa despues.
    modelos_df = modelos_df.copy()
    modelos_df["marca"] = modelos_df["marca"].astype(str).str.strip().str.rstrip(",")
    modelos_por_marca: dict[str, list[str]] = {}
    for marca, grupo in modelos_df.dropna(subset=["marca"]).groupby("marca"):
        vistos = set(modelos_por_marca.get(marca, []))
        nuevos = [
            m for m in sorted(grupo["modelo"].dropna().astype(str).str.strip().str.rstrip(",").unique())
            if m not in vistos
        ]
        modelos_por_marca.setdefault(marca, []).extend(nuevos)

    vocab = json.loads(VOCAB_PATH.read_text(encoding="utf-8"))

    agregadas, actualizadas = 0, 0
    for marca in marcas_norm:
        modelos = modelos_por_marca.get(marca, [])
        if marca not in vocab["marcas"]:
            vocab["marcas"][marca] = modelos
            agregadas += 1
        else:
            actuales = set(vocab["marcas"][marca])
            nuevos = [m for m in modelos if m not in actuales]
            if nuevos:
                vocab["marcas"][marca].extend(nuevos)
                actualizadas += 1

    VOCAB_PATH.write_text(
        json.dumps(vocab, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"Marcas en configuracion.xlsx: {len(marcas_norm)}")
    print(f"Marcas nuevas agregadas a vocab_extra.json: {agregadas}")
    print(f"Marcas existentes con modelos actualizados: {actualizadas}")
    print(f"Total marcas en vocab_extra.json ahora: {len(vocab['marcas'])}")


if __name__ == "__main__":
    main()
