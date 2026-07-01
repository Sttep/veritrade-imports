"""
pipeline/gold.py  —  FASE 2 (Silver → Gold): Normalización LLM híbrida
═══════════════════════════════════════════════════════════════════════

Lee los archivos estructurados de data/silver/ (_fase1.xlsx),
envía los registros de baja confianza a DeepSeek y escribe
los resultados normalizados en data/gold/.

Uso:
  python pipeline/gold.py
  python pipeline/gold.py --sample 300    # modo rápido
  python pipeline/gold.py --dry-run       # sin llamadas al LLM
"""

from __future__ import annotations

import argparse
import datetime as _dt
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def load_dotenv(path=".env"):
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, val = line.partition("=")
        os.environ.setdefault(k.strip(), val.strip().strip('"').strip("'"))


import pandas as pd
from pipeline.llm import report, sampler, validate, vocab as vocab_mod
from pipeline.llm.cache import Cache, text_key

BRONZE_DIR = ROOT / "data" / "bronze"
SILVER_DIR = ROOT / "data" / "silver"
GOLD_DIR   = ROOT / "data" / "gold"


def load_silver_data(silver_path: Path) -> pd.DataFrame:
    df = pd.read_excel(silver_path, sheet_name="estructurado")
    if "_descripcion" not in df.columns:
        df["_descripcion"] = ""
    df["row_key"] = df.apply(
        lambda r: f"{r.get('dua_dam', '')}|{r.get('vin', r.get('chasis', ''))}",
        axis=1,
    )
    return df


def make_on_batch():
    def on_batch(content, batch, keymap, cache):
        parsed = validate.parse_json_lenient(content)
        items  = validate.items_by_index(parsed)
        for i, (_, desc) in enumerate(batch):
            item = items.get(i)
            if item is not None:
                cache.put(keymap[i], item)
    return on_batch


def process_file(bronze_path: Path, silver_path: Path, out_path: Path,
                 v, cache, args) -> bool:
    print(f"\n=== {bronze_path.name} ===")

    df = load_silver_data(silver_path)
    use_sample = bool(args.sample) and not args.all
    sub = sampler.sample(df, v, n=args.sample) if use_sample else df
    print(f"Filas totales a evaluar: {len(sub)} (de {len(df)})")

    sub = sub.copy()

    if "_descripcion" not in sub.columns:
        print("⚠️  No hay columna '_descripcion'. Saltando llamado a LLM.")
        sub["_descripcion"] = ""

    sub["_tkey"] = sub["_descripcion"].map(text_key)

    pendientes = {}
    for _, r in sub.iterrows():
        k = r["_tkey"]
        confianza = str(r.get("confianza_clasificacion", "")).strip().upper()
        if (confianza != "ALTA"
                and k not in cache
                and k not in pendientes
                and isinstance(r.get("_descripcion"), str)
                and r["_descripcion"]):
            pendientes[k] = r["_descripcion"]

    print(f"Textos pendientes para la IA (DeepSeek): {len(pendientes)}")

    if args.dry_run:
        from pipeline.llm.client import Stats
        stats = Stats()
    else:
        from pipeline.llm.client import DeepSeekClient
        model  = args.model or None
        client = DeepSeekClient(
            v, **({"model": model} if model else {}),
            batch_size=args.batch_size, workers=args.workers,
        )
        on_batch = make_on_batch()
        pend = dict(pendientes)
        for paso in range(3):
            if not pend:
                break
            client.batch_size = args.batch_size if paso == 0 else min(5, args.batch_size)
            client.run(list(pend.items()), cache, on_batch=on_batch)
            pend = {k: d for k, d in pendientes.items() if k not in cache}
        stats = client.stats

    recs = []
    modelo_usado = args.model or os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")
    fecha = _dt.date.today().isoformat()

    for _, r in sub.iterrows():
        confianza = str(r.get("confianza_clasificacion", "")).strip().upper()

        if confianza == "ALTA":
            rec = {
                "marca_raw_llm": None, "marca_norm": r.get("marca"),
                "marca_in_vocab": True, "marca_sugerencia": None,
                "modelo_raw_llm": None, "modelo_match": r.get("modelo"),
                "modelo_score": 100.0, "modelo_flag": "reglas_alta",
                "tren_rodaje_norm": r.get("tren_rodaje"), "tren_rodaje_valido": True,
                "combustible_norm": r.get("combustible"), "combustible_valido": True,
                "categoria_maquinaria_norm": r.get("categoria_maquinaria"),
                "categoria_maquinaria_valido": True,
                "subcategoria_norm": r.get("subcategoria"),
                "fuente": "Reglas (Silver)",
            }
        else:
            raw = cache.get(r["_tkey"])
            rec = validate.normalize_record(raw, v) if raw else validate.empty_record()

            modelo_fase_a = r.get("modelo")
            if pd.notna(modelo_fase_a) and str(modelo_fase_a).strip() != "":
                rec["modelo_match"] = modelo_fase_a
                rec["modelo_flag"]  = "recuperado_silver"
                rec["modelo_score"] = 100.0

            rec["fuente"] = f"LLM_Hibrido:{modelo_usado}@{fecha}"

        recs.append(rec)

    norm_df = pd.DataFrame(recs, index=sub.index)
    out = pd.concat([sub.drop(columns=["_tkey"]), norm_df], axis=1)

    try:
        stats
    except NameError:
        from pipeline.llm.client import Stats
        stats = Stats()

    try:
        rep = report.build(out, stats)
        print("\n=== REPORTE ===")
        print(rep.to_string(index=False))
    except Exception:
        rep = pd.DataFrame()
        print("\n⚠️ No se pudo generar el reporte.")

    revisar = out[
        out["modelo_flag"].isin(["low", "nomatch", "alias"])
        | (~out["marca_in_vocab"].fillna(False).astype(bool))
        | (~out["tren_rodaje_valido"].fillna(True).astype(bool))
        | (~out["combustible_valido"].fillna(True).astype(bool))
        | (~out["categoria_maquinaria_valido"].fillna(True).astype(bool))
    ]

    nuevos = out[(~out["marca_in_vocab"]) & out["marca_norm"].notna()]
    vocab_nuevo = pd.DataFrame()
    if not nuevos.empty:
        vocab_nuevo = (
            nuevos.groupby("marca_norm")
            .agg(
                unidades=("marca_norm", "size"),
                sugerencia=("marca_sugerencia", "first"),
                modelos=("modelo_raw_llm",
                         lambda s: ", ".join(sorted({str(x) for x in s if pd.notna(x)})[:10])),
            )
            .sort_values("unidades", ascending=False)
            .reset_index()
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out_path, engine="openpyxl") as xw:
        out.to_excel(xw, sheet_name="normalizado_final", index=False)
        if not revisar.empty:
            revisar.to_excel(xw, sheet_name="_revisar_final", index=False)
        if not vocab_nuevo.empty:
            vocab_nuevo.to_excel(xw, sheet_name="_vocab_nuevo", index=False)
        if not rep.empty:
            rep.to_excel(xw, sheet_name="_reporte", index=False)

    print(f"✅ Gold escrito: {out_path.relative_to(ROOT)} ({len(out)} filas)")
    return True


