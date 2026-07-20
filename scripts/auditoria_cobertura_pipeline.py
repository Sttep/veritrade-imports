"""
scripts/auditoria_cobertura_pipeline.py
════════════════════════════════════════
Auditoría de cobertura real del pipeline (marca/modelo/categoría): mide qué
fracción de camiones.parquet tiene marca/modelo presentes en el vocabulario
actual (configuracion.xlsx) -- NO valida si la clasificación es correcta,
solo si el dato está cubierto por el vocabulario.

Por qué existe: `marca_in_vocab`/`modelo_flag` en data/gold/camiones.parquet NO
son señal confiable de cobertura. pipeline/gold.py (líneas ~135-147) las
hardcodea a True/"reglas_alta" cuando `confianza=="alta"` en silver, sin
validar nada contra el vocabulario real -- solo ~0.1% de las filas pasan de
verdad por el LLM/validación. Este script recalcula la cobertura real
revalidando marca_norm/modelo_match contra configuracion.xlsx (el mismo
vocabulario que usa el pipeline).

Alcance de esta iteración (deliberadamente acotado, ver plan de sesión):
  Fase 1 -- corregir la métrica de cobertura (marca/modelo en vocabulario)
  Fase 4 -- cobertura por categoría (carroceria_normalizada), peor a mejor
  Fase 3 -- filas fuera de vocabulario agrupadas por descripción, por frecuencia
  Conflictos entre fuentes de evidencia -- partida arancelaria, CA: declarado,
    descripción completa y resultado del parser se tratan como señales
    independientes que "sugieren" un tipo, NUNCA como la respuesta correcta.
    Se reportan conflictos/compatibilidades observables (con un índice de
    consenso que mide convergencia, no confianza), y un patrón por modelo para
    encontrar anomalías -- sin decidir cuál señal tiene razón ni proponer
    cambios al parser/diccionario.

NO incluye (a propósito, se evalúa después según estos resultados):
  excluidos de silver, comparación Bronze vs Silver, caché de bronze. Ver
  scripts/generar_informe_auditoria_comercial.py y
  scripts/auditar_embudo_importador.py para esos patrones si se retoma.

Solo lectura -- no modifica pipeline/, configuracion.xlsx, vocab_extra.json ni datos.

Uso:
  uv run python scripts/auditoria_cobertura_pipeline.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
GOLD_DIR = ROOT / "data" / "gold"
CONFIG_PATH = ROOT / "configuracion.xlsx"
OUT_XLSX = ROOT / "auditoria_cobertura_pipeline.xlsx"

sys.path.insert(0, str(ROOT))
from pipeline.silver import Config  # noqa: E402


def cargar_final() -> pd.DataFrame:
    return pd.read_parquet(GOLD_DIR / "camiones.parquet")


# ═══════════════════════════════════════════════════════════════════════════
# Fase 1 -- métrica de cobertura corregida
# ═══════════════════════════════════════════════════════════════════════════

def enriquecer_cobertura_real(final: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Agrega columnas de cobertura basadas en presencia real en el vocabulario
    de configuracion.xlsx -- no en marca_in_vocab/modelo_flag (contaminados,
    ver pipeline/gold.py:135-147).

    categoria_asignada mide solo no-nulidad de carroceria_normalizada, no
    presencia en un vocabulario -- esta columna NO valida si la clasificación
    es correcta, solo si el pipeline asignó algo.
    """
    final = final.copy()

    marcas_validas = set(cfg.marca_map.values())
    final["marca_en_vocabulario"] = (
        final["marca_norm"].notna()
        & final["marca_norm"].astype(str).str.upper().str.strip().isin(marcas_validas)
    )

    modelos_por_marca = {m: frozenset(s) for m, s in cfg.modelos.items()}
    marca_up = final["marca_norm"].astype(str).str.upper().str.strip()
    modelo_up = final["modelo_match"].astype(str).str.upper().str.strip()

    def _modelo_en_vocabulario(marca: str, modelo: str, tiene_modelo: bool) -> bool:
        if not tiene_modelo:
            return False
        return modelo in modelos_por_marca.get(marca, frozenset())

    final["modelo_en_vocabulario"] = [
        _modelo_en_vocabulario(m, mo, tiene)
        for m, mo, tiene in zip(marca_up, modelo_up, final["modelo_match"].notna())
    ]

    final["categoria_asignada"] = final["carroceria_normalizada"].notna()

    return final


def fase1_tabla_contaminacion(final: pd.DataFrame) -> pd.DataFrame:
    """Cuantifica cuántas filas cambian de estado al pasar de los flags
    contaminados de gold (marca_in_vocab/modelo_flag) a la métrica real."""
    filas = []

    marca_flag_viejo = final["marca_in_vocab"].fillna(False).astype(bool)
    filas.append({
        "campo": "marca",
        "segun_flag_viejo_gold": int(marca_flag_viejo.sum()),
        "segun_vocabulario_real": int(final["marca_en_vocabulario"].sum()),
        "filas_que_cambian_de_estado": int((marca_flag_viejo != final["marca_en_vocabulario"]).sum()),
    })

    modelo_flag_viejo = ~final["modelo_flag"].isin(["low", "nomatch", "alias"])
    filas.append({
        "campo": "modelo",
        "segun_flag_viejo_gold": int(modelo_flag_viejo.sum()),
        "segun_vocabulario_real": int(final["modelo_en_vocabulario"].sum()),
        "filas_que_cambian_de_estado": int((modelo_flag_viejo != final["modelo_en_vocabulario"]).sum()),
    })

    return pd.DataFrame(filas)


