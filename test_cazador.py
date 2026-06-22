#!/usr/bin/env python3
"""Extracción estructurada mejorada - con detección de carrocería basada en datos reales"""
from __future__ import annotations

import re
import argparse
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

INPUTS_DIR = "inputs"
OUTPUTS_DIR = "outputs"
HEADER_ROW = 6

# --- Columnas "duras" del export: cabecera original -> nombre de salida ---
HARD_COLS = {
    "Partida Aduanera": "partida",
    "Aduana": "aduana",
    "DUA / DAM": "dua_dam",
    "Fecha": "fecha",
    "Importador": "importador",
    "Embarcador / Exportador": "exportador",
    "Kg Bruto": "kg_bruto",
    "Kg Neto": "kg_neto",
    "U$ FOB Tot": "fob_usd",
    "U$ CFR Tot": "cfr_usd",
    "U$ CIF Tot": "cif_usd",
    "Pais de Origen": "pais_origen",
    "Pais de Compra": "pais_compra",
    "Puerto de Embarque": "puerto_embarque",
    "Via": "via",
    "Agente de Aduana": "agente_aduana",
    "Estado": "estado",
    "Ad Valorem": "ad_valorem",
    "IGV": "igv",
    "ISC": "isc",
    "IPM": "ipm",
    "Fecha Embarque": "fecha_embarque",
    "Descripcion Comercial": "_descripcion",
}

# --- Diccionario de códigos: CÓDIGO -> (columna, tipo) ---
CODES = {
    "MARCA": ("marca", "text"),
    "MODELO": ("modelo", "text"),
    "VERSION": ("version", "text"),
    "AÑO MOD": ("anio_modelo", "int"),
    "AÑO": ("anio_modelo", "int"),
    "VI": ("vin", "text"),
    "CH": ("chasis", "text"),
    "MO": ("motor_serie", "text"),
    "CO": ("combustible", "text"),
    "COMB": ("combustible", "text"),
    "C1": ("color", "text"),
    "NC": ("num_cilindros", "int"),
    "CC": ("cilindrada_cc", "num"),
    "PM": ("potencia", "power"),
    "EJ": ("ejes", "int"),
    "FR": ("traccion", "text"),
    "TT": ("transmision", "text"),
    "CA": ("carroceria", "text"),
    "AS": ("asientos", "int"),
    "PA": ("puertas", "int"),
    "PB": ("peso_bruto", "num"),
    "PN": ("peso_neto", "num"),
    "CU": ("carga_util", "num"),
    "LA": ("largo_mm", "num"),
    "AN": ("ancho_mm", "num"),
    "AL": ("alto_mm", "num"),
    "DE": ("dist_ejes", "num"),
    "KILOMETRAJE": ("kilometraje", "num"),
}

# Columnas extraídas, en orden de salida
EXTRACTED_ORDER = [
    "categoria", "marca", "modelo", "version", "anio_modelo",
    "vin", "chasis", "motor_serie", "combustible", "color",
    "num_cilindros", "cilindrada_cc", "potencia", "potencia_hp",
    "ejes", "traccion", "transmision", "carroceria", "asientos", "puertas",
    "peso_bruto", "peso_neto", "carga_util",
    "largo_mm", "ancho_mm", "alto_mm", "dist_ejes", "kilometraje",
    "desc_prefijo",
]

# Marcas conocidas de camiones
BRANDS = [
    "MERCEDES BENZ", "MERCEDES-BENZ", "MERCEDES", "FREIGHTLINER", "INTERNATIONAL",
    "VOLKSWAGEN", "DONGFENG", "SINOTRUK", "SHACMAN", "KENWORTH", "MITSUBISHI",
    "HYUNDAI", "ISUZU", "SCANIA", "VOLVO", "IVECO", "FOTON", "HOWO", "DAYUN",
    "CHANGAN", "MAXUS", "HINO", "FUSO", "FAW", "JAC", "JMC", "JBC", "MAN",
    "KIA", "DAF", "UD", "TATA", "DFAC", "DFSK", "CAMC", "BEIBEN", "JOYLONG",
]
BRAND_RE = re.compile(r"\b(" + "|".join(re.escape(b) for b in BRANDS) + r")\b", re.I)

