"""
scripts/generar_informe_auditoria_comercial.py
════════════════════════════════════════════════
Informe de Auditoria de Datos y Calidad Comercial (camiones) en 7 dimensiones,
pensado para responder: "¿puedo confiar en los indicadores comerciales que
salen de este archivo?"

"Categoria" y "Categoria Withmory" son las taxonomias reales del dashboard
(pages/2_Camiones.py::normalizar_carroceria / clasificar_segmento), NO
categoria_atu del pipeline -- ver plan de sesion 2026-07-08. Las funciones se
duplican aca (no se importa pages/2_Camiones.py directo porque es una pagina
Streamlit con codigo a nivel de modulo que espera correr con `streamlit run`).

Solo lectura -- no modifica ningun parquet/xlsx/dashboard.

Uso:
  uv run python scripts/generar_informe_auditoria_comercial.py
"""
from __future__ import annotations

import glob
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SILVER_DIR = ROOT / "data" / "silver"
GOLD_DIR = ROOT / "data" / "gold"

sys.path.insert(0, str(ROOT))
from pipeline.silver import PARTIDAS_CAMION  # noqa: E402,F401 (no se usa hoy, referencia futura)


# ═══════════════════════════════════════════════════════════════════════════
# Taxonomias del dashboard (duplicadas de pages/2_Camiones.py a proposito)
# ═══════════════════════════════════════════════════════════════════════════

def normalizar_carroceria(val) -> str:
    v = str(val).upper().strip().rstrip(",")
    if not v or v in ("NAN", "NONE", ""):
        return "OTROS"
    if any(k in v for k in ["TRACTO", "REMOLCADOR", "CABEZAL", "TRACTOREMOLCADOR"]):
        return "TRACTOCAMIÓN"
    if any(k in v for k in ["VOLQUETE", "VOLQUETA", "DUMPER", "TOLVA"]):
        return "VOLQUETE"
    if any(k in v for k in ["CHASIS CAB", "CHASIS MOT", "CHASIS MOTORIZ"]):
        return "CHASIS CABINA"
    if "CHASIS" in v and "CABINA" in v:
        return "CHASIS CABINA"
    if "CABINADO" in v:
        return "CHASIS CABINA"
    if "HORMIGON" in v or "MEZCLAD" in v or "MIXER" in v:
        return "HORMIGONERA"
    if "GRÚA" in v or "GRUA" in v or "AUXILIO MECANIC" in v:
        return "GRÚA"
    if "CISTERNA" in v or "TANQUE" in v:
        return "CISTERNA"
    if "FURGON" in v or "FURGÓN" in v:
        return "FURGÓN"
    if v.startswith("CHASIS"):
        return "CHASIS CABINA"
    return "OTROS"


def clasificar_segmento(pb) -> str:
    # NOTA: la funcion original en pages/2_Camiones.py tiene un bug real -- si pb
    # llega como float('nan') (no None, no string vacio), `float(nan)` NO lanza
    # excepcion y NaN <= 0 es False en Python, asi que cae sin querer hasta el
    # ultimo `return "PESADO"`. Confirmado 2026-07-08. Se corrige aca con un check
    # explicito de NaN para que este informe reporte el numero real; el dashboard
    # sigue con el bug sin corregir -- ver seccion 1.
    if pd.isna(pb):
        return "SIN DATO"
    try:
        pb = float(pb)
    except (TypeError, ValueError):
        return "SIN DATO"
    if pb <= 0:
        return "SIN DATO"
    if pb <= 6000:
        return "LDT 1"
    if pb <= 10000:
        return "LDT 2"
    if pb <= 15000:
        return "MDT 1"
    if pb <= 17000:
        return "MDT 2"
    if pb <= 25000:
        return "MDT 3"
    if pb <= 33000:
        return "SEMI PESADO"
    return "PESADO"