# ═══════════════════════════════════════════════════════════════════════════
# Fase 4 -- cobertura por categoría
# ═══════════════════════════════════════════════════════════════════════════

def fase4_cobertura_por_categoria(final: pd.DataFrame) -> pd.DataFrame:
    df = final.copy()
    df["categoria"] = df["carroceria_normalizada"].fillna("SIN CATEGORIA (nulo)")

    g = df.groupby("categoria", observed=True)
    tabla = g.agg(
        total=("categoria", "size"),
        marca_en_vocabulario=("marca_en_vocabulario", "sum"),
        modelo_en_vocabulario=("modelo_en_vocabulario", "sum"),
    ).reset_index()

    tabla["pct_marca_en_vocabulario"] = (tabla["marca_en_vocabulario"] / tabla["total"] * 100).round(1)
    tabla["pct_modelo_en_vocabulario"] = (tabla["modelo_en_vocabulario"] / tabla["total"] * 100).round(1)

    fuera_vocab = ~(df["marca_en_vocabulario"] & df["modelo_en_vocabulario"] & df["categoria_asignada"])
    tabla["fuera_de_vocabulario"] = (
        df.assign(_fv=fuera_vocab).groupby("categoria", observed=True)["_fv"].sum().values
    )
    tabla["pct_fuera_de_vocabulario"] = (tabla["fuera_de_vocabulario"] / tabla["total"] * 100).round(1)

    return tabla.sort_values("pct_fuera_de_vocabulario", ascending=False).reset_index(drop=True)


# ═══════════════════════════════════════════════════════════════════════════
# Fase 3 -- filas fuera de vocabulario agrupadas por descripción
# ═══════════════════════════════════════════════════════════════════════════

def fase3_fuera_de_vocabulario_por_descripcion(final: pd.DataFrame) -> pd.DataFrame:
    fuera_vocab = ~(final["marca_en_vocabulario"] & final["modelo_en_vocabulario"] & final["categoria_asignada"])
    df = final[fuera_vocab].copy()

    def _atributo(row) -> str:
        faltan = []
        if not row["marca_en_vocabulario"]:
            faltan.append("marca")
        if not row["modelo_en_vocabulario"]:
            faltan.append("modelo")
        if not row["categoria_asignada"]:
            faltan.append("categoria")
        return "+".join(faltan)

    df["atributo_fuera_de_vocabulario"] = df.apply(_atributo, axis=1)

    tabla = (
        df.groupby("_descripcion", observed=True)
        .agg(
            cantidad=("_descripcion", "size"),
            carroceria_normalizada=("carroceria_normalizada", "first"),
            marca_norm=("marca_norm", "first"),
            modelo_match=("modelo_match", "first"),
            atributo_fuera_de_vocabulario=("atributo_fuera_de_vocabulario", "first"),
        )
        .reset_index()
        .sort_values("cantidad", ascending=False)
        .reset_index(drop=True)
    )
    return tabla


def fase3b_modelos_fuera_vocab_por_marca(final: pd.DataFrame) -> pd.DataFrame:
    """Distribucion por marca de las filas con modelo fuera de vocabulario:
    cuantas marcas concentran el problema, cobertura de modelo por marca,
    modelos unicos faltantes por marca, y si hay ley de Pareto."""
    df = final.copy()
    df["marca_norm"] = df["marca_norm"].fillna("SIN MARCA")

    total_por_marca = df.groupby("marca_norm", observed=True).size()
    fuera = df[~df["modelo_en_vocabulario"]]

    tabla = fuera.groupby("marca_norm", observed=True).agg(
        filas_modelo_fuera_vocab=("marca_norm", "size"),
        modelos_unicos_faltantes=("modelo_match", "nunique"),
    ).reset_index()

    tabla["filas_totales_marca"] = tabla["marca_norm"].map(total_por_marca)
    tabla["pct_modelo_fuera_vocab_de_la_marca"] = (
        tabla["filas_modelo_fuera_vocab"] / tabla["filas_totales_marca"] * 100
    ).round(1)

    tabla = tabla.sort_values("filas_modelo_fuera_vocab", ascending=False).reset_index(drop=True)

    total_fuera = tabla["filas_modelo_fuera_vocab"].sum()
    tabla["pct_del_total_fuera_vocab"] = (tabla["filas_modelo_fuera_vocab"] / total_fuera * 100).round(1)
    tabla["pct_acumulado"] = tabla["pct_del_total_fuera_vocab"].cumsum().round(1)

    return tabla[[
        "marca_norm", "filas_totales_marca", "filas_modelo_fuera_vocab",
        "pct_modelo_fuera_vocab_de_la_marca", "modelos_unicos_faltantes",
        "pct_del_total_fuera_vocab", "pct_acumulado",
    ]]


def _normalizacion_laxa(s: str) -> str:
    """Quita todo lo que no sea letra/numero -- para detectar claves que solo
    difieren por guiones, espacios, comas, puntos, etc."""
    return re.sub(r"[^A-Z0-9]", "", s.upper())


