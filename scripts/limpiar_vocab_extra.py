"""Script de una sola corrida: limpia comas finales en los modelos de
data/vocab_extra.json (arrastradas desde configuracion.xlsx por un bug en
scripts/migrar_vocab_camiones.py, ya corregido) y fusiona WACKER dentro de
WACKER NEUSON (mismo bug de precedencia marca/alias ya corregido antes para
SINOTRUK/IVECO/PEREYRA en el commit 31d0c1d).

No es parte del pipeline -- se corre una vez, se revisa el diff de
vocab_extra.json, se commitea. Ver hallazgos 2 y 3 de la auditoría de datos
2026-07-09.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VOCAB_PATH = ROOT / "data" / "vocab_extra.json"


def main() -> None:
    vocab = json.loads(VOCAB_PATH.read_text(encoding="utf-8"))
    marcas = vocab["marcas"]

    comas_limpiadas = 0
    for marca, modelos in marcas.items():
        for i, m in enumerate(modelos):
            limpio = str(m).rstrip(",")
            if limpio != m:
                modelos[i] = limpio
                comas_limpiadas += 1

    # La coma limpiada puede dejar un modelo idéntico a otro que ya existía
    # sin coma en la misma lista (ej. "BJ4269SNFKB-1A," y "BJ4269SNFKB-1A"
    # coexistían) -- deduplicar preservando el orden de primera aparición.
    duplicados_removidos = 0
    for marca, modelos in marcas.items():
        vistos: set[str] = set()
        unicos = []
        for m in modelos:
            if m not in vistos:
                vistos.add(m)
                unicos.append(m)
            else:
                duplicados_removidos += 1
        marcas[marca] = unicos

    fusiones = 0
    if "WACKER" in marcas:
        destino = marcas.setdefault("WACKER NEUSON", [])
        vistos = set(destino)
        nuevos = [m for m in marcas["WACKER"] if m not in vistos]
        destino.extend(nuevos)
        fusiones = len(marcas.pop("WACKER"))

    VOCAB_PATH.write_text(
        json.dumps(vocab, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"Comas finales limpiadas: {comas_limpiadas}")
    print(f"Duplicados removidos tras limpiar comas: {duplicados_removidos}")
    print(f"Modelos de WACKER fusionados en WACKER NEUSON: {fusiones}")


if __name__ == "__main__":
    main()
