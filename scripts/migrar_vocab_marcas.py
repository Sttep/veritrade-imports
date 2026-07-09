"""
scripts/migrar_vocab_marcas.py
═══════════════════════════════════════
Consolida en `data/vocab_extra.json` las mismas familias de marca que
scripts/migrar_config_marcas.py consolida en configuracion.xlsx, para que
las filas que sí pasan por el LLM (confianza != ALTA) también resuelvan a
marca_norm consolidado.

Bug real encontrado y corregido acá: Vocab.marca_canonica() (pipeline/llm/
vocab.py) revisa el índice de marcas (autoregistrado desde toda clave de
"marcas") ANTES que el índice de alias -- agregar un alias "HOWO":"SINOTRUK"
sin más no tiene efecto mientras "HOWO" siga siendo su propia clave de
"marcas". Por eso este script primero fusiona las listas de modelos de las
marcas redundantes dentro de la marca canónica, LUEGO borra esas claves de
"marcas", y recién ahí agrega el alias.

KAMA/KAMAZ no se tocan (decisión de negocio: son marcas distintas).

Uso:
  uv run python scripts/migrar_vocab_marcas.py              # dry-run, solo reporta
  uv run python scripts/migrar_vocab_marcas.py --apply       # escribe (con backup)
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VOCAB_PATH = ROOT / "data" / "vocab_extra.json"

# claves de "marcas" a fusionar dentro de la marca canónica y luego borrar
FUSIONAR_EN_SINOTRUK = [
    "HOWO", "SINOTRUK HOWO", "SITRAK", "WANGPAI", "SINOTRUK WANGPAI",
    "SINOTRUK HOMAN", "SINOTRUK SITRAK C7H", "HOMAN",
]
FUSIONAR_EN_IVECO = ["IVECO ASTRA"]

# aliases nuevos a agregar (raw -> canónico)
ALIASES_NUEVOS = {
    "HOWO": "SINOTRUK",
    "SITRAK": "SINOTRUK",
    "WANGPAI": "SINOTRUK",
    "SINOTRUK HOWO": "SINOTRUK",
    "SINOTRUK WANGPAI": "SINOTRUK",
    "HOMAN": "SINOTRUK",
    "HONAN": "SINOTRUK",
    "SINOTRUK HOMAN": "SINOTRUK",
    "SINOTRUK SITRAK C7H": "SINOTRUK",
    "IVECO ASTRA": "IVECO",
    "ASTRA": "IVECO",
    "PEREYRA": "CP PEREYRA",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                     help="Escribe los cambios en data/vocab_extra.json (default: dry-run)")
    args = ap.parse_args()

    v = json.loads(VOCAB_PATH.read_text(encoding="utf-8"))
    marcas = v["marcas"]
    aliases = v.setdefault("aliases", {})

    n_fusionadas = 0
    n_modelos_movidos = 0
    for clave, destino in [(k, "SINOTRUK") for k in FUSIONAR_EN_SINOTRUK] + \
                           [(k, "IVECO") for k in FUSIONAR_EN_IVECO]:
        if clave not in marcas:
            continue
        modelos_a_mover = marcas[clave]
        existentes = set(marcas[destino])
        nuevos = [m for m in modelos_a_mover if m not in existentes]
        marcas[destino] = marcas[destino] + nuevos
        n_modelos_movidos += len(nuevos)
        del marcas[clave]
        n_fusionadas += 1
        print(f"  fusionada: {clave} ({len(modelos_a_mover)} modelos) -> {destino} (+{len(nuevos)} nuevos)")

    n_aliases_nuevos = 0
    for raw, canon in ALIASES_NUEVOS.items():
        if raw not in aliases:
            n_aliases_nuevos += 1
        aliases[raw] = canon

    print(f"\nMarcas fusionadas/borradas: {n_fusionadas}")
    print(f"Modelos movidos (dedup): {n_modelos_movidos}")
    print(f"Aliases nuevos agregados: {n_aliases_nuevos} de {len(ALIASES_NUEVOS)}")
    print(f"SINOTRUK modelos final: {len(marcas.get('SINOTRUK', []))}")
    print(f"IVECO modelos final: {len(marcas.get('IVECO', []))}")

    if not args.apply:
        print("\nDry-run -- no se escribió nada. Volver a correr con --apply para aplicar.")
        return 0

    backup_path = VOCAB_PATH.with_suffix(".json.bak")
    shutil.copy2(VOCAB_PATH, backup_path)
    print(f"\nBackup: {backup_path}")

    VOCAB_PATH.write_text(
        json.dumps(v, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Escrito: {VOCAB_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
