"""Test de regresion: contrato Silver -> Gold sobre la columna 'confianza'.

Ejecuta pipeline.gold.process_file() de punta a punta (con --dry-run, sin
llamar a la API real) sobre un silver sintetico con 4 variantes de la columna
de confianza, y verifica el comportamiento OBSERVABLE resultante -- no solo
que una cadena aparezca en el codigo fuente. Ver liz-4ca (bd) para el contexto
del bug historico (ya corregido en commit 3e57311, 2026-07-08).
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.gold import process_file  # noqa: E402
from pipeline.llm import vocab as vocab_mod  # noqa: E402
from pipeline.llm.cache import Cache  # noqa: E402


@pytest.fixture
def gold_scratch_dir():
    """gold_dir debe quedar bajo ROOT: process_file hace out_path.relative_to(ROOT)
    en su ultima linea y lanza ValueError si gold_dir esta fuera del repo (bug
    aparte, sin relacion con este test, encontrado durante la investigacion de
    liz-4ca -- no se corrige aca, fuera de alcance)."""
    d = ROOT / "tests" / "_tmp_gold_confianza_test"
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    yield d
    shutil.rmtree(d, ignore_errors=True)


def test_contrato_confianza_silver_gold(tmp_path, gold_scratch_dir):
    """Silver escribe la columna 'confianza' (alta/baja). Gold debe:

    - confianza='alta' -> atajo deterministico (fuente='Reglas (Silver)'), sin LLM.
    - confianza='baja' -> rama LLM/cache (fuente empieza con 'LLM_Hibrido').
    - columna 'confianza' ausente -> se comporta como baja (falla seguro, no
      toma el atajo por error).
    - solo 'confianza_clasificacion' presente (nombre viejo, pre-3e57311) ->
      tambien debe comportarse como baja. Si Gold volviera a leer ese nombre
      viejo en vez de 'confianza', esta fila tomaria el atajo por error y el
      assert de mas abajo fallaria.
    """
    filas = [
        {"dua_dam": "1", "vin": "V1", "_descripcion": "DESCRIPCION UNO", "confianza": "alta"},
        {"dua_dam": "2", "vin": "V2", "_descripcion": "DESCRIPCION DOS", "confianza": "baja"},
        {"dua_dam": "3", "vin": "V3", "_descripcion": "DESCRIPCION TRES"},
        {"dua_dam": "4", "vin": "V4", "_descripcion": "DESCRIPCION CUATRO",
         "confianza_clasificacion": "alta"},
    ]
    silver_path = tmp_path / "silver_test_fase1.parquet"
    pd.DataFrame(filas).to_parquet(silver_path)

    cache = Cache(path=tmp_path / "cache_test.jsonl")
    v = vocab_mod.load()  # vocab_extra.json real, no golpea la red
    args = SimpleNamespace(sample=0, all=True, dry_run=True, model=None,
                            batch_size=10, workers=4)

    ok = process_file(
        bronze_path=Path("dummy_no_se_lee.xlsx"),
        silver_path=silver_path,
        gold_dir=gold_scratch_dir,
        stem="silver_test",
        v=v,
        cache=cache,
        args=args,
    )
    assert ok

    out = pd.read_parquet(gold_scratch_dir / "silver_test_normalizado.parquet").set_index("dua_dam")

    assert out.loc["1", "fuente"] == "Reglas (Silver)"
    assert out.loc["1", "modelo_flag"] == "reglas_alta"

    assert out.loc["2", "fuente"].startswith("LLM_Hibrido")

    assert out.loc["3", "fuente"].startswith("LLM_Hibrido"), (
        "Fila sin columna 'confianza' tomo el atajo deterministico -- "
        "el contrato Silver->Gold se rompio (deberia ir a la rama LLM/cache)."
    )

    assert out.loc["4", "fuente"].startswith("LLM_Hibrido"), (
        "Fila con solo 'confianza_clasificacion' (nombre viejo) tomo el atajo "
        "deterministico -- Gold volvio a buscar la columna vieja en vez de 'confianza'."
    )