# ═══════════════════════════════════════════════════════════════════════════
# Carga de datos
# ═══════════════════════════════════════════════════════════════════════════

def _num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def cargar_excluidos_silver() -> pd.DataFrame:
    frames = []
    for f in sorted(glob.glob(str(SILVER_DIR / "*_qa.xlsx"))):
        try:
            df = pd.read_excel(f, sheet_name="_excluidos", dtype=str)
        except Exception:
            continue
        frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def cargar_validos_silver() -> pd.DataFrame:
    frames = [pd.read_parquet(f) for f in sorted(glob.glob(str(SILVER_DIR / "*_fase1.parquet")))]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def cargar_final() -> pd.DataFrame:
    return pd.read_parquet(GOLD_DIR / "camiones.parquet")


# ═══════════════════════════════════════════════════════════════════════════
# Secciones
# ═══════════════════════════════════════════════════════════════════════════

def seccion_1_totales_control(excl: pd.DataFrame, validos: pd.DataFrame, final: pd.DataFrame) -> str:
    out = ["## 1. Totales de Control (Integridad Absoluta)\n"]
    out.append("**Origen real de los datos: bronze de Veritrade (no hay un extracto SUNAT "
                "independiente contra el cual comparar) — el control es bronze → silver → "
                "gold → consolidado final, dentro de nuestro propio pipeline.**\n")

    bronze_total = len(excl) + len(validos)
    cif_bronze = _num(excl.get("cif_usd", pd.Series(dtype=float))).sum(skipna=True) + \
                 _num(validos.get("cif_usd", pd.Series(dtype=float))).sum(skipna=True)
    pb_bronze = _num(excl.get("peso_bruto_desc", pd.Series(dtype=float))).sum(skipna=True) + \
                _num(validos.get("peso_bruto_desc", pd.Series(dtype=float))).sum(skipna=True)

    cif_final = _num(final.get("cif_usd", pd.Series(dtype=float))).sum(skipna=True)
    pb_final = _num(final.get("peso_bruto_desc", pd.Series(dtype=float))).sum(skipna=True)

    tabla = pd.DataFrame([
        {"Etapa": "Bronze (crudo, incl. excluidos)", "Registros": bronze_total,
         "CIF Total USD": round(cif_bronze, 2), "Peso Bruto Total KG": round(pb_bronze, 2)},
        {"Etapa": "Válidas post-silver (a gold)", "Registros": len(validos),
         "CIF Total USD": round(_num(validos.get('cif_usd', pd.Series(dtype=float))).sum(skipna=True), 2),
         "Peso Bruto Total KG": round(_num(validos.get('peso_bruto_desc', pd.Series(dtype=float))).sum(skipna=True), 2)},
        {"Etapa": "Consolidado final (camiones.parquet)", "Registros": len(final),
         "CIF Total USD": round(cif_final, 2), "Peso Bruto Total KG": round(pb_final, 2)},
    ])
    out.append(tabla.to_string(index=False))
    out.append("")
    out.append(f"**Unidades finales: {len(final):,}** (1 fila = 1 unidad, deduplicado por DUA+VIN/chasis).\n")

    reduccion_pct = round((bronze_total - len(final)) / bronze_total * 100, 1) if bronze_total else 0
    out.append(f"Reducción bronze → final: **{reduccion_pct}%** (excluidas por partida no-camión, "
                "vans, duplicados, exclusiones de negocio como pickups — ver "
                "`scripts/auditar_embudo_importador.py` para el detalle por importador/razón.)\n")

    # Hallazgo: fallback a kg_bruto_col en el dashboard
    if "peso_bruto_desc" in final.columns and "kg_bruto_col" in final.columns:
        pb_nulo = final["peso_bruto_desc"].isna() | (_num(final["peso_bruto_desc"]).isna())
        kg_no_nulo = final["kg_bruto_col"].notna() & (_num(final["kg_bruto_col"]).notna())
        afectadas = (pb_nulo & kg_no_nulo).sum()
        pct = round(afectadas / len(final) * 100, 2) if len(final) else 0
        out.append(f"**[ALERTA] {afectadas:,} filas ({pct}%)** tienen `peso_bruto_desc` vacío pero "
                    "`kg_bruto_col` presente. El dashboard (`pages/2_Camiones.py::MAPEO_COLS`) usa "
                    "`kg_bruto_col` como fallback para calcular `segmento_peso` ('Categoría Withmory') "
                    "— pero `kg_bruto_col` es en realidad **peso neto**, no bruto (confirmado "
                    "2026-07-08, ver `informe_calidad_datos.md`). Estas filas probablemente están "
                    "en un segmento de peso más bajo del que les corresponde. No corregido en el "
                    "dashboard todavía — el pipeline (`categoria_atu`) ya no usa este fallback desde hoy.\n")

    n_sin_pb = final.get("peso_bruto_desc", pd.Series(dtype=object)).isna().sum()
    out.append(f"**[ALERTA] Bug confirmado en `pages/2_Camiones.py::clasificar_segmento()`:** cuando "
                f"`pb` llega como `NaN` (no `None`, no string vacío — un float `NaN` real, que es "
                f"exactamente cómo llegan los {n_sin_pb:,} valores faltantes desde el parquet), "
                "`float(pb)` NO lanza excepción y `NaN <= 0` da `False` en Python, así que la fila "
                "cae sin querer en el último `return \"PESADO\"` de la función — **el segmento más "
                "pesado**, no \"SIN DATO\". Confirmado y reproducido el 2026-07-08. Este informe usa "
                "una copia corregida de la función (ver comentario en el código fuente); el dashboard "
                "en producción sigue con el bug.\n")

    return "\n".join(out)


