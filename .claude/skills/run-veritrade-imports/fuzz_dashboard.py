"""
fuzz_dashboard.py -- fuzzer adversarial para el dashboard Streamlit
(pages/2_Camiones.py por default). Prueba automáticamente muchas
combinaciones de widgets vía AppTest (headless, sin servidor/navegador) y
reporta cualquier combinación que produzca una excepción sin capturar.

Tres pasadas, todas registradas:
  1. Barrido de un solo factor: cada widget, cada valor posible (recorta a
     --max-opciones por widget para no explotar en selects con muchas
     opciones), el resto en default. Encuentra la mayoría de los crashes
     de un solo causante.
  2. Combos adversariales a mano: rango de fechas invertido, Marca A ==
     Marca B, Vista=Sinotruk + filtro de carrocería vacío, etc.
  3. --random-n combos aleatorios de varios widgets a la vez, para agarrar
     interacciones entre factores que el barrido de a uno no ve.

Cada AppTest se reinstancia desde cero en cada prueba (no se reusa la misma
instancia entre casos) para que un crash en un caso no deje session_state
corrupto contaminando el siguiente.

Uso:
  PYTHONIOENCODING=utf-8 uv run python .claude/skills/run-veritrade-imports/fuzz_dashboard.py
  PYTHONIOENCODING=utf-8 uv run python .claude/skills/run-veritrade-imports/fuzz_dashboard.py --random-n 50
  PYTHONIOENCODING=utf-8 uv run python .claude/skills/run-veritrade-imports/fuzz_dashboard.py --page app.py
"""
from __future__ import annotations

import argparse
import logging
import random
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent

logging.disable(logging.WARNING)
warnings.filterwarnings("ignore")


def _fresh(page: str, timeout: float):
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(ROOT / page), default_timeout=timeout)
    at.run()
    return at


def _exc_text(at) -> list[str]:
    return [str(e) for e in at.exception]


def _registrar(hallazgos: list[dict], tipo: str, desc: str, at=None, error: str | None = None):
    crash = bool(error) or (at is not None and len(at.exception) > 0)
    entry = {"tipo": tipo, "desc": desc, "crash": crash}
    if crash:
        entry["error"] = error or "; ".join(_exc_text(at))
    hallazgos.append(entry)
    print(f"  [{'CRASH' if crash else 'ok'}] {tipo}: {desc}" + (f"  -> {entry.get('error','')[:200]}" if crash else ""))


def barrido_un_factor(page: str, timeout: float, max_opciones: int) -> list[dict]:
    print("\n== Pasada 1: barrido de un solo factor ==")
    hallazgos = []
    base = _fresh(page, timeout)

    for i, w in enumerate(base.radio):
        for val in w.options:
            at = _fresh(page, timeout)
            try:
                at.radio[i].set_value(val).run()
            except Exception as e:
                _registrar(hallazgos, "radio", f"{w.label!r} = {val!r}", error=str(e))
                continue
            _registrar(hallazgos, "radio", f"{w.label!r} = {val!r}", at=at)

    for i, w in enumerate(base.selectbox):
        opciones = list(w.options)[:max_opciones]
        for val in opciones:
            at = _fresh(page, timeout)
            try:
                at.selectbox[i].select(val).run()
            except Exception as e:
                _registrar(hallazgos, "selectbox", f"{w.label!r} = {val!r}", error=str(e))
                continue
            _registrar(hallazgos, "selectbox", f"{w.label!r} = {val!r}", at=at)

    for i, w in enumerate(base.multiselect):
        for desc, val in [("vacío", []), ("todas las opciones", list(w.options))]:
            at = _fresh(page, timeout)
            try:
                at.multiselect[i].set_value(val).run()
            except Exception as e:
                _registrar(hallazgos, "multiselect", f"{w.label!r} = {desc}", error=str(e))
                continue
            _registrar(hallazgos, "multiselect", f"{w.label!r} = {desc}", at=at)

    return hallazgos


