"""
scripts/validar_calidad_datos.py
═════════════════════════════════
QA de calidad interna de datos (no cobertura) para camiones.parquet y
maquinaria.parquet. Solo lectura — no modifica los parquet.

Complementa a scripts/validar_cobertura.py (que valida volumen vs AAP, no
calidad interna del dato: formato de VIN, coherencia numérica, duplicados
entre DUA, marcas fuera de vocabulario, mojibake, etc.)

Uso:
  uv run python scripts/validar_calidad_datos.py
  uv run python scripts/validar_calidad_datos.py --max-ejemplos 10
  uv run python scripts/validar_calidad_datos.py --no-markdown
"""
from __future__ import annotations

import argparse
import re
from datetime import date, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
MAX_EJEMPLOS_DEFAULT = 5

MESES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
    7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}

# ── Mapas de columnas por dataset ──────────────────────────────────────────
# camiones.parquet es 100% str (pipeline/build_parquet.py lee con dtype=str);
# maquinaria.parquet trae dtypes nativos mixtos de un generador distinto.
# Los nombres de columna no coinciden entre datasets para el mismo concepto
# (mismo patrón que shared/loader.py: MAPEO_COLUMNAS_* / _normalizar_columnas).
CAMIONES_COLS = {
    "vin": "vin", "chasis": "chasis", "dua": "dua_dam",
    "peso_bruto": "peso_bruto_desc", "peso_neto": "peso_neto_desc", "kg_bruto_col": "kg_bruto_col",
    "anio_modelo": "anio_modelo", "cilindrada": "cilindrada_cc", "num_cilindros": "num_cilindros",
    "ejes": "ejes", "largo": "largo_mm", "ancho": "ancho_mm", "alto": "alto_mm",
    "fob": "fob_usd", "cif": "cif_usd", "descripcion": "_descripcion", "version": "version",
    "campos_core": ["marca_declarada", "modelo", "carroceria"],
    "carroceria_normalizada": "carroceria_normalizada",
}
MAQUINARIA_COLS = {
    "vin": "vin", "chasis": "chasis", "dua": "dua_dam",
    "peso_bruto": "kg_bruto", "peso_neto": "kg_neto", "kg_bruto_col": None,
    "anio_modelo": "anio_modelo", "cilindrada": None, "num_cilindros": None,
    "ejes": None, "largo": None, "ancho": None, "alto": None,
    "fob": "fob_usd", "cif": "cif_usd", "descripcion": "_descripcion",
    "campos_core": ["marca", "categoria_maquinaria"],
    "carroceria_normalizada": None,  # taxonomia distinta (categoria_maquinaria), no aplica
}

CONFIG_PATH = ROOT / "configuracion.xlsx"

MOJIBAKE_SNIPPETS = ["�", "Ã¡", "Ã©", "Ã­", "Ã³", "Ãº", "Ã±", "Ã‘", "Â°", "â€™", "â€œ", "â€\x9d"]
MOJIBAKE_COLUMNAS = [
    "importador", "marca_declarada", "modelo", "version", "_descripcion",
    "color", "exportador", "carroceria", "transmision", "marca",
]

# Cortes de pages/2_Camiones.py::clasificar_segmento() (Withmory: LDT1/LDT2/MDT1/MDT2/
# MDT3/SEMI PESADO/PESADO). Concentración alta de peso EXACTO en uno de estos valores es
# el patrón "redondo de fábrica" que causó el bug de 33,000kg en tractocamiones (2026-07-09).
FRONTERAS_PESO_KG = [6000, 10000, 15000, 17000, 25000, 33000]

NOTAS_CODIGO = """## Notas de código (fuera de alcance de este script)

Los 4 hallazgos incidentales que este bloque documentaba (mismatch `confianza`/
`confianza_clasificacion` entre silver/gold, dedup por columna completa en vez de fila por fila
en `build_parquet.py`, referencia muerta a `r.get("marca")` en `gold.py`, y `kg_bruto_col` como
fallback de `peso_para_atu`) fueron **verificados como ya corregidos en el código actual**
(re-auditoría 2026-07-09 -- ver `git blame`/commits de julio 2026 para cuándo se corrigió cada
uno). Este bloque queda vacío a propósito -- si una futura auditoría encuentra un hallazgo de
código nuevo fuera de alcance de este script, documentarlo aquí siguiendo el mismo formato.
"""