def seccion_2_cobertura(final: pd.DataFrame) -> str:
    out = ["## 2. Cobertura Comercial por Atributo (Completitud)\n"]
    n = len(final)

    def pct_no_nulo(serie: pd.Series) -> float:
        return round(serie.notna().mean() * 100, 1) if n else 0.0

    marca = pct_no_nulo(final.get("marca_norm", pd.Series(dtype=object)))
    modelo = pct_no_nulo(final.get("modelo_match", pd.Series(dtype=object)))
    carroceria = pct_no_nulo(final.get("carroceria_normalizada", pd.Series(dtype=object)))
    categoria = carroceria  # "Categoría" = misma cobertura que carroceria_normalizada antes de bucketizar
    pb = final.get("peso_bruto_desc", pd.Series(dtype=object))
    categoria_withmory = round((_num(pb).notna() & (_num(pb) > 0)).mean() * 100, 1) if n else 0.0

    tabla = pd.DataFrame([
        {"Atributo": "Marca", "Cobertura %": marca},
        {"Atributo": "Modelo", "Cobertura %": modelo},
        {"Atributo": "Carrocería", "Cobertura %": carroceria},
        {"Atributo": "Categoría (bucket de carrocería)", "Cobertura %": categoria},
        {"Atributo": "Categoría Withmory (segmento de peso, solo peso_bruto_desc)", "Cobertura %": categoria_withmory},
    ])
    out.append(tabla.to_string(index=False))
    out.append("")

    for nombre, val in [("Marca", marca), ("Modelo", modelo), ("Carrocería", carroceria),
                         ("Categoría", categoria), ("Categoría Withmory", categoria_withmory)]:
        if val < 95:
            out.append(f"**[ALERTA] {nombre} está en {val}%, por debajo del umbral de 95%.** "
                        f"Un vacío de este tamaño distorsiona los rankings de participación de mercado "
                        f"basados en {nombre.lower()}.\n")
    return "\n".join(out)


