#!/usr/bin/env python3
"""Fase B — extracción estructurada con LLM (DeepSeek), híbrida y normalizada.
   [CORREGIDO: Merge por DUA/DAM para archivos filtrados]"""

import argparse, datetime as _dt, os, sys
from pathlib import Path

def load_dotenv(path=".env"):
    p = Path(path)
    if not p.exists(): return
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line: continue
        k, _, val = line.partition("=")
        os.environ.setdefault(k.strip(), val.strip().strip('"').strip("'"))

import openpyxl, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.llm import report, sampler, validate, vocab as vocab_mod
from scripts.llm.cache import Cache, text_key

INPUTS_DIR, OUTPUTS_DIR, HEADER_ROW = "inputs", "outputs", 6

def load_v1_with_desc(raw_path, v1_path):
    df = pd.read_excel(v1_path, sheet_name="estructurado")
    wb = openpyxl.load_workbook(raw_path, read_only=True)
    ws = wb.active
    header = next(ws.iter_rows(min_row=HEADER_ROW, max_row=HEADER_ROW, values_only=True))
    j_dua = header.index("DUA / DAM")
    j_desc = header.index("Descripcion Comercial")
    raw_data = []
    for row in ws.iter_rows(min_row=HEADER_ROW + 1, values_only=True):
        if all(c is None for c in row): continue
        raw_data.append({"dua_dam": str(row[j_dua]).strip() if row[j_dua] else "",
                         "_desc": str(row[j_desc]).strip() if row[j_desc] else ""})
    wb.close()
    df_raw = pd.DataFrame(raw_data)
    df = df.merge(df_raw, on="dua_dam", how="left")
    print(f"  v1={len(df)} filas, crudo={len(df_raw)} filas (merge OK)")
    df["row_key"] = df.apply(lambda r: f"{r['dua_dam']}|{r['vin'] if pd.notna(r['vin']) else r['chasis']}", axis=1)
    return df

def make_on_batch():
    def on_batch(content, batch, keymap, cache):
        parsed = validate.parse_json_lenient(content)
        items = validate.items_by_index(parsed)
        for i, (_, desc) in enumerate(batch):
            item = items.get(i)
            if item is not None: cache.put(keymap[i], item)
    return on_batch

def process_file(raw_path, v1_path, out_path, v, cache, args):
    print(f"\n=== {raw_path.name} ===")
    df = load_v1_with_desc(raw_path, v1_path)
    use_sample = bool(args.sample) and not args.all
    sub = sampler.sample(df, v, n=args.sample) if use_sample else df
    print(f"Filas a procesar: {len(sub)} (de {len(df)})")
    sub = sub.copy()
    sub["_tkey"] = sub["_desc"].map(text_key)
    pendientes = {}
    for _, r in sub.iterrows():
        k = r["_tkey"]
        if k not in cache and k not in pendientes and isinstance(r["_desc"], str):
            pendientes[k] = r["_desc"]
    print(f"Textos pendientes: {len(pendientes)}")
    
    if args.dry_run:
        from scripts.llm.client import Stats; stats = Stats()
    else:
        from scripts.llm.client import DeepSeekClient
        model = args.model or None
        client = DeepSeekClient(v, **({"model": model} if model else {}), batch_size=args.batch_size, workers=args.workers)
        on_batch = make_on_batch()
        pend = dict(pendientes)
        for paso in range(3):
            if not pend: break
            client.batch_size = args.batch_size if paso == 0 else 1
            client.run(list(pend.items()), cache, on_batch=on_batch)
            pend = {k: d for k, d in pendientes.items() if k not in cache}
        stats = client.stats
    
    recs = []
    for _, r in sub.iterrows():
        raw = cache.get(r["_tkey"])
        rec = validate.normalize_record(raw, v) if raw else validate.empty_record()
        recs.append(rec)
    
    norm_df = pd.DataFrame(recs, index=sub.index)
    out = pd.concat([sub.drop(columns=["_desc", "_tkey"]), norm_df], axis=1)
    fecha = _dt.date.today().isoformat()
    modelo_usado = args.model or os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")
    out["fuente"] = f"LLM:{modelo_usado}@{fecha}"
    rep = report.build(out, stats)
    print("\n=== REPORTE ===")
    print(rep.to_string(index=False))
    
    revisar = out[out["modelo_flag"].isin(["low", "nomatch", "alias"]) | (~out["marca_in_vocab"]) | (~out["traccion_valido"]) | (~out["combustible_valido"]) | (~out["clasificacion_valido"]) | (~out["caja_valido"])]
    nuevos = out[(~out["marca_in_vocab"]) & out["marca_norm"].notna()]
    vocab_nuevo = (nuevos.groupby("marca_norm").agg(unidades=("marca_norm", "size"), sugerencia=("marca_sugerencia", "first"), modelos=("modelo_raw_llm", lambda s: ", ".join(sorted({str(x) for x in s if pd.notna(x)})[:10]))).sort_values("unidades", ascending=False).reset_index())
    
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out_path, engine="openpyxl") as xw:
        out.to_excel(xw, sheet_name="normalizado_llm", index=False)
        revisar.to_excel(xw, sheet_name="_revisar_llm", index=False)
        vocab_nuevo.to_excel(xw, sheet_name="_vocab_nuevo", index=False)
        rep.to_excel(xw, sheet_name="_reporte", index=False)
    print(f"Escrito: {out_path} ({len(out)} filas)")
    return True

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs-dir", default=INPUTS_DIR)
    ap.add_argument("--outputs-dir", default=OUTPUTS_DIR)
    ap.add_argument("--input")
    ap.add_argument("--vocab", default=None)
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--batch-size", type=int, default=10)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--model", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    
    load_dotenv()
    v = vocab_mod.load(args.vocab) if args.vocab else vocab_mod.load()
    
    srcs = [Path(args.input)] if args.input else sorted(Path(args.inputs_dir).glob("*.xlsx"))
    if not srcs:
        print("No se encontraron .xlsx", file=sys.stderr)
        return 1
    
    out_dir = Path(args.outputs_dir)
    cache = Cache()
    ok = 0
    for raw in srcs:
        v1 = out_dir / f"{raw.stem}_estructurado.xlsx"
        if not v1.exists():
            print(f"Falta {v1}", file=sys.stderr)
            continue
        out = out_dir / f"{raw.stem}_normalizado.xlsx"
        if process_file(raw, v1, out, v, cache, args):
            ok += 1
    print(f"\nListo: {ok}/{len(srcs)} archivos normalizados.")
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