# ── Helpers de tipado tolerante ──────────────────────────────────────────────

def to_num(df: pd.DataFrame, col: str | None) -> pd.Series:
    """Convierte a numérico sin importar si la columna es str (camiones) o ya
    numérica (maquinaria). Serie de NA si la columna no existe."""
    if not col or col not in df.columns:
        return pd.Series(pd.NA, index=df.index, dtype="Float64")
    return pd.to_numeric(df[col], errors="coerce")


def to_bool_like(df: pd.DataFrame, col: str, default: bool = True) -> pd.Series:
    """Normaliza columnas booleanas que pueden venir como bool nativo
    (maquinaria) o como string 'True'/'False' (camiones)."""
    if col not in df.columns:
        return pd.Series(default, index=df.index)
    s = df[col]
    if s.dtype == bool:
        return s.fillna(default)
    return (
        s.astype(str).str.strip().str.lower()
        .map({"true": True, "false": False})
        .fillna(default)
    )


def text_or_empty(df: pd.DataFrame, col: str | None) -> pd.Series:
    if not col or col not in df.columns:
        return pd.Series("", index=df.index)
    return df[col].astype(str).where(df[col].notna(), "")


# ── Construcción de resultados (misma estructura para consola y markdown) ──

def _fecha_es(d: date) -> str:
    return f"{d.day} de {MESES_ES[d.month]} de {d.year}"


def _no_aplica(titulo: str, motivo: str = "columna no disponible en este dataset") -> dict:
    return {
        "titulo": titulo, "evaluadas": 0, "hallazgos": 0,
        "md": f"### {titulo}\n- — No aplica ({motivo}) —\n",
    }


def _ejemplos(hallazgos_df: pd.DataFrame, cfg: dict, max_ejemplos: int,
              extra_series: pd.Series | None = None, extra_label: str | None = None) -> list[str]:
    dua_col, vin_col, chasis_col = cfg.get("dua"), cfg.get("vin"), cfg.get("chasis")
    lines = []
    for idx, row in hallazgos_df.head(max_ejemplos).iterrows():
        dua = row.get(dua_col, "s/d") if dua_col else "s/d"
        vin = row.get(vin_col) if vin_col else None
        if vin is None or pd.isna(vin) or str(vin).strip() == "":
            vin = row.get(chasis_col) if chasis_col else None
        vin_str = "s/d" if vin is None or pd.isna(vin) or str(vin).strip() == "" else str(vin)
        extra_txt = ""
        if extra_series is not None and idx in extra_series.index:
            val = extra_series.loc[idx]
            if pd.notna(val):
                extra_txt = f" · {extra_label}={val}"
        lines.append(f"  - DUA {dua} · VIN/Chasis {vin_str}{extra_txt}")
    return lines


def _resultado(titulo: str, evaluadas: int, total: int, hallazgos_df: pd.DataFrame, cfg: dict,
               max_ejemplos: int, extra_series: pd.Series | None = None,
               extra_label: str | None = None, nota: str | None = None) -> dict:
    n = len(hallazgos_df)
    pct = (n / evaluadas * 100) if evaluadas else 0.0
    lines = [f"### {titulo}", f"- Filas evaluadas: {evaluadas:,} (de {total:,} totales)"]
    if nota:
        lines.append(f"- {nota}")
    lines.append(f"- Filas con hallazgo: {n:,} ({pct:.2f}%)")
    if n == 0:
        lines.append("- Sin hallazgos")
    else:
        lines.append(f"- Ejemplos (máx. {max_ejemplos}):")
        lines.extend(_ejemplos(hallazgos_df, cfg, max_ejemplos, extra_series, extra_label))
    lines.append("")
    return {"titulo": titulo, "evaluadas": int(evaluadas), "hallazgos": int(n), "md": "\n".join(lines)}


def _resumen_dataset(nombre: str, resultados: list[dict]) -> str:
    lines = [f"## Resumen {nombre.title()}", "", "| Check | Evaluadas | Hallazgos | % |", "|---|---|---|---|"]
    for r in resultados:
        pct = (r["hallazgos"] / r["evaluadas"] * 100) if r["evaluadas"] else 0.0
        lines.append(f"| {r['titulo']} | {r['evaluadas']:,} | {r['hallazgos']:,} | {pct:.2f}% |")
    lines.append("")
    return "\n".join(lines)