def seccion_3_no_clasificado(final: pd.DataFrame) -> str:
    out = ["## 3. Participación de \"No Clasificado\" (Riesgo de Sesgo)\n"]
    n = len(final)

    out.append("### Categoría (bucket de carrocería)\n")
    cat = final.get("carroceria_normalizada", pd.Series(dtype=object)).apply(normalizar_carroceria)
    tabla_cat = cat.value_counts().reset_index()
    tabla_cat.columns = ["Categoría", "Unidades"]
    out.append(tabla_cat.to_string(index=False))
    out.append("\n*Nota: \"OTROS\" mezcla carrocerías genuinamente distintas (ej. cisternas atípicas) "
                "con filas donde `carroceria_normalizada` estaba vacío — no es un \"no clasificado\" puro. "
                f"Vacíos reales dentro de OTROS: {(final.get('carroceria_normalizada', pd.Series(dtype=object)).isna()).sum():,}.*\n")

    out.append("\n### Categoría Withmory (segmento de peso)\n")
    pb = _num(final.get("peso_bruto_desc", pd.Series(dtype=object)))
    seg = pb.apply(clasificar_segmento)
    tabla_seg = seg.value_counts().reset_index()
    tabla_seg.columns = ["Categoría Withmory", "Unidades"]
    out.append(tabla_seg.to_string(index=False))

    sin_dato = (seg == "SIN DATO").sum()
    pct_sin_dato = round(sin_dato / n * 100, 1) if n else 0
    out.append("")
    if pct_sin_dato < 2:
        out.append(f"**Excelente**: {pct_sin_dato}% sin clasificar en Categoría Withmory.\n")
    elif pct_sin_dato > 15:
        out.append(f"**[ALERTA CRÍTICA] {pct_sin_dato}% de las unidades no tiene Categoría Withmory "
                    "(SIN DATO). Los informes de mercado por segmento de peso NO son confiables para "
                    "toma de decisiones gerenciales hasta reducir este porcentaje.**\n")
    else:
        out.append(f"{pct_sin_dato}% sin clasificar en Categoría Withmory — dentro de rango aceptable "
                    "pero vale la pena revisar (ver sección 4).\n")
    return "\n".join(out)


def seccion_4_top_sin_clasificar(final: pd.DataFrame, max_n: int = 100) -> str:
    out = [f"## 4. Top {max_n} Descripciones sin Clasificar (Guía de Acción del Parser)\n"]
    pb = _num(final.get("peso_bruto_desc", pd.Series(dtype=object)))
    sin_pb = final[pb.isna() | (pb <= 0)].copy()

    if sin_pb.empty:
        out.append("Sin filas pendientes — todo tiene `peso_bruto_desc`.\n")
        return "\n".join(out)

    desc = sin_pb["_descripcion"].astype(str)
    tiene_pb_code = desc.str.contains(r"\bPB\s*[:=]", case=False, regex=True, na=False)
    sin_pb_ausente = (~tiene_pb_code).sum()
    sin_pb_presente_no_parseado = tiene_pb_code.sum()

    out.append(f"Total filas sin `peso_bruto_desc`: **{len(sin_pb):,}**\n")
    out.append(f"- Código `PB:` **ausente** de la descripción (dato no capturado en origen): "
                f"{sin_pb_ausente:,} ({round(sin_pb_ausente/len(sin_pb)*100,1)}%)")
    out.append(f"- Código `PB:` **presente** pero no se pudo extraer un valor válido (posible bug del "
                f"parser, o descripción truncada antes del valor): "
                f"{sin_pb_presente_no_parseado:,} ({round(sin_pb_presente_no_parseado/len(sin_pb)*100,1)}%)\n")

    out.append("### Top marcas afectadas (dentro de las que no tienen PB: en absoluto)\n")
    sin_codigo = sin_pb[~tiene_pb_code]
    top_marcas = sin_codigo["marca_declarada"].value_counts().head(max_n)
    tabla = top_marcas.reset_index()
    tabla.columns = ["marca_declarada", "unidades_sin_PB_en_descripcion"]
    out.append(tabla.to_string(index=False))
    out.append(f"\nResolver las {min(max_n, len(tabla))} marcas de arriba cubre la mayoría de este "
                "bucket — si concentran >80% del total, confirma la heurística del 80/20 del enunciado "
                "original.\n")
    return "\n".join(out)