def detectar_mismatches_clave_marca_modelo(cfg: Config, final: pd.DataFrame) -> pd.DataFrame:
    """Para cada marca normalizada (cfg.marca_map.values()) que tenga al menos
    una fila con modelo_match en camiones.parquet, compara la clave esperada
    (la marca normalizada) contra las claves reales de cfg.modelos, y clasifica:
      - "ok_clave_exacta": la clave normalizada existe tal cual en cfg.modelos.
      - "mismatch_normalizacion": no existe tal cual, pero SI existe una clave
        en cfg.modelos que es igual quitando guiones/espacios/puntuacion
        (mismo problema que Mercedes-Benz: MERCEDES-BENZ vs MERCEDES BENZ).
      - "sin_entrada_modelos": no hay ninguna clave de cfg.modelos (ni exacta
        ni laxa) para esa marca -- el diccionario de modelos genuinamente no
        tiene nada cargado para ella.
    "filas_afectadas" cuenta filas con marca_norm==esa marca Y modelo_match no
    nulo -- son las filas que HOY se evaluan contra un set vacio de modelos
    (por mismatch o por ausencia real), independientemente de si el modelo en
    si mismo esta bien escrito.
    """
    marcas_normalizadas = sorted(set(cfg.marca_map.values()))
    modelos_keys = set(cfg.modelos.keys())
    laxa_a_claves: dict[str, list[str]] = {}
    for k in modelos_keys:
        laxa_a_claves.setdefault(_normalizacion_laxa(k), []).append(k)

    filas_por_marca = final.groupby(final["marca_norm"].fillna("SIN MARCA")).apply(
        lambda g: int(g["modelo_match"].notna().sum()), include_groups=False
    )

    resultados = []
    for marca in marcas_normalizadas:
        filas_afectadas = int(filas_por_marca.get(marca, 0))
        if filas_afectadas == 0:
            continue  # marca sin ninguna fila con modelo extraido -- no aporta evidencia

        if marca in modelos_keys:
            estado = "ok_clave_exacta"
            clave_real = marca
            n_modelos = len(cfg.modelos[marca])
        else:
            laxa = _normalizacion_laxa(marca)
            candidatas = laxa_a_claves.get(laxa, [])
            if candidatas:
                estado = "mismatch_normalizacion"
                clave_real = ", ".join(candidatas)
                n_modelos = sum(len(cfg.modelos[c]) for c in candidatas)
            else:
                estado = "sin_entrada_modelos"
                clave_real = ""
                n_modelos = 0

        resultados.append({
            "marca_normalizada": marca,
            "estado": estado,
            "clave_real_en_modelos": clave_real,
            "modelos_en_esa_clave": n_modelos,
            "filas_afectadas": filas_afectadas,
        })

    tabla = pd.DataFrame(resultados).sort_values(
        ["estado", "filas_afectadas"], ascending=[True, False]
    ).reset_index(drop=True)
    return tabla


# ═══════════════════════════════════════════════════════════════════════════
# Conflictos entre fuentes de evidencia (ninguna es ground truth)
#
# Premisa: la pregunta es "¿donde existen desacuerdos entre fuentes de
# evidencia?", no "¿donde falla la clasificacion?". Ninguna fuente (partida,
# CA: declarado, descripcion, ni el resultado del parser) se trata como la
# respuesta correcta -- cada una "sugiere" un tipo, nunca "es" un tipo. Las
# fuentes tampoco son estadisticamente independientes entre si (el parser
# deriva parcialmente del mismo texto de CA: que se usa como fuente aparte) --
# el objetivo es detectar conflictos observables, no medir independencia.
# ═══════════════════════════════════════════════════════════════════════════

# Mapeo partida -> tipo sugerido. Fuente: Nomenclatura Arancelaria (Sistema
# Armonizado, capitulo 87) -- EXTERNA al diccionario `carrocerias` del pipeline,
# pero es en si misma una HIPOTESIS de esta auditoria (una interpretacion de la
# nomenclatura), no una verdad -- puede tener errores, casos limite, o
# declaraciones de origen incorrectas que la nomenclatura no puede detectar.
# 8701.21/23/29 = tractores de carretera para semirremolques (definicion HS de
#   tracto-camion). 8704.10/60 = volquetes para uso fuera de carretera.
# 8704.21/22/23/31/32 = camiones generales, subdivididos por peso/motor, NO por
#   carroceria -- esa subpartida deliberadamente no sugiere nada.
# 8705.10 = camion grua. 8705.40 = camion hormigonera. 8705.90 = "los demas"
#   vehiculos especiales, catch-all sin un tipo unico -- no discrimina.
# 8706.00 = chasis con motor, carroceria aun no definida en esa etapa.
_PARTIDA_A_SENAL = {
    "8701210000": "TRACTO", "8701230000": "TRACTO", "8701290000": "TRACTO",
    "8704100000": "VOLQUETE", "8704601000": "VOLQUETE",
    "8705100000": "GRUA",
    "8705400000": "HORMIGONERA",
    "8706009200": "CHASIS_CON_MOTOR", "8706009900": "CHASIS_CON_MOTOR",
}