# ── Checks ───────────────────────────────────────────────────────────────────

def check_duplicados_exactos(df, nombre, cfg, max_ejemplos):
    titulo = "Duplicados exactos (DUA + VIN/Chasis)"
    dua_col, vin_col, chasis_col = cfg.get("dua"), cfg.get("vin"), cfg.get("chasis")
    if not dua_col or dua_col not in df.columns:
        return _no_aplica(titulo)
    vin_s = df[vin_col] if vin_col and vin_col in df.columns else pd.Series(pd.NA, index=df.index)
    chasis_s = df[chasis_col] if chasis_col and chasis_col in df.columns else pd.Series(pd.NA, index=df.index)
    vin_vacio = vin_s.isna() | (vin_s.astype(str).str.strip() == "")
    clave_id = vin_s.where(~vin_vacio, chasis_s)
    clave = df[dua_col].astype(str) + "|" + clave_id.astype(str)
    con_id = clave_id.notna() & (clave_id.astype(str).str.strip() != "")
    mask = clave.duplicated(keep=False) & con_id
    hallazgos = df[mask]
    return _resultado(titulo, len(df), len(df), hallazgos, cfg, max_ejemplos)


def check_vin_duplicado_entre_dua(df, nombre, cfg, max_ejemplos):
    titulo = "VIN duplicado entre distintos DUA"
    vin_col, dua_col = cfg.get("vin"), cfg.get("dua")
    if not vin_col or vin_col not in df.columns or not dua_col or dua_col not in df.columns:
        return _no_aplica(titulo)
    sub = df[[vin_col, dua_col]].copy()
    sub = sub[sub[vin_col].notna() & (sub[vin_col].astype(str).str.strip() != "")]
    grp = sub.groupby(vin_col)[dua_col].nunique()
    vins_multi = grp[grp > 1].index
    hallazgos = df[df[vin_col].isin(vins_multi)].sort_values(vin_col)
    return _resultado(titulo, len(sub), len(df), hallazgos, cfg, max_ejemplos)


def check_formato_vin(df, nombre, cfg, max_ejemplos):
    titulo = "Formato de VIN (ISO 3779)"
    vin_col = cfg.get("vin")
    if not vin_col or vin_col not in df.columns:
        return _no_aplica(titulo)
    vin = text_or_empty(df, vin_col)
    con_dato = vin.str.strip() != ""
    largo_invalido = con_dato & (vin.str.len() != 17)
    caracteres_invalidos = con_dato & vin.str.upper().str.contains(r"[IOQ]", regex=True, na=False)
    mask = largo_invalido | caracteres_invalidos
    hallazgos = df[mask]
    return _resultado(titulo, int(con_dato.sum()), len(df), hallazgos, cfg, max_ejemplos)


def check_coherencia_peso(df, nombre, cfg, max_ejemplos):
    titulo = "Coherencia peso neto vs. peso bruto"
    pb_col, pn_col = cfg.get("peso_bruto"), cfg.get("peso_neto")
    if not pb_col or not pn_col or pb_col not in df.columns or pn_col not in df.columns:
        return _no_aplica(titulo)
    pb, pn = to_num(df, pb_col), to_num(df, pn_col)
    con_dato = pb.notna() & pn.notna()
    mask = con_dato & (pn > pb)
    hallazgos = df[mask]
    return _resultado(titulo, int(con_dato.sum()), len(df), hallazgos, cfg, max_ejemplos,
                       extra_series=pn, extra_label=pn_col)


def check_rango(df, nombre, cfg, cfg_key, titulo, low, high, max_ejemplos):
    col = cfg.get(cfg_key)
    if not col or col not in df.columns:
        return _no_aplica(titulo)
    serie = to_num(df, col)
    con_dato = serie.notna()
    mask = con_dato & ((serie < low) | (serie > high))
    hallazgos = df[mask]
    return _resultado(titulo, int(con_dato.sum()), len(df), hallazgos, cfg, max_ejemplos,
                       extra_series=serie, extra_label=col, nota=f"Rango válido: [{low}, {high}]")