def seccion_5_ranking_vs_realidad(final: pd.DataFrame) -> str:
    out = ["## 5. Ranking contra la Realidad (Validación Manual y Consistencia)\n"]

    combo = final.groupby(["marca_norm", "modelo_match"], dropna=False).size().reset_index(name="unidades")
    combo = combo.sort_values("unidades", ascending=False).head(20)
    out.append("### Top 20 combinaciones Marca + Modelo\n")
    out.append(combo.to_string(index=False))

    # Cruce contra configuracion.xlsx (modelos conocidos por marca)
    try:
        modelos_cfg = pd.read_excel(ROOT / "configuracion.xlsx", sheet_name="modelos", dtype=str)
        conocidos = modelos_cfg.groupby("marca")["modelo"].apply(lambda s: set(s.dropna().str.upper().str.strip()))
        inconsistentes = []
        for _, r in combo.iterrows():
            marca, modelo = str(r["marca_norm"]).upper(), str(r["modelo_match"]).upper().strip()
            if marca in conocidos.index and modelo not in conocidos[marca]:
                inconsistentes.append((marca, modelo, r["unidades"]))
        out.append("\n### Combinaciones Marca-Modelo fuera del catálogo conocido (configuracion.xlsx)\n")
        if inconsistentes:
            tabla_inc = pd.DataFrame(inconsistentes, columns=["marca", "modelo", "unidades"])
            out.append(tabla_inc.to_string(index=False))
            out.append("\n*No implica error — puede ser un modelo nuevo legítimo no agregado aún al "
                        "catálogo. Revisar manualmente.*\n")
        else:
            out.append("Ninguna — las 20 combinaciones top están todas en el catálogo conocido.\n")
    except Exception as e:
        out.append(f"\n[No se pudo cruzar contra configuracion.xlsx: {e}]\n")

    out.append("\n### Protocolo de muestreo para validación manual\n")
    n_total = final["marca_norm"].notna().sum()
    z, p, e = 1.96, 0.5, 0.05
    n_muestra = (z**2 * p * (1 - p)) / (e**2)
    n_ajustado = n_muestra / (1 + (n_muestra - 1) / n_total) if n_total else n_muestra
    out.append(f"Con 95% de confianza y margen de error del 5% sobre {n_total:,} filas clasificadas, "
                f"el tamaño de muestra necesario es **{round(n_ajustado)} filas** "
                f"(fórmula `n = Z²·p·(1-p)/e²` con corrección por población finita). "
                "Tomar esa cantidad de filas al azar y verificar a mano Marca-Modelo-Categoría-Categoría "
                "Withmory contra el DUA original en Veritrade.\n")
    return "\n".join(out)


def seccion_6_fragmentacion_marcas(final: pd.DataFrame) -> str:
    out = ["## 6. Fragmentación de Marcas y Familias (Consolidación Comercial)\n"]
    marcas = final["marca_norm"].dropna().astype(str)
    conteo = marcas.value_counts()
    vistos = set()
    grupos = []
    for marca in conteo.index:
        if marca in vistos:
            continue
        raiz = marca.split()[0]
        similares = [m for m in conteo.index if m != marca and (raiz in m or marca in m) and len(raiz) > 3]
        if similares:
            grupo = [marca] + similares
            vistos.update(grupo)
            grupos.append(grupo)

    if not grupos:
        out.append("Sin fragmentación detectada por similitud de texto entre marcas normalizadas.\n")
        return "\n".join(out)

    for grupo in grupos:
        total = sum(conteo[m] for m in grupo)
        out.append(f"**{' / '.join(grupo)}** — total combinado: {total:,} unidades")
        for m in grupo:
            out.append(f"  - {m}: {conteo[m]:,}")
        out.append("")
    out.append("*Estas variantes probablemente son la misma marca comercial escrita distinto — "
                "consolidarlas evita subestimar su participación de mercado en los rankings.*\n")
    return "\n".join(out)