def derivar_senal_partida(partida) -> str:
    """La partida arancelaria SUGIERE un tipo -- ver _PARTIDA_A_SENAL arriba
    para la fuente y las limitaciones. Devuelve NO_DISCRIMINA para cualquier
    partida no listada ahi (el grueso de las filas, camion generico por
    peso/motor) -- nunca fuerza una categoria sin respaldo."""
    return _PARTIDA_A_SENAL.get(str(partida).strip(), "NO_DISCRIMINA")


# Vocabulario de esta auditoria (independiente del diccionario `carrocerias`
# del pipeline) para escanear texto libre -- compartido entre la senal de CA:
# y la de descripcion completa, para que sean comparables entre si. Patrones
# con \b para evitar falsos positivos ya conocidos (ej. "TRACTO" adentro de
# "EXTRACTOR").
_EVIDENCIA_PATRONES: dict[str, re.Pattern] = {
    "TRACTO": re.compile(
        r"TRACTOCAMI[OÓ]N|TRACTOREMOLCADOR|\bREMOLCADOR\b|\bCABEZAL\b|\bTRACTO\b"
        r"|5TA RUEDA|QUINTA RUEDA|5RA RUEDA"
    ),
    "VOLQUETE": re.compile(r"\bVOLQUETE\b|\bVOLQUETA\b|\bDUMPER\b|\bTOLVA\b"),
    "HORMIGONERA": re.compile(r"HORMIGON|MEZCLAD|\bMIXER\b|CONCRETE MIXER"),
    "GRUA": re.compile(r"\bGR[UÚ]A\b|\bCRANE\b"),
    "CISTERNA": re.compile(r"\bCISTERNA\b|\bTANQUE\b"),
    "CHASIS": re.compile(r"CHASIS CAB|CHASIS MOTORIZ|CHASIS MOT"),
    "COMPACTADOR": re.compile(r"COMPACTADOR|\bRODILLO\b"),
}

# Traduce el resultado del parser (carroceria_normalizada) al mismo espacio de
# tipos que las demas senales, para que sean comparables. Es una senal mas, no
# la respuesta a validar.
_PARSER_A_SENAL = {
    "TRACTOCAMIÓN": "TRACTO", "CHASIS CABINA": "CHASIS", "VOLQUETE": "VOLQUETE",
    "HORMIGONERA": "HORMIGONERA", "MEZCLADORA": "HORMIGONERA",
    "CISTERNA": "CISTERNA", "COMPACTADOR": "COMPACTADOR", "GRÚA": "GRUA",
    "OTROS": "OTROS",
}


def derivar_evidencia_texto(texto) -> set[str]:
    """Evidencia ENCONTRADA en el texto (CA: o descripcion completa) -- no una
    categoria forzada. Puede devolver vacio, un tipo, o varios si el texto
    menciona mas de uno (eso en si mismo es una observacion, no se colapsa a
    "el mas probable")."""
    t = str(texto or "").upper()
    return {tipo for tipo, patron in _EVIDENCIA_PATRONES.items() if patron.search(t)}


def evaluar_compatibilidad_fila(senales: dict[str, set]) -> dict:
    """Combina las senales disponibles (conjuntos no vacios) de una fila.
    Evalua COMPATIBILIDAD de evidencia, no igualdad -- por eso los estados no
    se llaman "coinciden"/"no_coinciden". indice_consenso mide unicamente
    convergencia entre senales, NO confianza ni probabilidad de acierto: un
    4/4 no prueba que la fila este bien clasificada (las 4 fuentes podrian
    compartir el mismo error de origen); un 2/4 no prueba que este mal."""
    utilizables = {nombre: conj for nombre, conj in senales.items() if conj}
    n = len(utilizables)

    if n < 2:
        return {
            "n_evidencias_utilizables": n,
            "estado": "evidencia_insuficiente",
            "indice_consenso": None,
            "pares_en_conflicto": "",
        }

    nombres = list(utilizables.keys())
    pares_conflicto = []
    for i in range(len(nombres)):
        for j in range(i + 1, len(nombres)):
            a, b = nombres[i], nombres[j]
            if not (utilizables[a] & utilizables[b]):
                pares_conflicto.append(f"{a} vs {b}")

    interseccion_total = set.intersection(*utilizables.values())
    estado = "compatibles" if interseccion_total else "conflictivas"

    conteo_tipos: dict[str, int] = {}
    for conj in utilizables.values():
        for tipo in conj:
            conteo_tipos[tipo] = conteo_tipos.get(tipo, 0) + 1
    tipo_mas_frecuente = max(conteo_tipos, key=conteo_tipos.get)
    k = sum(1 for conj in utilizables.values() if tipo_mas_frecuente in conj)

    return {
        "n_evidencias_utilizables": n,
        "estado": estado,
        "indice_consenso": f"{k}/{n}",
        "pares_en_conflicto": "; ".join(pares_conflicto),
    }