def check_rango_anio_dua(df, nombre, cfg, max_ejemplos, anio_actual):
    titulo = "Rango de año DUA (derivado de fecha_dua)"
    if "fecha_dua" not in df.columns:
        return _no_aplica(titulo)
    fechas = pd.to_datetime(df["fecha_dua"], errors="coerce")
    anios = fechas.dt.year
    con_dato = anios.notna()
    mask = con_dato & ((anios < 1990) | (anios > anio_actual + 1))
    hallazgos = df[mask]
    return _resultado(titulo, int(con_dato.sum()), len(df), hallazgos, cfg, max_ejemplos,
                       extra_series=anios, extra_label="año_dua",
                       nota=f"Rango válido: [1990, {anio_actual + 1}]")


def check_descripcion_sin_parsear(df, nombre, cfg, max_ejemplos):
    titulo = "Descripción sin parsear (texto presente, campos core vacíos)"
    desc_col = cfg.get("descripcion")
    core_cols = [c for c in cfg.get("campos_core", []) if c in df.columns]
    if not desc_col or desc_col not in df.columns or not core_cols:
        return _no_aplica(titulo)
    desc = text_or_empty(df, desc_col).str.strip()
    tiene_texto = desc.str.len() > 5
    todos_nulos = df[core_cols].isna().all(axis=1)
    mask = tiene_texto & todos_nulos
    hallazgos = df[mask]
    return _resultado(titulo, int(tiene_texto.sum()), len(df), hallazgos, cfg, max_ejemplos)


def check_kg_bruto_vs_peso(df, nombre, cfg, max_ejemplos):
    titulo = "kg_bruto (columna dura) vs. peso_bruto (extraído de texto)"
    kgb_col, pb_col = cfg.get("kg_bruto_col"), cfg.get("peso_bruto")
    if not kgb_col or not pb_col or kgb_col not in df.columns or pb_col not in df.columns:
        return _no_aplica(titulo)
    kgb, pb = to_num(df, kgb_col), to_num(df, pb_col)
    con_dato = kgb.notna() & pb.notna() & (kgb != 0)
    ratio = (pb / kgb).where(con_dato)
    n_eval = int(con_dato.sum())
    mask_outlier = con_dato & ((ratio < 1.0) | (ratio > 6.0))
    hallazgos = df[mask_outlier]

    stats_txt = ""
    if n_eval:
        r = ratio[con_dato]
        stats_txt = (
            f"- Distribución del ratio ({pb_col}/{kgb_col}): "
            f"mediana={r.median():.2f} · p25={r.quantile(.25):.2f} · p75={r.quantile(.75):.2f} "
            f"(patrón sistémico esperado ~3x, no todas las filas fuera de banda son error)"
        )
    resultado = _resultado(titulo, n_eval, len(df), hallazgos, cfg, max_ejemplos,
                            extra_series=ratio, extra_label="ratio", nota=stats_txt or None)
    return resultado


def check_marca_fuera_vocab(df, nombre, cfg, max_ejemplos):
    titulo = "Marca normalizada fuera del vocabulario controlado"
    col = "marca_in_vocab"
    if col not in df.columns:
        return _no_aplica(titulo)
    in_vocab = to_bool_like(df, col, default=True)
    mask = in_vocab == False  # noqa: E712 (serie booleana, no comparación de identidad)
    hallazgos = df[mask]

    marca_col = next((c for c in ("marca_normalizada", "marca_norm", "marca_declarada", "marca")
                       if c in df.columns), None)
    nota = None
    if marca_col and mask.any():
        top = hallazgos[marca_col].astype(str).value_counts().head(10)
        top_txt = ", ".join(f"{m}({n})" for m, n in top.items())
        nota = f"Top marcas afectadas: {top_txt}"

    return _resultado(titulo, len(df), len(df), hallazgos, cfg, max_ejemplos, nota=nota)


def _tiene_mojibake(s: str) -> bool:
    if any(snip in s for snip in MOJIBAKE_SNIPPETS):
        return True
    return bool(re.search(r"ÿ(?=[A-Za-zÁÉÍÓÚÑ])", s))


