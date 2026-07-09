"""
scripts/validar_diccionarios.py
═════════════════════════════════
Valida consistencia entre los dos catálogos de marca que usa el pipeline
-- `configuracion.xlsx` (hoja "marcas", camino determinístico de silver.py)
y `data/vocab_extra.json` (camino LLM de gold.py, vía pipeline/llm/vocab.py)
-- más consistencia interna de cada uno. Complementa a
scripts/validar_calidad_datos.py (que valida filas, no catálogos).

Solo lectura -- no modifica configuracion.xlsx, vocab_extra.json ni
ningún parquet.

Uso:
  uv run python scripts/validar_diccionarios.py
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "configuracion.xlsx"
VOCAB_PATH = ROOT / "data" / "vocab_extra.json"
PARQUET_PATH = ROOT / "data" / "gold" / "camiones.parquet"
INFORME_PATH = ROOT / "informe_diccionarios.md"

sys.path.insert(0, str(ROOT))


def _resultado(titulo: str, hallazgos: list[str], nota: str | None = None, max_ejemplos: int = 20) -> dict:
    lines = [f"### {titulo}"]
    if nota:
        lines.append(f"- {nota}")
    lines.append(f"- Hallazgos: {len(hallazgos):,}")
    if not hallazgos:
        lines.append("- Sin hallazgos")
    else:
        for h in hallazgos[:max_ejemplos]:
            lines.append(f"  - {h}")
        if len(hallazgos) > max_ejemplos:
            lines.append(f"  - ... y {len(hallazgos) - max_ejemplos:,} más")
    lines.append("")
    return {"titulo": titulo, "n": len(hallazgos), "md": "\n".join(lines)}


def check_reglas_vs_llm(marcas_cfg: pd.DataFrame, vocab) -> dict:
    titulo = "Marca con resultado distinto según pase por reglas (silver) o LLM (gold)"
    hallazgos = []
    for _, row in marcas_cfg.dropna(subset=["marca_bruta"]).iterrows():
        bruta = str(row["marca_bruta"]).strip()
        norm_reglas = str(row.get("marca_normalizada") or bruta).strip().upper()
        norm_llm = vocab.marca_canonica(bruta)
        if norm_llm and norm_llm.strip().upper() != norm_reglas:
            hallazgos.append(f"{bruta}: reglas→{norm_reglas} vs LLM→{norm_llm.strip().upper()}")
    nota = ("Estas marcas normalizan distinto según el camino que tome la fila (confianza=ALTA "
            "usa reglas, confianza=BAJA pasa por LLM) -- resultado inconsistente para el mismo "
            "texto declarado.")
    return _resultado(titulo, hallazgos, nota)


def check_precedencia_alias(vocab_json: dict) -> dict:
    titulo = "Bug de precedencia: marca es clave de 'marcas' Y de 'aliases' (el alias nunca se aplica)"
    marcas = set(vocab_json.get("marcas", {}).keys())
    hallazgos = []
    for alias, canon in vocab_json.get("aliases", {}).items():
        if alias in marcas and alias.strip().upper() != str(canon).strip().upper():
            hallazgos.append(f"{alias!r} -> {canon!r} (pero {alias!r} sigue siendo su propia "
                              f"marca en 'marcas', Vocab._marca_idx la resuelve antes que el alias)")
    nota = ("Mismo bug corregido para SINOTRUK/IVECO/PEREYRA en 2026-07-08 -- "
            "Vocab.marca_canonica() revisa _marca_idx antes que _alias_idx.")
    return _resultado(titulo, hallazgos, nota)


def check_marcas_huerfanas(df: pd.DataFrame, marcas_cfg: pd.DataFrame, vocab_json: dict) -> dict:
    titulo = "marca_norm en camiones.parquet ausente de ambos catálogos"
    validas_cfg = set(marcas_cfg["marca_normalizada"].dropna().astype(str).str.upper().str.strip())
    validas_vocab = {k.strip().upper() for k in vocab_json.get("marcas", {})} | \
        {str(v).strip().upper() for v in vocab_json.get("aliases", {}).values()}
    mn = df["marca_norm"].astype("string").str.upper().str.strip()
    conteo = mn.value_counts()
    hallazgos = [
        f"{marca}: {n:,} filas"
        for marca, n in conteo.items()
        if marca not in validas_cfg and marca not in validas_vocab
    ]
    nota = "Marcas resueltas 100% por inferencia del LLM, sin ningún catálogo local contra el cual validarlas."
    return _resultado(titulo, hallazgos, nota)


def check_duplicados_marcas_cfg(marcas_cfg: pd.DataFrame) -> dict:
    titulo = "marca_bruta repetida con distinto marca_normalizada en hoja 'marcas'"
    grp = marcas_cfg.dropna(subset=["marca_bruta"]).groupby("marca_bruta")["marca_normalizada"].nunique()
    hallazgos = [f"{m}: {n} valores distintos" for m, n in grp[grp > 1].items()]
    return _resultado(titulo, hallazgos)


def check_modelos_duplicados_vocab(vocab_json: dict) -> dict:
    titulo = "Modelos duplicados dentro de una misma marca en vocab_extra.json"
    hallazgos = []
    for marca, modelos in vocab_json.get("marcas", {}).items():
        vistos = set()
        dup = set()
        for m in modelos or []:
            if m in vistos:
                dup.add(m)
            vistos.add(m)
        if dup:
            hallazgos.append(f"{marca}: {sorted(dup)}")
    return _resultado(titulo, hallazgos)


def main() -> int:
    if not CONFIG_PATH.exists():
        print(f"No se encontró {CONFIG_PATH}")
        return 1
    if not VOCAB_PATH.exists():
        print(f"No se encontró {VOCAB_PATH}")
        return 1

    marcas_cfg = pd.ExcelFile(CONFIG_PATH).parse("marcas", dtype=str)
    vocab_json = json.loads(VOCAB_PATH.read_text(encoding="utf-8"))

    from pipeline.llm.vocab import load as cargar_vocab
    vocab = cargar_vocab()

    df = pd.read_parquet(PARQUET_PATH) if PARQUET_PATH.exists() else pd.DataFrame(columns=["marca_norm"])

    resultados = [
        check_reglas_vs_llm(marcas_cfg, vocab),
        check_precedencia_alias(vocab_json),
        check_marcas_huerfanas(df, marcas_cfg, vocab_json),
        check_duplicados_marcas_cfg(marcas_cfg),
        check_modelos_duplicados_vocab(vocab_json),
    ]

    for r in resultados:
        print(r["md"])

    total_hallazgos = sum(r["n"] for r in resultados)
    resumen = (
        "| Check | Hallazgos |\n|---|---|\n"
        + "\n".join(f"| {r['titulo']} | {r['n']:,} |" for r in resultados)
    )
    print(resumen)

    fecha = date.today().isoformat()
    cuerpo = (
        "# Auditoría de Diccionarios y Catálogos — Veritrade Imports\n"
        f"**Fecha:** {fecha}\n"
        f"**Fuentes:** `configuracion.xlsx` (hoja \"marcas\"), `data/vocab_extra.json`, "
        f"`data/gold/camiones.parquet` ({len(df):,} filas)\n\n"
        "---\n\n"
        f"## Resumen\n\n- **Total hallazgos:** {total_hallazgos:,}\n\n---\n\n"
        + "\n".join(r["md"] for r in resultados)
        + "\n---\n\n## Resumen\n\n" + resumen + "\n"
    )
    INFORME_PATH.write_text(cuerpo, encoding="utf-8")
    print(f"\nInforme escrito: {INFORME_PATH.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
