"""
apptest_inventory.py -- headless *data* verification for the
veritrade-imports Streamlit dashboard, without launching a server or a
browser.

Complementary to driver.py (which gives you a real screenshot): this uses
Streamlit's own test harness (`streamlit.testing.v1.AppTest`) to execute a
page script end-to-end -- including every `st.tabs()` block, since
Streamlit runs all tab bodies server-side regardless of which tab is
visually selected -- and lets you inspect the *exact* data (labels/values)
inside every Plotly chart. Faster than driver.py and better for "does
chart X contain value Y" questions; use driver.py when you need to see
layout/CSS or hand someone a picture.

Usage:
  uv run python .claude/skills/run-veritrade-imports/apptest_inventory.py
  uv run python .claude/skills/run-veritrade-imports/apptest_inventory.py --page app.py
  uv run python .claude/skills/run-veritrade-imports/apptest_inventory.py --grep HOWO
  uv run python .claude/skills/run-veritrade-imports/apptest_inventory.py --dump inventory.json

Must be run with PYTHONIOENCODING=utf-8 (see SKILL.md Gotchas).
"""
from __future__ import annotations

import argparse
import base64
import json
import logging
import warnings
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _decode(v):
    """Plotly's compact JSON array format stores big arrays as
    {"dtype": "...", "bdata": "<base64>"} instead of a plain list."""
    if isinstance(v, dict) and "bdata" in v:
        raw = base64.b64decode(v["bdata"])
        return np.frombuffer(raw, dtype=v["dtype"]).tolist()
    return v


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", default="pages/2_Camiones.py",
                     help="Page/app file to run (relative to repo root). Default: pages/2_Camiones.py")
    ap.add_argument("--grep", default=None,
                     help="Only print charts whose title or any label contains this substring (case-insensitive)")
    ap.add_argument("--dump", default=None,
                     help="Write the full chart inventory (title + labels + values) as JSON to this path")
    ap.add_argument("--timeout", type=float, default=60.0)
    args = ap.parse_args()

    logging.disable(logging.WARNING)
    warnings.filterwarnings("ignore")

    from streamlit.testing.v1 import AppTest

    page_path = ROOT / args.page
    if not page_path.exists():
        print(f"No existe: {page_path}")
        return 1

    at = AppTest.from_file(str(page_path), default_timeout=args.timeout)
    at.run()

    print(f"Página: {args.page}")
    print(f"Excepciones: {len(at.exception)}")
    for e in at.exception:
        print("--- EXCEPTION ---")
        print(e)

    charts = at.get("plotly_chart")
    print(f"Charts (plotly_chart): {len(charts)}")

    inventory = []
    grep = args.grep.upper() if args.grep else None
    for i, chart in enumerate(charts):
        spec = json.loads(chart.proto.spec)
        title = spec.get("layout", {}).get("title", {})
        title_text = title.get("text") if isinstance(title, dict) else title
        traces = []
        for tr in spec.get("data", []):
            labels = _decode(tr.get("labels") or tr.get("x"))
            values = _decode(tr.get("values") or tr.get("y"))
            traces.append({"type": tr.get("type"), "labels": labels, "values": values})
        entry = {"index": i, "title": title_text, "traces": traces}
        inventory.append(entry)

        if grep is not None:
            hay = str(title_text or "").upper()
            hay += " " + " ".join(str(lab).upper() for tr in traces for lab in (tr["labels"] or []))
            if grep not in hay:
                continue

        print(f"\n--- chart #{i}: {title_text} ---")
        for tr in traces:
            pairs = list(zip(tr["labels"] or [], tr["values"] or []))
            print(f"  [{tr['type']}] {pairs[:15]}{' ...' if len(pairs) > 15 else ''}")

    if args.dump:
        out_path = Path(args.dump)
        out_path.write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nVolcado: {out_path}")

    return 1 if at.exception else 0


if __name__ == "__main__":
    raise SystemExit(main())
