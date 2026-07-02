"""Orquestador del pipeline Veritrade: Bronze → Silver → Gold.

Uso:
  python pipeline/run.py                   # pipeline completo
  python pipeline/run.py --silver-only     # solo Fase 1 (Bronze → Silver)
  python pipeline/run.py --gold-only       # solo Fase 2 (Silver → Gold)
  python pipeline/run.py --input archivo.xlsx
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser(description="Pipeline Veritrade: Bronze -> Silver -> Gold")
    ap.add_argument("--silver-only", action="store_true", help="Solo ejecutar Fase 1")
    ap.add_argument("--gold-only",   action="store_true", help="Solo ejecutar Fase 2")
    ap.add_argument("--input", help="Archivo específico a procesar (opcional)")
    args = ap.parse_args()

    if not args.gold_only:
        print("\n" + "═" * 60)
        print("  FASE 1: Bronze → Silver (parse determinístico)")
        print("═" * 60)
        cmd = [sys.executable, str(ROOT / "pipeline" / "silver.py")]
        if args.input:
            cmd += ["--input", args.input]
        result = subprocess.run(cmd, cwd=str(ROOT))
        if result.returncode != 0:
            print("❌ Fase 1 falló. Abortando.")
            return 1

    if not args.silver_only:
        print("\n" + "═" * 60)
        print("  FASE 2: Silver → Gold (normalización LLM)")
        print("═" * 60)
        cmd = [sys.executable, str(ROOT / "pipeline" / "gold.py")]
        if args.input:
            cmd += ["--input", args.input]
        result = subprocess.run(cmd, cwd=str(ROOT))
        if result.returncode != 0:
            print("❌ Fase 2 falló.")
            return 1

    print("\n✅ Pipeline completo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