def check_mojibake(df, nombre, cfg, max_ejemplos):
    titulo = "Mojibake de encoding en columnas de texto"
    cols_candidatas = [c for c in MOJIBAKE_COLUMNAS if c in df.columns]
    if not cols_candidatas:
        return _no_aplica(titulo)

    mask_total = pd.Series(False, index=df.index)
    detalle = []
    for c in cols_candidatas:
        s = text_or_empty(df, c)
        mask_col = s.apply(_tiene_mojibake)
        if mask_col.any():
            detalle.append(f"{c}({int(mask_col.sum())})")
        mask_total |= mask_col

    hallazgos = df[mask_total]
    nota = f"Columnas con hallazgo: {', '.join(detalle)}" if detalle else None
    return _resultado(titulo, len(df), len(df), hallazgos, cfg, max_ejemplos, nota=nota)


def check_fob_cif(df, nombre, cfg, max_ejemplos):
    titulo = "CIF menor que FOB"
    fob_col, cif_col = cfg.get("fob"), cfg.get("cif")
    if not fob_col or not cif_col or fob_col not in df.columns or cif_col not in df.columns:
        return _no_aplica(titulo)
    fob, cif = to_num(df, fob_col), to_num(df, cif_col)
    con_dato = fob.notna() & cif.notna() & (fob > 0)
    mask = con_dato & (cif < fob)
    hallazgos = df[mask]
    return _resultado(titulo, int(con_dato.sum()), len(df), hallazgos, cfg, max_ejemplos,
                       extra_series=cif, extra_label=cif_col)


def check_carroceria_fuera_catalogo(df, nombre, cfg, max_ejemplos):
    titulo = "Carrocería fuera del catálogo conocido (configuracion.xlsx)"
    col = cfg.get("carroceria_normalizada")
    if not col or col not in df.columns:
        return _no_aplica(titulo)
    if not CONFIG_PATH.exists():
        return _no_aplica(titulo, motivo="configuracion.xlsx no encontrado")
    carrocerias = pd.ExcelFile(CONFIG_PATH).parse("carrocerias", dtype=str)
    validos = set(carrocerias["valor"].dropna().str.upper().str.strip())

    serie = df[col].astype(str).where(df[col].notna(), "").str.upper().str.strip()
    con_dato = serie != ""
    mask = con_dato & ~serie.isin(validos)
    hallazgos = df[mask]

    nota = None
    if mask.any():
        top = serie[mask].value_counts().head(10)
        top_txt = ", ".join(f"{v}({n})" for v, n in top.items())
        nota = f"Top valores no catalogados: {top_txt}"

    return _resultado(titulo, int(con_dato.sum()), len(df), hallazgos, cfg, max_ejemplos, nota=nota)


def check_formato_anio_modelo(df, nombre, cfg, max_ejemplos):
    titulo = "Formato inconsistente de anio_modelo (string 'YYYY' vs 'YYYY.0')"
    col = cfg.get("anio_modelo")
    if not col or col not in df.columns:
        return _no_aplica(titulo)
    serie = df[col].astype(str).where(df[col].notna(), "")
    con_dato = serie != ""
    con_punto = serie.str.match(r"^\d+\.0$")
    sin_punto = serie.str.match(r"^\d+$")
    mask = con_dato & sin_punto & ~con_punto
    hallazgos = df[mask]
    nota = ("Numéricamente inofensivo (pd.to_numeric interpreta ambos formatos igual) -- "
            "riesgo solo para filtros por string exacto.") if mask.any() else None
    return _resultado(titulo, int(con_dato.sum()), len(df), hallazgos, cfg, max_ejemplos, nota=nota)


def check_nulos_campo(df, nombre, cfg, cfg_key, titulo, max_ejemplos, valores_placeholder=None):
    """Tasa de nulos reales (tag ausente en la descripción, ej. VE: no presente) en un
    campo declarativo. Distingue explícitamente de valores placeholder (ej. 'SIN VERSION',
    que SÍ es un valor declarado por el importador, no un vacío) -- valores_placeholder se
    reporta aparte en la nota y no cuenta como hallazgo."""
    col = cfg.get(cfg_key)
    if not col or col not in df.columns:
        return _no_aplica(titulo)

    nulos_reales = df[col].isna()
    hallazgos = df[nulos_reales]

    nota = None
    if valores_placeholder:
        placeholder_set = {v.upper() for v in valores_placeholder}
        serie_up = df[col].astype(str).str.upper().str.strip().where(df[col].notna(), "")
        es_placeholder = serie_up.isin(placeholder_set)
        n_ph = int(es_placeholder.sum())
        pct_ph = (n_ph / len(df) * 100) if len(df) else 0.0
        nota = (f"Valor declarado como {'/'.join(valores_placeholder)} (dato real, NO es nulo, "
                f"no cuenta como hallazgo): {n_ph:,} ({pct_ph:.2f}%)")

    return _resultado(titulo, len(df), len(df), hallazgos, cfg, max_ejemplos, nota=nota)