def detectar_conflictos_entre_senales(final: pd.DataFrame) -> pd.DataFrame:
    """Por fila, deriva las 4 senales y evalua su compatibilidad. Nunca oculta
    el detalle de cada senal detras del resultado agregado."""
    df = final.copy()

    senal_partida = df["partida"].apply(derivar_senal_partida)
    senal_ca = df["carroceria"].apply(derivar_evidencia_texto)
    senal_desc = df["_descripcion"].apply(derivar_evidencia_texto)
    senal_parser = df["carroceria_normalizada"].map(_PARSER_A_SENAL)

    filas = []
    for i in range(len(df)):
        sp = senal_partida.iloc[i]
        senales = {
            "partida": set() if sp == "NO_DISCRIMINA" else {sp},
            "CA": senal_ca.iloc[i],
            "descripcion": senal_desc.iloc[i],
            "parser": set() if pd.isna(senal_parser.iloc[i]) else {senal_parser.iloc[i]},
        }
        resultado = evaluar_compatibilidad_fila(senales)
        resultado.update({
            "dua_dam": df["dua_dam"].iloc[i],
            "marca_norm": df["marca_norm"].iloc[i],
            "modelo_match": df["modelo_match"].iloc[i],
            "senal_partida": sp,
            "senal_CA": ", ".join(sorted(senales["CA"])) if senales["CA"] else "",
            "senal_descripcion": ", ".join(sorted(senales["descripcion"])) if senales["descripcion"] else "",
            "senal_parser": senal_parser.iloc[i] if pd.notna(senal_parser.iloc[i]) else "",
            "carroceria_normalizada": df["carroceria_normalizada"].iloc[i],
        })
        filas.append(resultado)

    cols = [
        "dua_dam", "marca_norm", "modelo_match", "carroceria_normalizada",
        "senal_partida", "senal_CA", "senal_descripcion", "senal_parser",
        "n_evidencias_utilizables", "estado", "indice_consenso", "pares_en_conflicto",
    ]
    return pd.DataFrame(filas)[cols]


def fase_resumen_conflictos(resultado: pd.DataFrame) -> pd.DataFrame:
    """Agregado descriptivo: NO decide cual senal tiene razon. Cruza estado
    con n_evidencias_utilizables (separa conflictos fuertes de debiles) y
    reporta la distribucion del indice_consenso -- recordando que ese indice
    mide convergencia, no confianza."""
    resumen = (
        resultado.groupby(["estado", "n_evidencias_utilizables"], observed=True)
        .size()
        .reset_index(name="filas")
        .sort_values(["estado", "n_evidencias_utilizables"])
        .reset_index(drop=True)
    )
    return resumen


def fase_resumen_pares_en_conflicto(resultado: pd.DataFrame) -> pd.DataFrame:
    """Que PARES de senales estan en conflicto con mas frecuencia -- para
    saber donde mirar despues, sin decidir todavia que esta "mal"."""
    conflictivas = resultado[resultado["estado"] == "conflictivas"]
    pares = conflictivas["pares_en_conflicto"].str.split("; ").explode()
    pares = pares[pares != ""]
    return (
        pares.value_counts()
        .rename_axis("par_de_senales")
        .reset_index(name="filas")
        .sort_values("filas", ascending=False)
        .reset_index(drop=True)
    )


def _entropia_normalizada(counts: pd.Series) -> float:
    """Entropia de Shannon de una distribucion, normalizada a [0,1] por
    log(n_categorias). 0 = toda la masa en una categoria (poca incertidumbre
    estructural); 1 = repartido lo mas parejo posible. No decide si la
    variabilidad es "buena" o "mala" -- solo la mide."""
    n = len(counts)
    if n < 2:
        return 0.0
    p = counts / counts.sum()
    entropia = -(p * np.log(p)).sum()
    return float(entropia / np.log(n))


def fase_patrones_por_modelo(final: pd.DataFrame) -> pd.DataFrame:
    """No decide nada -- busca ANOMALIAS a nivel de patron, no casos
    individuales. Distribucion % de carroceria_normalizada (la senal del
    parser) por (marca_norm, modelo_match), mas indice_variabilidad (entropia
    normalizada) para tener una medida continua de dispersion, no solo el %
    de la categoria dominante. Ordenado por indice_variabilidad descendente
    (mas "anomalas"/parejas primero) -- son las que ameritan mirar el detalle
    por fila.

    Nota de arquitectura: por ahora solo agrega la distribucion del parser;
    esta pensada para que sumar la distribucion de las demas senales (partida,
    CA:, descripcion) sea extender este mismo groupby, no reescribir la
    funcion."""
    df = final.copy()
    df["categoria"] = df["carroceria_normalizada"].fillna("SIN_CATEGORIA")
    df = df[df["modelo_match"].notna() & (df["modelo_match"].astype(str).str.strip() != "")]

    filas = []
    for (marca, modelo), g in df.groupby(["marca_norm", "modelo_match"], observed=True):
        counts = g["categoria"].value_counts()
        if len(counts) < 2:
            continue
        total = int(counts.sum())
        pct = (counts / total * 100).round(1)
        filas.append({
            "marca_norm": marca,
            "modelo_match": modelo,
            "n_filas": total,
            "n_categorias_distintas": len(counts),
            "pct_categoria_dominante": float(pct.iloc[0]),
            "indice_variabilidad": round(_entropia_normalizada(counts), 3),
            "distribucion_parser": ", ".join(f"{p}% {c}" for c, p in pct.items()),
        })

    tabla = pd.DataFrame(filas)
    if tabla.empty:
        return tabla
    return tabla.sort_values("indice_variabilidad", ascending=False).reset_index(drop=True)