# --- Patrones de carrocería MEJORADOS ---
CARROCERIA_PATTERNS = [
    # Tractocamiones y similares
    "TRACTOCAMION", "TRACTOCAMIÓN", "TRACTOR", "TRACTO", "CABEZAL",
    "REMOLCADOR", "TRACTOREMOLCADOR", "TRACTO CAMION", "TRACTOR CAMION",
    "TRACTOR-CAMION", "CHASIS CABINADO", "CHASIS CABINADO TRACTO",
    "TRACTO CHASIS CABINADO", "HEAD TRUCK", "TRUCK TRACTOR",
    "5TA RUEDA", "QUINTA RUEDA", "SEMIRREMOLQUE",
    
    # Carga general
    "FURGON", "FURGÓN", "FURGON CARGA", "FURGÓN CARGA",
    "BARANDA", "BARANDA", "BARANDA FIJA", "BARANDA ABATIBLE",
    "PLATAFORMA", "PLATAFORMA FIJA", "PLANCHA",
    "CAJA", "CAJON", "CAJÓN", "CAJA SECA", "CAJA REFRIGERADA",
    "ESTACA", "ESTACAS", "ESTACA FIJA", "ESTACAS ABATIBLES",
    
    # Especializados
    "CISTERNA", "TANQUE", "CISTERNA COMBUSTIBLE", "TANQUE AGUA",
    "VOLQUETE", "VOLQUETA", "TOLVA", "VOLQUETE DOBLE",
    "REFRIGERAD", "ISOTERM", "FRIGORIFIC", "REEFER",
    "GANADERA", "GANADERO", "PORTACONTENEDOR", "PORTACONTENEDORES",
    "GRUA", "GRÚA", "GRUA ARTICULADA", "GRÚA TELESCÓPICA",
    "HORMIGONERA", "MEZCLADOR", "MEZCLADORA", "COMPACTADOR",
    "BOMBERO", "AMBULANCIA",
    
    # Tipos de cabina y chasis
    "CHASIS CABINA", "CHASIS-CABINA", "CAMION CHASIS", "CHASIS LARGO",
    "CHASIS CORTO", "CABINA SIMPLE", "CABINA DOBLE", "DOBLE CABINA",
    "CABINA Y MEDIA", "CABINA DORMITORIO",
    
    # Materiales y características
    "MADERA", "METALICA", "METÁLICA", "ALUMINIO", "ACERO",
    "FIJA", "ABATIBLE", "CORREDIZA", "LONA", "PANEL", "PANELES",
    "LIVIANA", "REFORZADA", "TÉRMICA", "TERMICA",
    
    # Carga específica
    "CAMA BAJA", "CAMA ALTA", "LOWBOY", "LOW BOY", "NODRIZA",
    "PORTAMÁQUINAS", "PORTAMAQUINAS", "PORTACABALLOS",
]

# Compilar regex
CARROCERIA_RE = re.compile(
    r'\b(' + '|'.join(re.escape(c) for c in CARROCERIA_PATTERNS) + r')\b', 
    re.IGNORECASE
)

# Contexto explícito de carrocería (prioridad alta)
CARROCERIA_CONTEXT_RE = re.compile(
    r'(?:CARROCERIA|CARROCERÍA|TIPO|TIPO DE CARROCERIA|CARROCERIA DE)\s*:?\s*([^,;]{3,50})',
    re.IGNORECASE
)

# Mapeo de normalización
CARROCERIA_NORMALIZE = {
    "TRACTOCAMIÓN": "TRACTOCAMIÓN",
    "TRACTOR": "TRACTOCAMIÓN",
    "TRACTO": "TRACTOCAMIÓN",
    "TRACTO CAMION": "TRACTOCAMIÓN",
    "CABEZAL": "TRACTOCAMIÓN",
    "REMOLCADOR": "TRACTOCAMIÓN",
    "TRACTOREMOLCADOR": "TRACTOCAMIÓN",
    "CHASIS CABINADO TRACTO": "TRACTOCAMIÓN",
    "HEAD TRUCK": "TRACTOCAMIÓN",
    "TRUCK TRACTOR": "TRACTOCAMIÓN",
    
    "FURGON": "FURGÓN",
    "FURGON CARGA": "FURGÓN",
    "CAJON": "CAJÓN",
    "GRUA": "GRÚA",
    "METALICA": "METÁLICA",
    "TERMICA": "TÉRMICA",
}