def check_peso_en_frontera_categoria(df, nombre, cfg, max_ejemplos):
    titulo = "Concentración de peso bruto exactamente en una frontera de categoría (patrón 'redondo de fábrica')"
    pb_col = cfg.get("peso_bruto")
    if not pb_col or pb_col not in df.columns:
        return _no_aplica(titulo)
    pb = to_num(df, pb_col)
    con_dato = pb.notna()
    n_eval = int(con_dato.sum())
    mask = con_dato & pb.isin(FRONTERAS_PESO_KG)
    hallazgos = df[mask]

    alertas = []
    if n_eval:
        for frontera in FRONTERAS_PESO_KG:
            n_frontera = int((pb == frontera).sum())
            pct = n_frontera / n_eval * 100
            if pct >= 1.0:
                alertas.append(f"{frontera:,}kg: {n_frontera:,} filas ({pct:.2f}%)")
    nota = ("[ALERTA] concentración >=1% en frontera(s) exacta(s): " + "; ".join(alertas)
            if alertas else
            "Sin concentración >=1% en ninguna frontera (alerta informativa, no es error binario "
            "-- una fila aislada en un valor de frontera no es en sí un problema).")

    return _resultado(titulo, n_eval, len(df), hallazgos, cfg, max_ejemplos,
                       extra_series=pb, extra_label=pb_col, nota=nota)


CHECKS = [
    lambda df, nombre, cfg, me, anio_actual: check_duplicados_exactos(df, nombre, cfg, me),
    lambda df, nombre, cfg, me, anio_actual: check_vin_duplicado_entre_dua(df, nombre, cfg, me),
    lambda df, nombre, cfg, me, anio_actual: check_formato_vin(df, nombre, cfg, me),
    lambda df, nombre, cfg, me, anio_actual: check_coherencia_peso(df, nombre, cfg, me),
    lambda df, nombre, cfg, me, anio_actual: check_rango(df, nombre, cfg, "anio_modelo", "Rango de año modelo", 1990, anio_actual + 1, me),
    lambda df, nombre, cfg, me, anio_actual: check_rango_anio_dua(df, nombre, cfg, me, anio_actual),
    lambda df, nombre, cfg, me, anio_actual: check_rango(df, nombre, cfg, "cilindrada", "Rango de cilindrada (cc)", 500, 20000, me),
    lambda df, nombre, cfg, me, anio_actual: check_rango(df, nombre, cfg, "num_cilindros", "Rango de número de cilindros", 1, 16, me),
    lambda df, nombre, cfg, me, anio_actual: check_rango(df, nombre, cfg, "ejes", "Rango de número de ejes", 2, 6, me),
    lambda df, nombre, cfg, me, anio_actual: check_rango(df, nombre, cfg, "largo", "Rango de largo (mm)", 2000, 20000, me),
    lambda df, nombre, cfg, me, anio_actual: check_rango(df, nombre, cfg, "ancho", "Rango de ancho (mm)", 1200, 3200, me),
    lambda df, nombre, cfg, me, anio_actual: check_rango(df, nombre, cfg, "alto", "Rango de alto (mm)", 1000, 4800, me),
    lambda df, nombre, cfg, me, anio_actual: check_descripcion_sin_parsear(df, nombre, cfg, me),
    lambda df, nombre, cfg, me, anio_actual: check_kg_bruto_vs_peso(df, nombre, cfg, me),
    lambda df, nombre, cfg, me, anio_actual: check_marca_fuera_vocab(df, nombre, cfg, me),
    lambda df, nombre, cfg, me, anio_actual: check_mojibake(df, nombre, cfg, me),
    lambda df, nombre, cfg, me, anio_actual: check_fob_cif(df, nombre, cfg, me),
    lambda df, nombre, cfg, me, anio_actual: check_carroceria_fuera_catalogo(df, nombre, cfg, me),
    lambda df, nombre, cfg, me, anio_actual: check_formato_anio_modelo(df, nombre, cfg, me),
    lambda df, nombre, cfg, me, anio_actual: check_nulos_campo(
        df, nombre, cfg, "version", "Nulos en 'version'", me, valores_placeholder=["SIN VERSION"]),
    lambda df, nombre, cfg, me, anio_actual: check_peso_en_frontera_categoria(df, nombre, cfg, me),
]