def detectar_claves_duplicadas_carrocerias(config_path: Path) -> pd.DataFrame:
    """Relee la hoja `carrocerias` de configuracion.xlsx SIN pasar por Config
    (para ver el estado antes del colapso a dict por orden de lectura), agrupa
    por clave normalizada y filtra las que mapean a mas de un valor distinto.
    Ya confirmado el caso "CHASIS CABINADO,"."""
    xl = pd.ExcelFile(config_path)
    df = xl.parse("carrocerias", dtype=str).dropna()
    cols = df.columns.tolist()
    clave = df[cols[0]].astype(str).str.upper().str.strip()
    valor = df[cols[1]].astype(str).str.upper().str.strip()

    agrupado = pd.DataFrame({"clave": clave, "valor": valor}).groupby("clave")["valor"].agg(
        lambda s: sorted(set(s))
    ).reset_index()
    agrupado["n_valores_distintos"] = agrupado["valor"].apply(len)
    conflictos = agrupado[agrupado["n_valores_distintos"] > 1].rename(
        columns={"valor": "valores_en_conflicto"}
    )
    return conflictos.reset_index(drop=True)


# ═══════════════════════════════════════════════════════════════════════════
# Caracterizacion de incertidumbre del sistema (no busqueda de bugs)
#
# Cambio de pregunta: no "donde esta el error" sino "donde toma decisiones el
# pipeline con alta, parcial o baja convergencia de evidencia -- y por que
# (insuficiencia de evidencia, reglas del diccionario poco usadas o demasiado
# generales, o variabilidad real del resultado)". No se decide cual senal
# tiene razon ni se proponen cambios al parser/diccionario.
# ═══════════════════════════════════════════════════════════════════════════

def derivar_nivel_evidencia(n_evidencias_utilizables: int, estado: str) -> str:
    """Reinterpreta el resultado de detectar_conflictos_entre_senales como un
    nivel de CONVERGENCIA de evidencia -- no una probabilidad de acierto.
    Calibrado empiricamente contra la distribucion real de indice_consenso
    (compatibles siempre da consenso 1.0 por construccion; conflictivas solo
    aparece en 3/4 o 1/2 en los datos actuales)."""
    if estado == "evidencia_insuficiente":
        return "no_evaluable"
    if estado == "compatibles":
        return "alta_convergencia" if n_evidencias_utilizables >= 3 else "convergencia_parcial"
    # conflictivas
    return "convergencia_parcial" if n_evidencias_utilizables >= 3 else "baja_convergencia"


def fase_nivel_evidencia_por_fila(conflictos: pd.DataFrame) -> pd.DataFrame:
    df = conflictos.copy()
    df["nivel_evidencia"] = [
        derivar_nivel_evidencia(n, e)
        for n, e in zip(df["n_evidencias_utilizables"], df["estado"])
    ]
    return df


_NIVELES_EVIDENCIA = ["alta_convergencia", "convergencia_parcial", "baja_convergencia", "no_evaluable"]


def fase_evidencia_por_categoria(niveles: pd.DataFrame) -> pd.DataFrame:
    """Por categoria (carroceria_normalizada), % de filas en cada nivel de
    convergencia. Hipotesis a VERIFICAR con datos, no asumida: OTROS
    probablemente concentra mas no_evaluable -- se reporta el numero, no se da
    por sentado."""
    df = niveles.copy()
    df["categoria"] = df["carroceria_normalizada"].fillna("SIN_CATEGORIA")

    tabla = df.groupby(["categoria", "nivel_evidencia"], observed=True).size().unstack(fill_value=0)
    for col in _NIVELES_EVIDENCIA:
        if col not in tabla.columns:
            tabla[col] = 0
    tabla = tabla[_NIVELES_EVIDENCIA]
    tabla["total"] = tabla.sum(axis=1)
    for col in _NIVELES_EVIDENCIA:
        tabla[f"pct_{col}"] = (tabla[col] / tabla["total"] * 100).round(1)

    return tabla.reset_index().sort_values("pct_no_evaluable", ascending=False).reset_index(drop=True)