def combos_adversariales(page: str, timeout: float) -> list[dict]:
    print("\n== Pasada 2: combos adversariales a mano ==")
    hallazgos = []

    def intentar(desc: str, pasos):
        at = _fresh(page, timeout)
        try:
            for paso in pasos:
                paso(at)
            at.run()
        except Exception as e:
            _registrar(hallazgos, "combo", desc, error=str(e))
            return
        _registrar(hallazgos, "combo", desc, at=at)

    def set_radio_por_label(at, label, val):
        for w in at.radio:
            if w.label == label:
                w.set_value(val)
                return
        raise AssertionError(f"no se encontró radio {label!r}")

    def selectbox_por_label(at, label):
        for w in at.selectbox:
            if w.label == label:
                return w
        return None

    def set_selectbox_por_label(at, label, val):
        w = selectbox_por_label(at, label)
        if w is None:
            raise AssertionError(f"no se encontró selectbox {label!r}")
        w.select(val)

    intentar("Vista=Sinotruk + Carr. vacío (0 filas Sinotruk garantizado)", [
        lambda at: set_radio_por_label(at, "Vista", "🟡 Sinotruk"),
        lambda at: at.multiselect[0].set_value([]),
    ])

    def igualar_marca_a_b(at):
        wa, wb = selectbox_por_label(at, "Marca A"), selectbox_por_label(at, "Marca B")
        if wa is None or wb is None:
            raise AssertionError("no se encontraron los selectbox Marca A / Marca B")
        val = wa.options[0]
        wa.select(val)
        wb.select(val)

    intentar("Marca A == Marca B en el comparador", [igualar_marca_a_b])

    intentar("Carr. vacío en vista Global", [
        lambda at: at.multiselect[0].set_value([]),
    ])

    intentar("Desglose por Segmento + Carr. vacío", [
        lambda at: set_radio_por_label(at, "Desglose por:", "⚖️ Segmento (Peso)"),
        lambda at: at.multiselect[0].set_value([]),
    ])

    intentar("Rango de fechas invertido: fin (Mf/Af) antes que inicio (Mi/Ai)", [
        lambda at: set_selectbox_por_label(at, "Mi", "Dic"),
        lambda at: set_selectbox_por_label(at, "Ai", "2026"),
        lambda at: set_selectbox_por_label(at, "Mf", "Ene"),
        lambda at: set_selectbox_por_label(at, "Af", "2023"),
    ])

    intentar("Rango de fechas de un solo mes (Mi=Mf, Ai=Af)", [
        lambda at: set_selectbox_por_label(at, "Mi", "Ene"),
        lambda at: set_selectbox_por_label(at, "Ai", "2026"),
        lambda at: set_selectbox_por_label(at, "Mf", "Ene"),
        lambda at: set_selectbox_por_label(at, "Af", "2026"),
    ])

    return hallazgos


def combos_aleatorios(page: str, timeout: float, n: int, max_opciones: int, seed: int) -> list[dict]:
    print(f"\n== Pasada 3: {n} combos aleatorios (seed={seed}) ==")
    rng = random.Random(seed)
    hallazgos = []
    base = _fresh(page, timeout)
    n_radios = len(base.radio)
    n_selects = len(base.selectbox)
    n_multi = len(base.multiselect)

    for _ in range(n):
        at = _fresh(page, timeout)
        elegidos = []
        try:
            for i in range(n_radios):
                if rng.random() < 0.5:
                    val = rng.choice(at.radio[i].options)
                    at.radio[i].set_value(val)
                    elegidos.append(f"radio[{i}]={val!r}")
            for i in range(n_selects):
                if rng.random() < 0.3:
                    opts = list(at.selectbox[i].options)[:max_opciones]
                    if opts:
                        val = rng.choice(opts)
                        at.selectbox[i].select(val)
                        elegidos.append(f"selectbox[{i}]={val!r}")
            for i in range(n_multi):
                if rng.random() < 0.3:
                    opts = list(at.multiselect[i].options)
                    subset = rng.sample(opts, k=rng.randint(0, len(opts))) if opts else []
                    at.multiselect[i].set_value(subset)
                    elegidos.append(f"multiselect[{i}]={len(subset)} opciones")
            at.run()
        except Exception as e:
            _registrar(hallazgos, "random", ", ".join(elegidos) or "(sin cambios)", error=str(e))
            continue
        _registrar(hallazgos, "random", ", ".join(elegidos) or "(sin cambios)", at=at)

    return hallazgos


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", default="pages/2_Camiones.py")
    ap.add_argument("--timeout", type=float, default=60.0)
    ap.add_argument("--max-opciones", type=int, default=8,
                     help="Tope de valores a probar por selectbox en el barrido (default 8)")
    ap.add_argument("--random-n", type=int, default=20,
                     help="Cantidad de combos aleatorios a probar (default 20)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--skip-sweep", action="store_true")
    ap.add_argument("--skip-adversarial", action="store_true")
    ap.add_argument("--skip-random", action="store_true")
    args = ap.parse_args()

    print(f"Fuzzing: {args.page}")
    todos = []
    if not args.skip_sweep:
        todos += barrido_un_factor(args.page, args.timeout, args.max_opciones)
    if not args.skip_adversarial:
        todos += combos_adversariales(args.page, args.timeout)
    if not args.skip_random:
        todos += combos_aleatorios(args.page, args.timeout, args.random_n, args.max_opciones, args.seed)

    crashes = [h for h in todos if h["crash"]]
    print(f"\n{'=' * 60}")
    print(f"Total casos probados: {len(todos)}")
    print(f"Crashes encontrados: {len(crashes)}")
    print(f"{'=' * 60}")
    for c in crashes:
        print(f"\n[{c['tipo']}] {c['desc']}")
        print(f"  {c['error']}")

    return 1 if crashes else 0


if __name__ == "__main__":
    raise SystemExit(main())