# ── Markdown ─────────────────────────────────────────────────────────────────

def escribir_markdown(path: Path, dataset_bloques: list[tuple[str, int, list[dict]]]):
    ahora = datetime.now()
    fecha_larga = _fecha_es(ahora.date())
    hora_str = ahora.strftime("%H:%M")

    resumen_exec = "\n".join(
        f"- **{nombre.title()}**: {total:,} filas, "
        f"{sum(r['hallazgos'] for r in resultados):,} hallazgos marcados en total"
        for nombre, total, resultados in dataset_bloques
    )

    cuerpo_datasets = []
    for nombre, total, resultados in dataset_bloques:
        cuerpo_datasets.append(f"## {nombre.title()} — {total:,} filas\n")
        cuerpo_datasets.extend(r["md"] for r in resultados)
        cuerpo_datasets.append(_resumen_dataset(nombre, resultados))

    if not path.exists():
        header = (
            "# Auditoría de Calidad de Datos — Veritrade Imports\n"
            f"**Fecha:** {fecha_larga}\n"
            "**Datasets:** " + ", ".join(f"{n} ({t:,} filas)" for n, t, _ in dataset_bloques) + "\n\n"
            "---\n\n"
            "## Resumen ejecutivo\n\n" + resumen_exec + "\n\n---\n\n"
        )
        cuerpo = header + "\n\n".join(cuerpo_datasets) + "\n\n---\n\n" + NOTAS_CODIGO
        path.write_text(cuerpo, encoding="utf-8")
    else:
        bloque = (
            f"\n---\n\n## Ejecución — {fecha_larga} {hora_str}\n\n"
            + resumen_exec + "\n\n"
            + "\n\n".join(cuerpo_datasets) + "\n\n"
            + NOTAS_CODIGO
        )
        with path.open("a", encoding="utf-8") as f:
            f.write(bloque)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-ejemplos", type=int, default=MAX_EJEMPLOS_DEFAULT,
                     help="Máximo de filas de ejemplo por check (default: 5)")
    ap.add_argument("--no-markdown", action="store_true",
                     help="No escribir/actualizar informe_calidad_datos.md")
    args = ap.parse_args()

    anio_actual = date.today().year
    datasets = [
        ("camiones", ROOT / "data" / "gold" / "camiones.parquet", CAMIONES_COLS),
        ("maquinaria", ROOT / "data" / "gold" / "maquinaria.parquet", MAQUINARIA_COLS),
    ]

    dataset_bloques = []
    for nombre, path, cfg in datasets:
        if not path.exists():
            print(f"AVISO: {path} no encontrado — se omite {nombre}")
            continue
        df = pd.read_parquet(path)

        print(f"\n{'=' * 65}")
        print(f"  CALIDAD DE DATOS — {nombre.upper()} ({len(df):,} filas)")
        print(f"{'=' * 65}")

        resultados = [check(df, nombre, cfg, args.max_ejemplos, anio_actual) for check in CHECKS]
        for r in resultados:
            print(r["md"])
        print(_resumen_dataset(nombre, resultados))

        dataset_bloques.append((nombre, len(df), resultados))

    if not dataset_bloques:
        print("No se encontró ningún parquet en data/gold/. Nada que validar.")
        return 1

    if not args.no_markdown:
        informe_path = ROOT / "informe_calidad_datos.md"
        escribir_markdown(informe_path, dataset_bloques)
        print(f"\n{'=' * 65}")
        print(f"  Informe actualizado: {informe_path.name}")
        print(f"{'=' * 65}\n")
    else:
        print("\n--no-markdown: no se escribió el informe.\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