def instrumentar_uso_reglas_carroceria(cfg: Config, final: pd.DataFrame) -> pd.DataFrame:
    """Replica (SIN tocar pipeline/silver.py) el algoritmo de
    normalizar_carroceria() -- match exacto primero, si no la primera clave de
    cfg.carroceria_map que sea substring o superstring del texto crudo, en
    orden de iteracion del dict -- pero registrando que CLAVE especifica gano
    para cada fila, informacion que hoy se descarta (solo queda el resultado
    normalizado).

    Caveat: usa el diccionario ACTUAL; algunas filas del parquet se procesaron
    cuando configuracion.xlsx tenia otro contenido (se edito varias veces en
    las ultimas 2 semanas) -- esto aproxima el uso de reglas bajo la
    configuracion de hoy, no reconstruye exactamente que regla decidio cada
    fila historicamente."""
    carroceria_map = cfg.carroceria_map
    valores_crudos = final["carroceria"].dropna().astype(str).str.upper().str.strip()
    valores_crudos = valores_crudos[valores_crudos != ""]

    registros = []
    for v in valores_crudos:
        if v in carroceria_map:
            registros.append({"clave": v, "tipo_match": "exacto", "valor_crudo": v})
            continue
        for k in carroceria_map:
            if k in v:
                registros.append({"clave": k, "tipo_match": "substring", "valor_crudo": v})
                break
            if v in k:
                registros.append({"clave": k, "tipo_match": "superstring", "valor_crudo": v})
                break

    df = pd.DataFrame(registros)

    todas_claves = pd.DataFrame({"clave": list(carroceria_map.keys())})
    if df.empty:
        resumen = todas_claves.copy()
        resumen["veces_usada"] = 0
        resumen["valores_crudos_distintos_matcheados"] = 0
        resumen["match_exacto"] = resumen["match_substring"] = resumen["match_superstring"] = 0
    else:
        base = df.groupby("clave").agg(
            veces_usada=("valor_crudo", "size"),
            valores_crudos_distintos_matcheados=("valor_crudo", "nunique"),
        ).reset_index()

        dist = df.groupby(["clave", "tipo_match"]).size().unstack(fill_value=0)
        for col in ["exacto", "substring", "superstring"]:
            if col not in dist.columns:
                dist[col] = 0
        dist = dist[["exacto", "substring", "superstring"]].reset_index()
        dist.columns = ["clave", "match_exacto", "match_substring", "match_superstring"]

        base = base.merge(dist, on="clave", how="left")
        resumen = todas_claves.merge(base, on="clave", how="left")
        cols_num = ["veces_usada", "valores_crudos_distintos_matcheados",
                    "match_exacto", "match_substring", "match_superstring"]
        resumen[cols_num] = resumen[cols_num].fillna(0).astype(int)

    resumen["longitud_clave"] = resumen["clave"].str.len()
    resumen["carroceria_final"] = resumen["clave"].map(carroceria_map)

    cols = ["clave", "carroceria_final", "longitud_clave", "veces_usada",
            "match_exacto", "match_substring", "match_superstring",
            "valores_crudos_distintos_matcheados"]
    return resumen[cols].sort_values("veces_usada", ascending=False).reset_index(drop=True)


def fase_zonas_informacion_insuficiente(final: pd.DataFrame, niveles: pd.DataFrame) -> pd.DataFrame:
    """Filas donde carroceria (CA: crudo, codigo explicito) es nulo/vacio pero
    carroceria_normalizada si tiene valor: ese valor vino del fallback
    posicional (_extraer_posicional/CARROCERIA_KW sobre la cabecera de la
    descripcion), un insumo estructuralmente mas indirecto que el codigo
    explicito. Cruza cantidad/% por categoria con el nivel de evidencia de
    detectar_conflictos_entre_senales -- hipotesis a VERIFICAR: estas filas
    concentrarian mas no_evaluable/baja_convergencia. final y niveles deben
    tener el mismo orden de filas (se alinean por posicion, no por dua_dam,
    porque dua_dam no está garantizado único por fila)."""
    df = final[["carroceria", "carroceria_normalizada"]].reset_index(drop=True).copy()
    df["categoria"] = df["carroceria_normalizada"].fillna("SIN_CATEGORIA")
    df["ca_crudo"] = np.where(
        df["carroceria"].isna() | (df["carroceria"].astype(str).str.strip() == ""),
        "vacio (fallback posicional)",
        "con codigo explicito",
    )
    df["nivel_evidencia"] = niveles["nivel_evidencia"].reset_index(drop=True)

    filas = []
    for (categoria, ca_crudo), g in df.groupby(["categoria", "ca_crudo"], observed=True):
        dist = g["nivel_evidencia"].value_counts(normalize=True).mul(100).round(1)
        filas.append({
            "categoria": categoria,
            "ca_crudo": ca_crudo,
            "filas": len(g),
            "pct_alta_convergencia": float(dist.get("alta_convergencia", 0.0)),
            "pct_convergencia_parcial": float(dist.get("convergencia_parcial", 0.0)),
            "pct_baja_convergencia": float(dist.get("baja_convergencia", 0.0)),
            "pct_no_evaluable": float(dist.get("no_evaluable", 0.0)),
        })

    return pd.DataFrame(filas).sort_values(["categoria", "ca_crudo"]).reset_index(drop=True)