# Tokenizador genérico
GENERIC_CODE_RE = re.compile(
    r"(?:^|[,;\s])((?:CH/VIN)|[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9.]{0,14})\s*:",
)
CATEGORY_RE = re.compile(r"^\s*(N\d)", re.IGNORECASE)
YEAR_RE = re.compile(r"A[ÑN]O(?:\s*MOD)?\s*:?\s*((?:19|20)\d{2})", re.IGNORECASE)
NUM_RE = re.compile(r"-?\d+(?:[.,]\d+)?")
FUEL_RE = re.compile(r"DIESEL|PETROLEO|GASOLINA|GAS\b|GNV|GLP|ELECTR|H[IÍ]BRID|DUAL|BIODIESEL", re.I)


def to_num(v) -> Optional[float]:
    """Convierte string a número flotante."""
    if pd.isna(v) or v is None:
        return None
    m = NUM_RE.search(str(v).replace(",", "."))
    if not m:
        return None
    try:
        return float(m.group(0))
    except ValueError:
        return None


def to_int(v) -> Optional[int]:
    """Convierte string a entero."""
    n = to_num(v)
    return int(n) if n is not None else None


def normalizar_carroceria(carr: str) -> str:
    """Normaliza nombres de carrocería a un formato estándar."""
    if not carr:
        return None
    
    carr_upper = carr.upper().strip()
    
    # Buscar en diccionario de normalización
    for key, value in CARROCERIA_NORMALIZE.items():
        if key in carr_upper:
            return value
    
    # Capitalizar primera letra de cada palabra
    return ' '.join(word.capitalize() for word in carr.split())


