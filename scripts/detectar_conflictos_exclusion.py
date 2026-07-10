"""
scripts/detectar_conflictos_exclusion.py
══════════════════════════════════════════
Generaliza el hallazgo de "PICK UP" del 2026-07-08: un termino en
configuracion.xlsx hoja "excluir" (o en VANS_EXCLUIDAS) puede estar
descartando filas que caen en una partida que metodologia_descarga_mensual.md
documenta como camion legitimo a descargar -- exactamente lo que pasaba con
las pickups VW AMAROK/SAVEIRO en partida 8704211010/8704311010.

No decide automaticamente si el conflicto es un bug o una decision de
negocio (PICK UP resulto ser intencional) -- solo saca a la superficie los
candidatos para que el usuario decida, filtrando por volumen para no
generar ruido de 1-2 filas sueltas.

Solo lectura.

Uso:
  uv run python scripts/detectar_conflictos_exclusion.py
  uv run python scripts/detectar_conflictos_exclusion.py --min-filas 20
"""
from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SILVER_DIR = ROOT / "data" / "silver"

sys.path.insert(0, str(ROOT))
from pipeline.silver import PARTIDAS_CAMION  # noqa: E402


def cargar_excluidos_por_razon_carroceria_marca_texto() -> pd.DataFrame:
    """Filas excluidas por carroceria_excluida / marca_excluida / texto_excluido,
    con el termino especifico que causo la exclusion y la partida de la fila."""
    frames = []
    for f in sorted(glob.glob(str(SILVER_DIR / "*_qa.xlsx"))):
        try:
            df = pd.read_excel(f, sheet_name="_excluidos", dtype=str)
        except Exception:
            continue
        if "razon_exclusion" not in df.columns or "partida" not in df.columns:
            continue
        razon = df["razon_exclusion"].astype(str)
        mask = razon.str.startswith(("carroceria_excluida=", "marca_excluida=", "texto_excluido="))
        sub = df[mask].copy()
        if sub.empty:
            continue
        sub["tipo"] = razon[mask].str.split("=").str[0]
        sub["termino"] = razon[mask].str.split("=", n=1).str[1]
        frames.append(sub[["tipo", "termino", "partida"]])
    if not frames:
        return pd.DataFrame(columns=["tipo", "termino", "partida"])
    return pd.concat(frames, ignore_index=True)


def construir_tabla_conflictos(excl: pd.DataFrame, min_filas: int = 10) -> pd.DataFrame:
    """Agrupa las exclusiones por (tipo, termino) y devuelve solo las que caen en
    partidas documentadas como camión legítimo -- extraída de main() (2026-07-10)
    para reusarse desde el dashboard (shared/riesgos.py)."""
    filas = []
    for (tipo, termino), grupo in excl.groupby(["tipo", "termino"]):
        n = len(grupo)
        if n < min_filas:
            continue
        partidas = grupo["partida"].astype(str).value_counts()
        partidas_legitimas = {p: c for p, c in partidas.items() if p in PARTIDAS_CAMION}
        n_legitimas = sum(partidas_legitimas.values())
        if n_legitimas == 0:
            continue  # no cae en ninguna partida documentada como camion -- exclusion sin conflicto
        pct_legitimas = round(n_legitimas / n * 100, 1)
        filas.append({
            "tipo": tipo,
            "termino": termino,
            "filas_excluidas_total": n,
            "filas_en_partida_camion_legitima": n_legitimas,
            "pct_en_partida_legitima": pct_legitimas,
            "partidas_legitimas_afectadas": ", ".join(f"{p}({c})" for p, c in sorted(partidas_legitimas.items(), key=lambda x: -x[1])),
        })
    if not filas:
        return pd.DataFrame(columns=["tipo", "termino", "filas_excluidas_total",
                                      "filas_en_partida_camion_legitima",
                                      "pct_en_partida_legitima", "partidas_legitimas_afectadas"])
    return pd.DataFrame(filas).sort_values("filas_en_partida_camion_legitima", ascending=False)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-filas", type=int, default=10,
                     help="Ignorar terminos con menos de N filas excluidas (default 10)")
    args = ap.parse_args()

    print("Cargando exclusiones de silver...")
    excl = cargar_excluidos_por_razon_carroceria_marca_texto()
    if excl.empty:
        print("No se encontraron exclusiones por carroceria/marca/texto en los _qa.xlsx.")
        return 1

    tabla = construir_tabla_conflictos(excl, min_filas=args.min_filas)

    if tabla.empty:
        print("Sin conflictos detectados (ningun termino de exclusion cae en partidas de camion documentadas).")
        return 0

    pd.set_option("display.max_colwidth", None)
    pd.set_option("display.width", 220)
    print(f"\n{len(tabla)} termino(s) de exclusion con conflicto potencial "
          f"(caen en partidas documentadas como camion legitimo en metodologia_descarga_mensual.md):\n")
    print(tabla.to_string(index=False))
    print("\nOjo: esto NO significa que sean bugs -- solo candidatos a revisar. "
          "'PICK UP' aparece aca y ya se confirmo (2026-07-08) que es una exclusion intencional.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