def seccion_7_impacto_economico(final: pd.DataFrame) -> str:
    out = ["## 7. Impacto Económico (Traducción Financiera de Errores)\n"]
    cif = _num(final.get("cif_usd", pd.Series(dtype=float))).fillna(0)
    cif_total = cif.sum()

    clasificado = (
        final["marca_norm"].notna()
        & final["carroceria_normalizada"].notna()
        & _num(final.get("peso_bruto_desc", pd.Series(dtype=object))).notna()
    )
    cif_clasificado = cif[clasificado].sum()
    cif_no_clasificado = cif_total - cif_clasificado
    pct_no_clasificado = round(cif_no_clasificado / cif_total * 100, 1) if cif_total else 0

    tabla = pd.DataFrame([
        {"Categoría": "CIF Clasificado (Marca+Categoría+Cat.Withmory completos)",
         "USD": round(cif_clasificado, 2), "%": round(100 - pct_no_clasificado, 1)},
        {"Categoría": "CIF No Clasificado / Erróneo",
         "USD": round(cif_no_clasificado, 2), "%": pct_no_clasificado},
        {"Categoría": "TOTAL", "USD": round(cif_total, 2), "%": 100.0},
    ])
    out.append(tabla.to_string(index=False))
    out.append("")

    if pct_no_clasificado > 15:
        out.append(f"**[ALERTA DE ALTO RIESGO FINANCIERO] El {pct_no_clasificado}% del capital CIF "
                    "analizado (US$ {:,.0f}) está en registros no clasificados o erróneos. Las "
                    "proyecciones comerciales basadas en este dataset tienen un riesgo financiero "
                    "significativo hasta reducir este porcentaje.**\n".format(cif_no_clasificado))
    elif pct_no_clasificado > 5:
        out.append(f"{pct_no_clasificado}% del CIF sin clasificar completamente — moderado, revisar "
                    "antes de reportes de alto impacto (juntas directivas, proyecciones anuales).\n")
    else:
        out.append(f"{pct_no_clasificado}% del CIF sin clasificar — bajo, no representa riesgo "
                    "financiero material.\n")
    return "\n".join(out)


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

def main() -> int:
    print("Cargando datos...")
    excl = cargar_excluidos_silver()
    validos = cargar_validos_silver()
    final = cargar_final()

    if final.empty:
        print("No se encontró data/gold/camiones.parquet. Correr el pipeline primero.")
        return 1

    secciones = [
        seccion_1_totales_control(excl, validos, final),
        seccion_2_cobertura(final),
        seccion_3_no_clasificado(final),
        seccion_4_top_sin_clasificar(final),
        seccion_5_ranking_vs_realidad(final),
        seccion_6_fragmentacion_marcas(final),
        seccion_7_impacto_economico(final),
    ]

    encabezado = (
        "# Informe de Auditoría de Datos y Calidad Comercial — Camiones\n"
        f"**Fecha de generación:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"**Dataset:** `data/gold/camiones.parquet` ({len(final):,} filas)\n\n"
        "Pregunta que este informe busca responder: **¿puedo confiar en los indicadores "
        "comerciales (participación de mercado, rankings, tendencias por carrocería) que "
        "salen de este archivo?**\n\n"
        "---\n"
    )

    contenido = encabezado + "\n\n---\n\n".join(secciones)
    out_path = ROOT / "informe_auditoria_comercial.md"
    out_path.write_text(contenido, encoding="utf-8")

    print(f"\n{'='*60}")
    print(f"  Informe generado: {out_path.name}")
    print(f"{'='*60}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