def extract_ca_value(text: str) -> Optional[str]:
    """Extrae específicamente el valor del código CA:"""
    if pd.isna(text):
        return None
    
    match = re.search(r'CA\s*:\s*([^,;]+)', str(text), re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def extract_carroceria(text: str) -> Optional[str]:
    """
    Extrae carrocería usando estrategias en cascada:
    1. Mención explícita con "CARROCERIA:" o "TIPO:"
    2. Patrones conocidos
    3. Inferencia por contexto
    """
    if pd.isna(text):
        return None
    
    text = str(text).strip()
    text_upper = text.upper()
    
    # Estrategia 1: Búsqueda explícita
    match = CARROCERIA_CONTEXT_RE.search(text)
    if match:
        valor = match.group(1).strip()
        valor = valor.split(',')[0].split(';')[0].strip()
        return normalizar_carroceria(valor)
    
    # Estrategia 2: Buscar en todo el texto
    matches = CARROCERIA_RE.findall(text)
    if matches:
        # Tomar la carrocería más específica (más larga primero)
        matches_sorted = sorted(matches, key=len, reverse=True)
        carr = matches_sorted[0].strip()
        
        # Buscar contexto cercano para detalles adicionales
        first_match = CARROCERIA_RE.search(text)
        if first_match:
            context_start = max(0, first_match.start() - 40)
            context_end = min(len(text), first_match.end() + 40)
            context = text[context_start:context_end].upper()
            
            # Añadir características si están cerca
            adiciones = []
            if "FIJA" in context:
                adiciones.append("FIJA")
            if "ABATIBLE" in context:
                adiciones.append("ABATIBLE")
            if "CORREDIZA" in context:
                adiciones.append("CORREDIZA")
            if "REFRIGERAD" in context or "TERMICA" in context:
                adiciones.append("REFRIGERADA")
            
            if adiciones:
                carr = f"{carr} {' '.join(adiciones)}"
        
        return normalizar_carroceria(carr)
    
    # Estrategia 3: Inferencia por palabras clave en contexto
    if "TRACTOR" in text_upper and ("CAMI" in text_upper or "SEMI" in text_upper):
        return "TRACTOCAMIÓN"
    if "5TA RUEDA" in text_upper or "QUINTA RUEDA" in text_upper:
        return "TRACTOCAMIÓN"
    if "CHASIS" in text_upper and "CABIN" in text_upper:
        return "CHASIS CABINA"
    if "FURGON" in text_upper or "FURGÓN" in text_upper:
        return "FURGÓN"
    if "CISTERNA" in text_upper or "TANQUE" in text_upper:
        return "CISTERNA"
    if "VOLQUETE" in text_upper or "VOLQUETA" in text_upper:
        return "VOLQUETE"
    if "BARANDA" in text_upper:
        return "BARANDA"
    
    return None


def parse_descripcion_vectorized(df: pd.DataFrame) -> pd.DataFrame:
    """
    Versión vectorizada MEJORADA con detección robusta de carrocería.
    """
    # Inicializar columnas
    for col in EXTRACTED_ORDER:
        if col not in df.columns:
            df[col] = None
    
    # Filtrar nulos
    mask = df['_descripcion'].notna()
    if not mask.any():
        return df
    
    descs = df.loc[mask, '_descripcion'].astype(str)
    
    # --- Extracciones básicas (rápidas) ---
    df.loc[mask, 'categoria'] = descs.str.extract(CATEGORY_RE, expand=False).str.upper()
    df.loc[mask, 'marca'] = descs.str.extract(BRAND_RE, expand=False).str.upper()
    df.loc[mask, 'anio_modelo'] = pd.to_numeric(
        descs.str.extract(YEAR_RE, expand=False), errors='coerce'
    ).astype('Int64')
    
    # --- Carrocería por CA: explícito (prioridad) ---
    ca_values = descs.apply(extract_ca_value)
    ca_normalized = ca_values.apply(
        lambda x: normalizar_carroceria(x) if pd.notna(x) else None
    )
    
    # --- Carrocería por heurístico (si no se encontró por CA:) ---
    carr_heuristic = descs.apply(extract_carroceria)
    
    # Combinar: CA: tiene prioridad
    df.loc[mask, 'carroceria'] = ca_normalized.fillna(carr_heuristic)
    
    # --- Parseo detallado de otros códigos ---
    def parse_row(desc):
        """Parse detallado para una fila individual."""
        if pd.isna(desc):
            return {}
        
        s = str(desc).strip()
        result = {}
        
        matches = list(GENERIC_CODE_RE.finditer(s))
        
        for i, m in enumerate(matches):
            code = m.group(1).upper()
            if code not in CODES and code != "CH/VIN":
                continue
            
            val_start = m.end()
            val_end = matches[i + 1].start(1) if i + 1 < len(matches) else len(s)
            raw = s[val_start:val_end].strip().strip(",;").strip()
            
            if not raw:
                continue
            
            if code == "CH/VIN":
                result.setdefault("chasis", raw)
                result.setdefault("vin", raw)
            elif code == "CO":
                if FUEL_RE.search(raw):
                    result.setdefault("combustible", raw)
                else:
                    result.setdefault("color", raw)
            elif code == "CA":
                # Ya procesado, guardamos referencia
                result["carroceria_crudo"] = raw
            else:
                col, typ = CODES[code]
                if col in result:  # No sobrescribir
                    continue
                if typ == "int":
                    result[col] = to_int(raw)
                elif typ == "num":
                    result[col] = to_num(raw)
                elif typ == "power":
                    result[col] = raw
                    hp = raw.split("@")[0]
                    result["potencia_hp"] = to_num(hp)
                else:
                    result[col] = raw
        
        return result
    
    # Aplicar parseo detallado
    parsed = descs.apply(parse_row)
    
    # Expandir resultados (sin sobrescribir carroceria)
    for col in EXTRACTED_ORDER:
        if col not in ['categoria', 'marca', 'anio_modelo', 'carroceria']:
            df.loc[mask, col] = parsed.apply(lambda x: x.get(col))
    
    # Reporte de tipos de carrocería encontrados
    carr_counts = df.loc[mask, 'carroceria'].value_counts()
    print(f"\n  Tipos de carrocería detectados: {len(carr_counts)}")
    for carr, count in carr_counts.head(10).items():
        print(f"    {carr:<30} {count:>5}")
    
    return df


def process_file(src: Path, out: Path) -> bool:
    """Parsea un export usando pandas y escribe resultados."""
    print(f"\n=== {src.name} ===")
    
    try:
        df = pd.read_excel(src, header=HEADER_ROW - 1)
    except Exception as e:
        print(f"Error leyendo {src}: {e}", file=sys.stderr)
        return False
    
    if df.empty:
        print(f"  Sin filas de datos en {src.name}.", file=sys.stderr)
        return False
    
    # Renombrar columnas duras
    rename_map = {k: v for k, v in HARD_COLS.items() if k in df.columns}
    df = df.rename(columns=rename_map)
    
    if '_descripcion' not in df.columns:
        print(f"  ERROR: No se encontró 'Descripcion Comercial' en {src.name}", file=sys.stderr)
        return False
    
    total = len(df)
    
    # Parsear descripciones
    print(f"  Parseando {total} registros...")
    df = parse_descripcion_vectorized(df)
    
    # --- Reporte de cobertura ---
    print(f"\nRegistros procesados: {total}\n")
    print(f"{'CAMPO EXTRAÍDO':<16}{'CON VALOR':>10}{'%':>7}")
    print("-" * 33)
    
    for col in EXTRACTED_ORDER:
        if col in df.columns:
            count = df[col].notna().sum()
            print(f"{col:<16}{count:>10}{100 * count / total:>6.0f}%")
    
    # Filas a revisar
    revisar = df[
        df['vin'].isna() & 
        df['chasis'].isna() & 
        df['marca'].isna()
    ]
    print(f"\nFilas a revisar (sin vin/chasis/marca): {len(revisar)}")
    
    # --- Preparar salida ---
    hard_out = [v for k, v in HARD_COLS.items() if v != "_descripcion"]
    columns = [c for c in hard_out + EXTRACTED_ORDER if c in df.columns]
    
    # Escribir con openpyxl
    out.parent.mkdir(parents=True, exist_ok=True)
    
    wb = Workbook()
    ws_main = wb.active
    ws_main.title = "estructurado"
    
    df_out = df[columns].copy()
    
    # Convertir tipos problemáticos
    for col in df_out.columns:
        if df_out[col].dtype == 'Int64':
            df_out[col] = df_out[col].astype(object)
    
    for r in dataframe_to_rows(df_out, index=False, header=True):
        ws_main.append(r)
    
    if not revisar.empty:
        ws_rev = wb.create_sheet("_revisar")
        rev_cols = ['dua_dam', 'estado', 'categoria', 'desc_prefijo', 'carroceria']
        rev_cols = [c for c in rev_cols if c in revisar.columns]
        
        df_rev = revisar[rev_cols].copy()
        for r in dataframe_to_rows(df_rev, index=False, header=True):
            ws_rev.append(r)
    
    wb.save(out)
    print(f"  Escrito: {out}  ({total} filas, {len(columns)} columnas)")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="Parser determinístico de la Descripción Comercial (pandas).")
    ap.add_argument("--inputs-dir", default=INPUTS_DIR, help="carpeta con exports crudos (default: inputs/)")
    ap.add_argument("--outputs-dir", default=OUTPUTS_DIR, help="carpeta de salida (default: outputs/)")
    ap.add_argument("--input", help="procesar un solo archivo (override de --inputs-dir)")
    args = ap.parse_args()

    if args.input:
        srcs = [Path(args.input)]
    else:
        srcs = sorted(Path(args.inputs_dir).glob("*.xlsx"))
    
    if not srcs:
        print(f"No se encontraron .xlsx en {args.inputs_dir}/", file=sys.stderr)
        return 1

    out_dir = Path(args.outputs_dir)
    ok = 0
    
    for src in srcs:
        if not src.exists():
            print(f"No existe: {src}", file=sys.stderr)
            continue
        out = out_dir / f"{src.stem}_estructurado.xlsx"
        if process_file(src, out):
            ok += 1
    
    print(f"\nListo: {ok}/{len(srcs)} archivos procesados.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())