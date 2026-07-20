"""
scripts/migrar_config_marcas.py
═══════════════════════════════════════
Consolida en `configuracion.xlsx` las familias de marca fragmentadas
detectadas en la sección 6 del informe de auditoría comercial:

- SINOTRUK: SINOTRUK, HOWO, HOWO MAX, SINOTRUK HOWO, SITRAK, WANGPAI,
  SINOTRUK WANGPAI, HOMAN, HONAN, SINOTRUK HONAN, SINOTRUK SITRAK C7H
  -> marca_normalizada=SINOTRUK
- IVECO: IVECO, IVECO ASTRA, ASTRA -> marca_normalizada=IVECO
- PEREYRA: PEREYRA -> CP PEREYRA (mismo actor comercial, nombre corto vs largo)

NOTA: SINOTRUK HOMAN y SINOTRUK SITRAK C7H se agregaron en un segundo paso
(2026-07-09) -- habian quedado corregidas en data/vocab_extra.json pero no
aca, mismo bug de raiz que las demas variantes Sinotruk. 0 filas afectadas
en camiones.parquet al momento del fix -- es preventivo para datos futuros.

KAMA/KAMAZ NO se tocan -- son probablemente marcas distintas (KAMAZ es un
fabricante ruso conocido), decisión de negocio confirmada explícitamente.

Toca dos hojas:
- `marcas` (marca_bruta -> marca_normalizada): actualiza filas existentes y
  agrega las que faltan (ASTRA, PEREYRA, HONAN, SINOTRUK HONAN).
- `modelos` (marca -> modelo): reetiqueta la columna `marca` en las filas de
  las familias de arriba, para que el catálogo de modelos conocidos no genere
  falsos "fuera de catálogo" una vez que marca_norm quede consolidado (ver
  scripts/generar_informe_auditoria_comercial.py sección 5).

La hoja `sinotruk` queda intacta en el archivo (no se borra, por si se quiere
auditar despues) pero pipeline/silver.py deja de leerla -- ver el fix
correspondiente en Config.

Uso:
  uv run python scripts/migrar_config_marcas.py              # dry-run, solo reporta
  uv run python scripts/migrar_config_marcas.py --apply       # escribe (con backup)
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "configuracion.xlsx"

# marca_bruta -> marca_normalizada nueva (filas existentes a actualizar)
MARCAS_UPDATE = {
    "HOWO": "SINOTRUK",
    "HOWO MAX": "SINOTRUK",
    "SINOTRUK HOWO": "SINOTRUK",
    "SITRAK": "SINOTRUK",
    "WANGPAI": "SINOTRUK",
    "SINOTRUK WANGPAI": "SINOTRUK",
    "HOMAN": "SINOTRUK",
    "IVECO ASTRA": "IVECO",
    "SINOTRUK HOMAN": "SINOTRUK",
    "SINOTRUK SITRAK C7H": "SINOTRUK",
}

# marca_bruta -> marca_normalizada nueva (filas ausentes hoy, a agregar)
MARCAS_NUEVAS = {
    "ASTRA": "IVECO",
    "PEREYRA": "CP PEREYRA",
    "HONAN": "SINOTRUK",
    "SINOTRUK HONAN": "SINOTRUK",
}

# marca vieja -> marca nueva, para la hoja `modelos`
MODELOS_RELABEL = {
    "HOWO": "SINOTRUK",
    "SITRAK": "SINOTRUK",
    "WANGPAI": "SINOTRUK",
    "SINOTRUK HOWO": "SINOTRUK",
    "SINOTRUK WANGPAI": "SINOTRUK",
    "HOMAN": "SINOTRUK",
    "ASTRA": "IVECO",
    "IVECO ASTRA": "IVECO",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                     help="Escribe los cambios en configuracion.xlsx (default: dry-run)")
    args = ap.parse_args()

    if not CONFIG_PATH.exists():
        print(f"No se encontró {CONFIG_PATH}")
        return 1

    xl = pd.ExcelFile(CONFIG_PATH)
    sheets = {name: xl.parse(name, dtype=str) for name in xl.sheet_names}

    marcas = sheets["marcas"]
    modelos = sheets["modelos"]

    # --- marcas: actualizar filas existentes ---
    n_actualizadas = 0
    for bruta, nueva in MARCAS_UPDATE.items():
        mask = marcas["marca_bruta"] == bruta
        actual = marcas.loc[mask, "marca_normalizada"]
        if len(actual) and actual.iloc[0] != nueva:
            n_actualizadas += 1
        marcas.loc[mask, "marca_normalizada"] = nueva

    # --- marcas: agregar filas nuevas ---
    filas_nuevas = []
    for bruta, nueva in MARCAS_NUEVAS.items():
        if not (marcas["marca_bruta"] == bruta).any():
            filas_nuevas.append({"marca_bruta": bruta, "marca_normalizada": nueva})
    if filas_nuevas:
        marcas = pd.concat([marcas, pd.DataFrame(filas_nuevas)], ignore_index=True)

    # --- modelos: reetiquetar columna marca ---
    n_modelos_afectados = modelos["marca"].isin(MODELOS_RELABEL.keys()).sum()
    modelos["marca"] = modelos["marca"].replace(MODELOS_RELABEL)

    print(f"Hoja 'marcas': {n_actualizadas} filas actualizadas, {len(filas_nuevas)} filas nuevas")
    for f in filas_nuevas:
        print(f"  + {f['marca_bruta']} -> {f['marca_normalizada']}")
    print(f"Hoja 'modelos': {n_modelos_afectados} filas reetiquetadas")
    print(modelos.loc[modelos["marca"].isin(["SINOTRUK", "IVECO"]), "marca"].value_counts())

    if not args.apply:
        print("\nDry-run -- no se escribió nada. Volver a correr con --apply para aplicar.")
        return 0

    backup_path = CONFIG_PATH.with_suffix(".xlsx.bak")
    shutil.copy2(CONFIG_PATH, backup_path)
    print(f"\nBackup: {backup_path}")

    sheets["marcas"] = marcas
    sheets["modelos"] = modelos
    with pd.ExcelWriter(CONFIG_PATH, engine="openpyxl") as xw:
        for name, df in sheets.items():
            df.to_excel(xw, sheet_name=name, index=False)

    print(f"Escrito: {CONFIG_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
