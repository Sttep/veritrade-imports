"""
filtro_por_marca.py — Filtro para descargas Veritrade por MARCA
Regla única y sin excepciones:
  ✅ MANTENER : la descripción empieza con N1, N2 o N3
  ❌ EXCLUIR  : todo lo demás (piezas, autos, ropa, buses, químicos, etc.)

Uso:
  1. Pon las descargas en  inputs/por_marca/
  2. python filtro_por_marca.py
  3. Los limpios quedan en  inputs/  listos para extractor_fase1.py
"""
from pathlib import Path
import re
import pandas as pd
import warnings; warnings.filterwarnings("ignore")

ENTRADA = Path("inputs/marcasotros")
SALIDA  = Path("inputs")

# Regex: solo acepta descripción que EMPIECE con N1, N2 o N3
RE_N = re.compile(r"^\s*N[123][\s,]", re.IGNORECASE)

# ── DETECCIÓN DE HEADER ───────────────────────────────────────────────────────
HEADER_KW = {"DUA","DAM","IMPORTADOR","DESCRIPCI","ADUANA","PARTIDA","FECHA"}

def detectar_header(path: Path) -> int:
    df_raw = pd.read_excel(path, header=None, dtype=str, nrows=20)
    for i, row in df_raw.iterrows():
        vals = {str(v).upper()[:15] for v in row if pd.notna(v)}
        if len(vals & HEADER_KW) >= 2:
            return i
    return 0

# ── DETECCIÓN DE COLUMNA DE DESCRIPCIÓN ──────────────────────────────────────
NOMBRES_DESC = [
    "descripcion comercial", "descripción comercial",
    "descripcion", "descripción",
    "commercial description", "desc comercial",
    "detalle", "mercancia", "mercancía",
]

def encontrar_col_desc(df: pd.DataFrame) -> str | None:
    cols_lower = {c: c.lower().strip() for c in df.columns}

    # 1. Buscar por nombre conocido
    for c, cl in cols_lower.items():
        for nombre in NOMBRES_DESC:
            if nombre in cl:
                return c

    # 2. Buscar por nombre parcial (descripci / comercial)
    for c, cl in cols_lower.items():
        if "descripci" in cl or "comercial" in cl:
            return c

    # 3. Fallback: columna de texto con más contenido
    #    (la que tiene el mayor número de celdas no vacías)
    candidatas = [
        c for c in df.columns
        if df[c].dtype == object and df[c].notna().sum() > len(df) * 0.5
    ]
    if candidatas:
        # La más larga en promedio (descripción > código de producto)
        mejor = max(candidatas, key=lambda c: df[c].dropna().astype(str).str.len().mean())
        return mejor

    return None

# ── PROCESAR UN ARCHIVO ───────────────────────────────────────────────────────
def procesar(path: Path):
    print(f"\n  📄 {path.name}")

    h = detectar_header(path)
    try:
        df = pd.read_excel(path, header=h, dtype=str)
    except Exception as e:
        print(f"     ❌ Error al leer: {e}"); return

    df.columns = [str(c).strip() for c in df.columns]
    total = len(df)
    print(f"     Header fila {h} | {total:,} filas | Columnas: {list(df.columns[:6])}...")

    col = encontrar_col_desc(df)
    if not col:
        print("     ❌ No encontré columna de descripción — saltando")
        return
    print(f"     Columna usada: '{col}'")

    # Mostrar primeras 5 descripciones para verificar
    muestras = df[col].dropna().head(5).tolist()
    print("     Muestra de descripciones:")
    for m in muestras:
        print(f"       → {str(m)[:80]}")

    # FILTRO: solo N1 / N2 / N3
    mask = df[col].fillna("").astype(str).apply(lambda x: bool(RE_N.match(x)))
    df_ok   = df[mask].copy()
    df_excl = df[~mask].copy()

    n_ok   = len(df_ok)
    n_excl = len(df_excl)
    pct    = n_ok / total * 100 if total > 0 else 0

    print(f"     ✅ Mantener (N1/N2/N3): {n_ok:>6,}  ({pct:.1f}%)")
    print(f"     ❌ Excluir (resto)    : {n_excl:>6,}  ({100-pct:.1f}%)")

    if n_ok == 0:
        print("     ⚠  CERO filas N1/N2/N3 — ¿columna correcta?")
        print(f"     → Primeras 3 celdas de '{col}':")
        for v in df[col].dropna().head(3):
            print(f"        '{str(v)[:100]}'")
        return

    # Guardar
    out = SALIDA / f"cleaned_{path.stem}.xlsx"
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        df_ok.to_excel(  w, sheet_name="datos",      index=False)
        df_excl.to_excel(w, sheet_name="_excluidos", index=False)
    print(f"     💾 → {out.name}")

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    print("\n" + "═"*60)
    print("  FILTRO POR MARCA  —  Regla: solo N1 / N2 / N3")
    print("═"*60)
    ENTRADA.mkdir(parents=True, exist_ok=True)
    SALIDA.mkdir(parents=True, exist_ok=True)

    archivos = sorted(ENTRADA.glob("*.xlsx"))
    if not archivos:
        print(f"\n  ⚠  No hay .xlsx en {ENTRADA.resolve()}")
        print("  → Pon tus descargas de Veritrade en esa carpeta")
        return

    print(f"\n  {len(archivos)} archivo(s) encontrado(s)\n")
    for p in archivos:
        procesar(p)

    print(f"\n{'═'*60}")
    print("  Listo → python extractor_fase1.py")
    print(f"{'═'*60}\n")

if __name__ == "__main__":
    main()