def fase_sin_categoria_detalle(final: pd.DataFrame) -> pd.DataFrame:
    """Las filas con carroceria_normalizada nula -- volumen chico, no aplica
    'no revisar fila por fila'."""
    df = final[final["carroceria_normalizada"].isna()].copy()
    df["descripcion_fragmento"] = df["_descripcion"].astype(str).str.slice(0, 200)
    cols = [c for c in ["dua_dam", "marca_norm", "modelo_match", "carroceria", "descripcion_fragmento"]
            if c in df.columns]
    return df[cols].reset_index(drop=True)


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    print("Cargando configuracion.xlsx (vocabulario real del pipeline)...")
    cfg = Config(CONFIG_PATH)

    print("Cargando data/gold/camiones.parquet...")
    final = cargar_final()
    print(f"  {len(final):,} filas")

    final = enriquecer_cobertura_real(final, cfg)

    print("\n=== FASE 1: metrica vieja (gold) vs. presencia real en vocabulario ===")
    tabla1 = fase1_tabla_contaminacion(final)
    print(tabla1.to_string(index=False))

    print("\n=== FASE 4: cobertura por categoria (peor a mejor) ===")
    tabla4 = fase4_cobertura_por_categoria(final)
    print(tabla4.to_string(index=False))

    print("\n=== FASE 3: fuera de vocabulario por descripcion (top 20 por frecuencia) ===")
    tabla3 = fase3_fuera_de_vocabulario_por_descripcion(final)
    print(f"  Total descripciones distintas con algo fuera de vocabulario: {len(tabla3):,}")
    print(f"  Total filas afectadas: {tabla3['cantidad'].sum():,}")
    print(tabla3.head(20).to_string(index=False))

    print("\n=== FASE 3b: modelos fuera de vocabulario por marca ===")
    tabla3b = fase3b_modelos_fuera_vocab_por_marca(final)
    n_marcas_80 = int((tabla3b["pct_acumulado"] <= 80).sum()) + 1
    print(f"  Marcas con al menos 1 modelo fuera de vocab: {len(tabla3b):,}")
    print(f"  {n_marcas_80} marca(s) concentran el 80% de las filas con modelo fuera de vocab")
    print(tabla3b.head(25).to_string(index=False))

    print("\n=== FASE 1b: mismatches de clave marca <-> hoja modelos (todas las marcas) ===")
    tabla1b = detectar_mismatches_clave_marca_modelo(cfg, final)
    resumen_estado = tabla1b.groupby("estado").agg(
        marcas=("marca_normalizada", "count"), filas_afectadas=("filas_afectadas", "sum")
    )
    print(resumen_estado.to_string())
    print()
    print(tabla1b[tabla1b["estado"] != "ok_clave_exacta"].to_string(index=False))

    print("\n=== PATRONES POR MODELO: distribucion del parser (mas anomalas primero) ===")
    tabla_patrones = fase_patrones_por_modelo(final)
    print(f"  Modelos con mas de una categoria del parser: {len(tabla_patrones):,}")
    print(tabla_patrones.head(20).to_string(index=False))

    print("\n=== CONFLICTOS ENTRE FUENTES DE EVIDENCIA (partida/CA/descripcion/parser) ===")
    print("  Ninguna fuente es ground truth -- se reportan conflictos observables, no veredictos.")
    conflictos = detectar_conflictos_entre_senales(final)
    resumen_conflictos = fase_resumen_conflictos(conflictos)
    print(resumen_conflictos.to_string(index=False))
    print()
    pares_conflicto = fase_resumen_pares_en_conflicto(conflictos)
    print(pares_conflicto.to_string(index=False))

    print("\n=== CLAVES DUPLICADAS EN LA HOJA 'carrocerias' ===")
    duplicados_carrocerias = detectar_claves_duplicadas_carrocerias(CONFIG_PATH)
    print(duplicados_carrocerias.to_string(index=False))

    sin_categoria = fase_sin_categoria_detalle(final)
    print(f"\n=== FILAS SIN CATEGORIA ASIGNADA: {len(sin_categoria)} ===")

    print("\n=== CARACTERIZACION DE INCERTIDUMBRE (no busqueda de bugs) ===")
    niveles = fase_nivel_evidencia_por_fila(conflictos)
    print(niveles["nivel_evidencia"].value_counts().to_string())

    print("\n--- Evidencia por categoria ---")
    evidencia_categoria = fase_evidencia_por_categoria(niveles)
    print(evidencia_categoria.to_string(index=False))

    print("\n--- Uso y generalidad de reglas de 'carrocerias' (top 15 mas usadas) ---")
    uso_reglas = instrumentar_uso_reglas_carroceria(cfg, final)
    print(uso_reglas.head(15).to_string(index=False))
    print(f"  Reglas nunca usadas con los datos actuales: {(uso_reglas['veces_usada'] == 0).sum()}")

    print("\n--- Zonas de informacion indirecta/insuficiente (CA: vacio vs explicito) ---")
    zonas_info = fase_zonas_informacion_insuficiente(final, niveles)
    print(zonas_info.to_string(index=False))

    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as xw:
        tabla1.to_excel(xw, sheet_name="01_metrica_vieja_vs_real", index=False)
        tabla1b.to_excel(xw, sheet_name="01b_mismatch_clave_marca", index=False)
        tabla4.to_excel(xw, sheet_name="04_cobertura_por_categoria", index=False)
        tabla3.to_excel(xw, sheet_name="03_fuera_vocab_por_desc", index=False)
        tabla3b.to_excel(xw, sheet_name="03b_fuera_vocab_por_marca", index=False)
        tabla_patrones.to_excel(xw, sheet_name="05_patrones_por_modelo", index=False)
        conflictos.to_excel(xw, sheet_name="06_conflictos_por_fila", index=False)
        resumen_conflictos.to_excel(xw, sheet_name="07a_resumen_conflictos", index=False)
        pares_conflicto.to_excel(xw, sheet_name="07b_pares_en_conflicto", index=False)
        duplicados_carrocerias.to_excel(xw, sheet_name="08_duplicados_carrocerias", index=False)
        sin_categoria.to_excel(xw, sheet_name="09_sin_categoria_detalle", index=False)
        niveles.to_excel(xw, sheet_name="10_nivel_evidencia_por_fila", index=False)
        evidencia_categoria.to_excel(xw, sheet_name="11_evidencia_por_categoria", index=False)
        uso_reglas.to_excel(xw, sheet_name="13_uso_reglas_carroceria", index=False)
        zonas_info.to_excel(xw, sheet_name="14_zonas_informacion_insuficiente", index=False)

    print(f"\nExcel escrito: {OUT_XLSX.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