def main():
    ap = argparse.ArgumentParser(description="Fase 2 (Gold) — Normalización LLM Veritrade")
    ap.add_argument("--bronze-dir",  default=str(BRONZE_DIR))
    ap.add_argument("--silver-dir",  default=str(SILVER_DIR))
    ap.add_argument("--gold-dir",    default=str(GOLD_DIR))
    ap.add_argument("--input")
    ap.add_argument("--vocab",       default=None)
    ap.add_argument("--sample",      type=int, default=0)
    ap.add_argument("--all",         action="store_true")
    ap.add_argument("--batch-size",  type=int, default=10)
    ap.add_argument("--workers",     type=int, default=4)
    ap.add_argument("--model",       default=None)
    ap.add_argument("--dry-run",     action="store_true")
    ap.add_argument("--exclude",     nargs="*", default=[], metavar="PATRON",
                    help="Excluir archivos cuyo nombre contenga alguno de estos patrones (sin distinción de mayúsculas)")
    args = ap.parse_args()

    load_dotenv()
    v = vocab_mod.load(args.vocab) if args.vocab else vocab_mod.load()

    bronze_dir = Path(args.bronze_dir)
    silver_dir = Path(args.silver_dir)
    gold_dir   = Path(args.gold_dir)
    gold_dir.mkdir(parents=True, exist_ok=True)

    srcs = [Path(args.input)] if args.input else sorted(bronze_dir.glob("*.xlsx"))
    if args.exclude:
        excluidos = [f for f in srcs if any(p.lower() in f.name.lower() for p in args.exclude)]
        srcs = [f for f in srcs if f not in excluidos]
        for f in excluidos:
            print(f"⏭  Excluido: {f.name}")
    if not srcs:
        print("❌ No se encontraron archivos en bronze.", file=sys.stderr)
        return 1

    cache = Cache()
    ok = 0
    for raw in srcs:
        silver = silver_dir / f"{raw.stem}_fase1.xlsx"
        if not silver.exists():
            print(f"⚠️ Falta {silver}. Corre primero pipeline/silver.py.", file=sys.stderr)
            continue
        out = gold_dir / f"{raw.stem}_normalizado.xlsx"
        if process_file(raw, silver, out, v, cache, args):
            ok += 1

    print(f"\n🎉 Listo: {ok}/{len(srcs)} archivos procesados en Gold.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
