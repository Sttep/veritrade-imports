"""
dashboard_camiones_v2.py — Dashboard Importaciones Camiones Perú
Uso: streamlit run dashboard_camiones_v2.py
"""
import warnings
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from calendar import monthrange
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shared.dashboard_helpers import (  # noqa: E402
    calc_var, descargar_csv, excel_bytes, fmt_tabla, pct, render_bloque,
    render_kpi_cards, safe_selectbox, tabla_dl, vc_reales,
)
from shared.riesgos import (  # noqa: E402
    hay_qa_silver, obtener_alertas_continuidad, obtener_conflictos_exclusion,
    obtener_embudo_importador, obtener_periodo_riesgos,
)

warnings.filterwarnings("ignore")

# ── CONFIG ────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Importaciones de Camiones - Dashboard",
                   page_icon="🚛", layout="wide",
                   initial_sidebar_state="expanded")

# ── CONSTANTES ────────────────────────────────────────────────────────────────
COLOR_SINOTRUK = '#F6E421'
COLOR_PALETTE  = ['#1E448A','#2E8B57','#4A90E2','#34495E','#50C878',
                  '#D98880','#A9CCE3','#F39C12','#9B59B6','#F6E421']
MESES_NOMBRES  = ['Ene','Feb','Mar','Abr','May','Jun',
                  'Jul','Ago','Sep','Oct','Nov','Dic']
CAT_REQUERIDAS = ["TRACTOCAMIÓN","CHASIS CABINA","VOLQUETE","HORMIGONERA",
                  "GRÚA","CISTERNA","FURGÓN","OTROS"]

# Segmentos por peso (PB en kg)
SEGMENTOS_PESO = [
    (3500,  "LDT 1"),
    (6000,  "LDT 1"),
    (10000, "LDT 2"),
    (15000, "MDT 1"),
    (17000, "MDT 2"),
    (25000, "MDT 3"),
    (33000, "SEMI PESADO"),
    (float("inf"), "PESADO"),
]
SEG_ORDEN = ["LDT 1","LDT 2","MDT 1","MDT 2","MDT 3","SEMI PESADO","PESADO","SIN DATO"]
SEG_COLORS = {
    "LDT 1":"#A9CCE3","LDT 2":"#4A90E2","MDT 1":"#2E8B57",
    "MDT 2":"#50C878","MDT 3":"#F39C12","SEMI PESADO":"#D98880",
    "PESADO":"#1E448A","SIN DATO":"#CCCCCC"
}
MARCA_PROPIA     = "SINOTRUK"
IMPORTADOR_PROPIO= "CORPORATION WITHMORY S.R.L."

PAIS_ISO = {
    "CHINA":"CHN","BRASIL":"BRA","JAPÓN":"JPN","COLOMBIA":"COL","SUECIA":"SWE",
    "COREA DEL SUR":"KOR","MÉXICO":"MEX","ESPAÑA":"ESP","ITALIA":"ITA",
    "ALEMANIA":"DEU","INDIA":"IND","PAÍSES BAJOS":"NLD","BÉLGICA":"BEL",
    "ESTADOS UNIDOS":"USA","POLONIA":"POL","REINO UNIDO":"GBR","JAPON":"JPN",
    "HOLANDA":"NLD","FINLANDIA":"FIN","AUSTRIA":"AUT","TURQUÍA":"TUR",
}
COORDS = {
    "CHN":(35.86,104.19),"BRA":(-14.23,-51.92),"JPN":(36.20,138.25),
    "COL":(4.57,-74.29),"SWE":(60.12,18.64),"KOR":(35.90,127.76),
    "MEX":(23.63,-102.55),"ESP":(40.46,-3.74),"ITA":(41.87,12.56),
    "DEU":(51.16,10.45),"IND":(20.59,78.96),"NLD":(52.13,5.29),
    "BEL":(50.50,4.46),"USA":(37.09,-95.71),"POL":(51.91,19.14),
    "GBR":(55.37,-3.43),"FIN":(61.92,25.74),"AUT":(47.51,14.55),
    "TUR":(38.96,35.24),
}

# Macro-región de manufactura, para la pestaña "Volquetes por Origen" del
# reporte de gerencia (guia estructura antes ppt.txt, pestaña 7) -- agrupa
# los países de PAIS_ISO en los 5 bloques que pide la guía.
PAIS_A_REGION = {
    "CHINA":"China","BRASIL":"Brasil","JAPÓN":"Japón/Corea","JAPON":"Japón/Corea",
    "COREA DEL SUR":"Japón/Corea",
    "SUECIA":"Europa","ESPAÑA":"Europa","ITALIA":"Europa","ALEMANIA":"Europa",
    "PAÍSES BAJOS":"Europa","HOLANDA":"Europa","BÉLGICA":"Europa","POLONIA":"Europa",
    "REINO UNIDO":"Europa","FINLANDIA":"Europa","AUSTRIA":"Europa","TURQUÍA":"Europa",
    "COLOMBIA":"Otros","MÉXICO":"Otros","INDIA":"Otros","ESTADOS UNIDOS":"Otros",
}

MAPEO_COLS = {
    'marca_norm':          ['marca_norm','marca_normalizada','marca_declarada'],
    'modelo':              ['modelo_match','modelo','modelo_norm'],
    'categoria_carroceria':['categoria_maquinaria','carroceria_normalizada','carroceria'],
    'grupo_importador':    ['grupo_importador','importador_grupo','importador'],
    'valor_fob':           ['valor_fob','fob','fob_usd'],
    'valor_cif':           ['valor_cif','cif','cif_usd'],
    'pb':                  ['peso_bruto_desc'],  # kg_bruto_col/kg_bruto es peso NETO, no bruto -- no usar como fallback
}

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""<style>
.block-container{padding:0.5rem 1.5rem!important;max-width:100%!important;}
.main{background-color:#F5F5F5;}
div[data-testid="stMultiSelect"]>div{min-height:48px!important;
  background-color:#FFFFFF!important;border-radius:8px!important;}
div[data-testid="stHorizontalBlock"]:has(.kpi-row-marker){
  background-color:#262626;padding:20px 25px;border-radius:12px;
  box-shadow:0 4px 15px rgba(0,0,0,0.3);margin-bottom:20px;align-items:center;}
div[data-testid="stHorizontalBlock"]:has(.kpi-row-marker) label,
div[data-testid="stHorizontalBlock"]:has(.kpi-row-marker) .stMarkdown p{
  color:#AAAAAA!important;font-size:0.75rem;}
.kpi-container-transparent{display:flex;justify-content:space-between;
  align-items:center;text-align:center;width:100%;}
.kpi-box{flex:1;border-right:1px solid rgba(255,255,255,0.15);padding:10px 20px;}
.kpi-box:last-child{border-right:none;}
.kpi-title{font-size:0.85rem;color:#CCCCCC;font-weight:700;
  text-transform:uppercase;letter-spacing:0.5px;}
.kpi-subtitle{font-size:0.75rem;color:#999999;display:block;margin-top:2px;}
.kpi-value{font-size:1.9rem;color:#FFFFFF;font-weight:800;margin-top:8px;}
.kpi-var-up{color:#4CAF50;font-weight:800;font-size:1.9rem;margin-top:8px;}
.kpi-var-down{color:#FF5252;font-weight:800;font-size:1.9rem;margin-top:8px;}
.section-header{display:flex;justify-content:space-between;align-items:center;
  background:#FFFFFF;color:#1A1A1A;border-left:4px solid #F6E421;
  padding:10px 15px;border-radius:8px;margin-bottom:15px;
  box-shadow:0 2px 8px rgba(0,0,0,0.08);border-top:1px solid #E8E8E8;
  border-right:1px solid #E8E8E8;border-bottom:1px solid #E8E8E8;}
.section-title-text{font-size:0.9rem;font-weight:600;margin:0;letter-spacing:0.3px;}
.section-divider{border:0;height:2px;
  background:linear-gradient(90deg,#333 0%,#555 50%,#333 100%);
  margin:25px 0;border-radius:2px;}
.insight-card{background:white;border-left:4px solid #F6E421;padding:15px;
  border-radius:6px;margin-bottom:10px;box-shadow:0 2px 8px rgba(0,0,0,0.08);}
.insight-positive{border-left-color:#4CAF50;}
.insight-warning{border-left-color:#FFA500;}
.insight-danger{border-left-color:#FF5252;}
.insight-info{border-left-color:#F6E421;}
.insight-title{font-size:0.85rem;font-weight:700;color:#1A1A1A;margin-bottom:5px;}
.insight-text{font-size:0.8rem;color:#555;line-height:1.5;}
</style>""", unsafe_allow_html=True)

# ── HELPERS ───────────────────────────────────────────────────────────────────
def normalizar_columnas(df, mapeo):
    df = df.copy()
    for std, posibles in mapeo.items():
        for nombre in posibles:
            if nombre in df.columns:
                if nombre != std:
                    df = df.rename(columns={nombre: std})
                break
    return df

def normalizar_carroceria(val):
    v = str(val).upper().strip().rstrip(",")
    if not v or v in ("NAN","NONE",""):
        return "OTROS"
    if any(k in v for k in ["TRACTO","REMOLCADOR","CABEZAL","TRACTOREMOLCADOR"]):
        return "TRACTOCAMIÓN"
    if any(k in v for k in ["VOLQUETE","VOLQUETA","DUMPER","TOLVA"]):
        return "VOLQUETE"
    if any(k in v for k in ["CHASIS CAB","CHASIS MOT","CHASIS MOTORIZ"]):
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
    # COMPACTADOR, BARREDERA, MINIBUS, EXPLOSIVOS, PICK UP → OTROS
    return "OTROS"

def clasificar_segmento(pb, carroceria: str | None = None) -> str:
    """Clasifica por Peso Bruto Vehicular (kg) según rangos Withmory.

    Si carroceria ya es TRACTOCAMIÓN, se fuerza PESADO sin importar el peso
    declarado -- decisión de negocio (2026-07-09): 93% de los tractocamiones de
    Zapler (1,017 filas) declaran exactamente 33,000kg de fábrica y caían mal
    clasificados en SEMI PESADO por el corte de peso puro."""
    if carroceria == "TRACTOCAMIÓN":
        return "PESADO"
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

def normalizar_combustible(val):
    v = str(val).upper()
    if "GNL" in v:
        return "GNL"
    if "GNV" in v or "GAS NAT" in v:
        return "GNV"
    if "ELECT" in v:
        return "ELÉCTRICO"
    if "GASOL" in v:
        return "GASOLINA"
    if "DIESEL" in v or "PETROL" in v:
        return "DIESEL"
    if "HIBRID" in v:
        return "HÍBRIDO"
    return "OTRO"

_TRACCION_MAP = {
    # espacios → sin espacios
    "4 X 2":"4X2","4 X 4":"4X4","6 X 2":"6X2","6 X 4":"6X4",
    "8 X 2":"8X2","8 X 4":"8X4","6 X 6":"6X6","10 X 4":"10X4",
    # tag axle / eje levantable (notación con asterisco)
    "6X2*4":"6X2","6X2 *4":"6X2","6X2* 4":"6X2","6X2*":"6X2",
    "8X4*4":"8X4","8X4 *4":"8X4","8X4*":"8X4",
    "4X2*4":"4X2","4X2*":"4X2",
    # sufijos de tracto (TT, T/T, coma)
    "6X4,TT":"6X4","6X4 TT":"6X4","6X4TT":"6X4",
    "4X2,TT":"4X2","4X2 TT":"4X2","4X2TT":"4X2",
    "6X2,TT":"6X2","6X2 TT":"6X2",
    # nulos
    "NAN":"N/D","NONE":"N/D","N/A":"N/D","":"N/D","-":"N/D","0":"N/D",
}

def normalizar_traccion(val):
    v = str(val).upper().strip()
    if v in _TRACCION_MAP:
        return _TRACCION_MAP[v]
    m = re.match(r'^(\d+X\d+)', v)
    if m:
        return m.group(1)
    return v if v else "N/D"

def destacar_sinotruk(row):
    for col in [COL_MARCA,'Marca','Actor Comercial']:
        if col in row.index and row[col] == MARCA_PROPIA:
            return ['background-color:#FFF8E1;font-weight:bold;']*len(row)
    return ['']*len(row)

def insights_ejecutivos(df_act, df_ant, total_act, total_ant):
    ins = []
    if total_ant > 0:
        var = (total_act-total_ant)/total_ant*100
        ins.append({'tipo':'positive' if var>10 else 'danger' if var<-10 else 'info',
                    'titulo':f'{"📈 Mercado en Expansión" if var>10 else "📉 Contracción" if var<-10 else "📊 Mercado Estable"}',
                    'texto':f'Variación {var:+.1f}% vs año anterior. Total: {total_act:,} uds.'})
    if COL_MARCA in df_act.columns:
        top = df_act[COL_MARCA].value_counts().head(1)
        if not top.empty:
            ins.append({'tipo':'info','titulo':f'👑 Marca Líder: {top.index[0]}',
                        'texto':f'{top.values[0]:,} uds · {top.values[0]/total_act*100:.1f}% share'})
    if COL_MARCA in df_act.columns:
        # Familia completa Sinotruk -- marca_norm ya viene consolidada del pipeline
        mask_sin_act = df_act[COL_MARCA].astype(str).str.upper().str.strip() == "SINOTRUK"
        mask_sin_ant = (df_ant[COL_MARCA].astype(str).str.upper().str.strip() == "SINOTRUK") \
            if COL_MARCA in df_ant.columns else pd.Series(False)
        n_sin = mask_sin_act.sum()
        n_ant = mask_sin_ant.sum() if len(mask_sin_ant) > 0 else 0
        if n_sin > 0:
            var_s = (n_sin-n_ant)/n_ant*100 if n_ant>0 else 0
            ins.append({'tipo':'positive' if var_s>=0 else 'warning',
                        'titulo':f'🟡 Familia Sinotruk: {var_s:+.1f}%',
                        'texto':f'{n_sin:,} uds · {n_sin/total_act*100:.1f}% market share'})
    if COL_FOB in df_act.columns and df_act[COL_FOB].sum()>0:
        fob = df_act[COL_FOB].mean()
        fob_a = df_ant[COL_FOB].mean() if COL_FOB in df_ant.columns and df_ant[COL_FOB].sum()>0 else 0
        if fob_a>0:
            vf = (fob-fob_a)/fob_a*100
            ins.append({'tipo':'warning' if vf>0 else 'positive',
                        'titulo':f'💰 FOB Prom: US$ {fob:,.0f}',
                        'texto':f'Variación {vf:+.1f}% vs año anterior (US$ {fob_a:,.0f})'})
    return ins[:4]


def insights_por_marca(df_act, df_ant, top_n=5, min_uds=20):
    """Hallazgos automáticos: delta de pp de share por marca (con umbral mínimo
    de unidades para no generar ruido de marcas con 1-2 uds -- ver liz-z26.5),
    más crecimiento por segmento y concentración de origen si son notorios.
    Bloque ADICIONAL a insights_ejecutivos(), no lo reemplaza."""
    total_a, total_b = len(df_act), len(df_ant)
    bullets = []

    if total_a and total_b and COL_MARCA in df_act.columns:
        rank_act = df_act[COL_MARCA].value_counts()
        rank_ant = df_ant[COL_MARCA].value_counts() if COL_MARCA in df_ant.columns else pd.Series(dtype=int)
        deltas = []
        for m in rank_act[rank_act >= min_uds].index:
            ms_a = pct(int(rank_act.get(m, 0)), total_a)
            ms_b = pct(int(rank_ant.get(m, 0)), total_b) if total_b else 0.0
            deltas.append((str(m), round(ms_a - ms_b, 1), ms_a, ms_b))
        deltas.sort(key=lambda d: abs(d[1]), reverse=True)
        for m, d, ms_a, ms_b in deltas[:top_n]:
            if d > 0:
                icono, verbo = "📈", "ganó"
            elif d < 0:
                icono, verbo = "📉", "cayó"
            else:
                icono, verbo = "➖", "se mantuvo en"
            bullets.append(f"{icono} **{m}** {verbo} {abs(d):.1f} pp de share "
                           f"({ms_b:.1f}% → {ms_a:.1f}%)")

    if 'categoria_carroceria' in df_act.columns:
        seg_act = df_act['categoria_carroceria'].apply(_bucket_segmento_guia).value_counts()
        seg_ant = (df_ant['categoria_carroceria'].apply(_bucket_segmento_guia).value_counts()
                   if 'categoria_carroceria' in df_ant.columns else pd.Series(dtype=int))
        for seg in ['Camiones', 'Tractos', 'Volquetes']:
            a, b = int(seg_act.get(seg, 0)), int(seg_ant.get(seg, 0))
            if b >= min_uds:
                var = (a - b) / b * 100
                if abs(var) >= 15:
                    icono = "🚛" if var > 0 else "🔻"
                    verbo = "crecieron" if var > 0 else "cayeron"
                    bullets.append(f"{icono} Los {seg.lower()} {verbo} {abs(var):.0f}% interanual")

    if 'pais_origen' in df_act.columns and total_a:
        origen = df_act['pais_origen'].astype(str).str.upper().str.strip().value_counts()
        if not origen.empty:
            top_pais, n_pais = str(origen.index[0]), int(origen.iloc[0])
            share_pais = pct(n_pais, total_a)
            if share_pais >= 40:
                bullets.append(f"🌏 {top_pais.title()} ya representa {share_pais:.0f}% del origen "
                               f"de las unidades")

    return bullets


# ── CARGA ─────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def cargar():
    ruta_parquet = Path(__file__).parent.parent / 'data' / 'gold' / 'camiones.parquet'
    if ruta_parquet.exists():
        df = pd.read_parquet(ruta_parquet)
        ultima = ruta_parquet.stat().st_mtime
    else:
        ruta = Path(__file__).parent.parent / 'data' / 'silver'
        if not ruta.exists():
            ruta = Path('.')
        archivos = sorted(ruta.glob('*_fase1.parquet'))
        if not archivos:
            return pd.DataFrame(), None

        frames, ultima = [], 0
        for f in archivos:
            try:
                d = pd.read_parquet(f)
                frames.append(d)
                ultima = max(ultima, f.stat().st_mtime)
            except Exception:
                pass
        if not frames:
            return pd.DataFrame(), None
        df = pd.concat(frames, ignore_index=True)
    if 'dua_dam' in df.columns:
        dua = df['dua_dam'].fillna('').astype(str)
        if 'vin' in df.columns:
            vin_part = df['vin']
            if 'chasis' in df.columns:
                vin_part = vin_part.where(vin_part.notna() & (vin_part.astype(str) != ''), df['chasis'])
        elif 'chasis' in df.columns:
            vin_part = df['chasis']
        else:
            vin_part = pd.Series('', index=df.index)
        df['_k'] = dua + '|' + vin_part.fillna('').astype(str)
        df = df.drop_duplicates('_k').drop(columns='_k')

    if 'fecha_dua' in df.columns:
        df['fecha'] = pd.to_datetime(df['fecha_dua'], errors='coerce')
        df['año']   = df['fecha'].dt.year.astype('Int64')
        df['mes']   = df['fecha'].dt.month.astype('Int64')
        df['mes_nombre'] = df['mes'].map({i+1:m for i,m in enumerate(MESES_NOMBRES)})

    df = normalizar_columnas(df, MAPEO_COLS)
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()]

    for col in ['categoria_carroceria','marca_norm','grupo_importador']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.upper().str.strip()
            df[col] = df[col].replace(['NAN','NONE','NULL','',' '], pd.NA)

    if 'categoria_carroceria' in df.columns:
        df['categoria_carroceria'] = df['categoria_carroceria'].apply(normalizar_carroceria)
    if 'combustible' in df.columns:
        df['combustible_norm'] = df['combustible'].apply(normalizar_combustible)
    if 'traccion' in df.columns:
        df['traccion'] = df['traccion'].astype(str).str.upper().str.strip().apply(normalizar_traccion)

    # ── Peso bruto y segmento ─────────────────────────────────────────────────
    if 'pb' in df.columns:
        df['pb'] = pd.to_numeric(df['pb'], errors='coerce')
    else:
        df['pb'] = pd.NA
    cat_para_segmento = (df['categoria_carroceria'] if 'categoria_carroceria' in df.columns
                          else pd.Series([None] * len(df), index=df.index))
    df['segmento_peso'] = [clasificar_segmento(pb, cat)
                            for pb, cat in zip(df['pb'], cat_para_segmento)]

    for c in ['valor_fob','valor_cif','fob_usd','cif_usd']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

    # ── Año como int nativo (evita bugs de tipo en comparaciones) ────────────
    if 'año' in df.columns:
        df['año'] = df['año'].apply(lambda x: int(x) if pd.notna(x) else pd.NA).astype('Int64')

    for col in ['categoria_carroceria','marca_norm','grupo_importador']:
        if col in df.columns:
            df[col] = df[col].astype('category')

    return df, ultima

df, ULTIMA_ACT = cargar()
if df is None or df.empty:
    st.error("No se encontraron archivos *_fase1.parquet en data/silver/")
    st.stop()

COL_MARCA = 'marca_norm' if 'marca_norm' in df.columns else 'marca'
COL_MODELO= 'modelo'
COL_FOB   = 'valor_fob' if 'valor_fob' in df.columns else None
COL_CIF   = 'valor_cif' if 'valor_cif' in df.columns else None

# ── HEADER ────────────────────────────────────────────────────────────────────
# FIX CRÍTICO: años como int nativo (evita numpy.float64 en monthrange)
años_disp = sorted([int(a) for a in df['año'].dropna().unique()])
cats_disp = sorted([c for c in df['categoria_carroceria'].dropna().unique()
                    if c in CAT_REQUERIDAS])

st.markdown('<div style="padding-top:8px"></div>', unsafe_allow_html=True)
col_titulo, col_desde, col_hasta, col_btn = st.columns([2.8, 0.9, 0.9, 0.4])

with col_desde:
    st.markdown('<div style="font-size:0.6rem;color:#888;font-weight:700;margin-bottom:2px;">📅 Desde</div>',
                unsafe_allow_html=True)
    c1, c2 = st.columns([1,1.1], gap="small")
    with c1:
        mes_ini = safe_selectbox("Mi", MESES_NOMBRES, index=0, label_visibility="collapsed", key="mes_ini")
    with c2:
        año_ini = safe_selectbox("Ai", años_disp, index=0, label_visibility="collapsed", key="año_ini")

with col_hasta:
    st.markdown('<div style="font-size:0.6rem;color:#888;font-weight:700;margin-bottom:2px;">📅 Hasta</div>',
                unsafe_allow_html=True)
    c3, c4 = st.columns([1,1.1], gap="small")
    with c3:
        mes_fin = safe_selectbox("Mf", MESES_NOMBRES, index=len(MESES_NOMBRES)-1, label_visibility="collapsed", key="mes_fin")
    with c4:
        año_fin = safe_selectbox("Af", años_disp, index=len(años_disp)-1, label_visibility="collapsed", key="año_fin")

with col_titulo:
    col_txt, col_toggle = st.columns([2,1])
    with col_txt:
        st.markdown(f"""
        <h1 style="font-size:1.6rem;font-weight:800;color:#1A1A1A;margin:0;">
          🚛 Importaciones de Camiones · Perú
        </h1>
        <div style="font-size:0.7rem;color:#666;">
          Fuente: <strong>Veritrade</strong> | {mes_ini} {año_ini} – {mes_fin} {año_fin}
          | vs {mes_ini} {año_ini-1} – {mes_fin} {año_fin-1}
        </div>""", unsafe_allow_html=True)
    with col_toggle:
        st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
        vista = st.radio("Vista", ["🌐 Global","🟡 Sinotruk"],
                         horizontal=True, label_visibility="collapsed", key="vista")

with col_btn:
    st.markdown('<div style="height:32px"></div>', unsafe_allow_html=True)
    if st.button("🔄", use_container_width=True, help="Actualizar datos"):
        st.cache_data.clear()
        st.toast("✅ Datos actualizados", icon="🔄")
        st.rerun()
    _f_act = datetime.fromtimestamp(ULTIMA_ACT).strftime('%d/%m %H:%M') if ULTIMA_ACT else "—"
    st.caption(f"↻ {_f_act}")

# ── FECHAS — FIX: int() explícito para monthrange ─────────────────────────────
mes_ini_n   = MESES_NOMBRES.index(mes_ini) + 1
mes_fin_n   = MESES_NOMBRES.index(mes_fin) + 1
año_ini_int = int(año_ini)
año_fin_int = int(año_fin)

_, ld   = monthrange(año_fin_int, mes_fin_n)
_, ld_a = monthrange(año_fin_int-1, mes_fin_n)

f_ini   = pd.Timestamp(año_ini_int,   mes_ini_n, 1)
f_fin   = pd.Timestamp(año_fin_int,   mes_fin_n, ld,   23, 59, 59)
f_ini_a = pd.Timestamp(año_ini_int-1, mes_ini_n, 1)
f_fin_a = pd.Timestamp(año_fin_int-1, mes_fin_n, ld_a, 23, 59, 59)

if f_ini > f_fin:
    st.warning("⚠️ La fecha 'Desde' es posterior a 'Hasta' — invertí el rango para ver datos.")
    st.stop()

df_actual   = df[(df['fecha']>=f_ini)   & (df['fecha']<=f_fin)]
df_anterior = df[(df['fecha']>=f_ini_a) & (df['fecha']<=f_fin_a)]

# Snapshot del mercado total (todas las marcas, mismo rango de fechas) antes
# del filtro Sinotruk -- se usa como referencia real de mercado para las
# tarjetas comparativas (Competencia, share Sinotruk) cuando la vista está en
# Modo Sinotruk, donde df_actual/df_anterior quedan reducidos a una sola marca.
df_mercado_actual, df_mercado_anterior = df_actual, df_anterior

# Filtro Sinotruk si aplica
es_sinotruk = "Sinotruk" in vista
def mask_sin(d):
    m = d[COL_MARCA].astype(str).str.upper().str.strip() == "SINOTRUK"
    return d[m]
if es_sinotruk:
    df_actual   = mask_sin(df_actual)
    df_anterior = mask_sin(df_anterior)

# ── FILA KPIs ─────────────────────────────────────────────────────────────────
col_seg, col_kpis = st.columns([1.8, 3.2])

with col_seg:
    st.markdown('<div class="kpi-row-marker"></div>', unsafe_allow_html=True)
    if es_sinotruk:
        st.markdown("""
        <div style="background:#1A1A1A;border-radius:8px;padding:12px;
                    border-left:4px solid #F6E421;margin-top:4px;">
          <div style="color:#F6E421;font-weight:800;">🟡 Modo Sinotruk</div>
          <div style="color:#aaa;font-size:0.75rem;margin-top:4px;">
            SINOTRUK · HOWO · SITRAK · HOWO MAX · HONAN · WANGPAI
          </div>
        </div>""", unsafe_allow_html=True)
        cat_sel = []
    else:
        st.caption("TIPOS DE CARROCERÍA")
        cat_sel = st.multiselect("Carr.", cats_disp, default=cats_disp,
                                 label_visibility="collapsed", key="cat_sel")
        if cat_sel:
            df_actual   = df_actual[df_actual['categoria_carroceria'].isin(cat_sel)]
            df_anterior = df_anterior[df_anterior['categoria_carroceria'].isin(cat_sel)]

    col_topn, col_graf = st.columns(2)
    with col_topn:
        TOP_N = safe_selectbox("Top", [10, 15, 20, 30, 50], index=1, key="top_n_global",
                             help="Cuántas filas muestran las tablas de ranking (Mercado, Marca y "
                                  "Segmento, Camiones, Tractos, Volquetes). No afecta Segmentos, "
                                  "Volquetes por Origen ni Combustible, que tienen categorías fijas.")
    with col_graf:
        st.markdown('<div style="height:28px"></div>', unsafe_allow_html=True)
        MOSTRAR_GRAFICO = st.checkbox("📊 Gráficos", value=True, key="mostrar_grafico",
                                      help="Las tablas siempre se muestran; esto solo agrega o quita "
                                           "los gráficos del reporte.")

total_act = len(df_actual)
total_ant = len(df_anterior)
var_pct   = (total_act-total_ant)/total_ant*100 if total_ant>0 else None

# FIX: la proyección extrapola el RITMO DE año_fin_int, no el promedio de
# todo el rango de fechas seleccionado (que puede abarcar varios años) --
# antes, con el filtro default de 4 años, "Proyección 2026" en realidad
# devolvía el promedio anual 2023-2026 disfrazado de proyección del año.
f_ini_proy = max(f_ini, pd.Timestamp(año_fin_int, 1, 1))
df_proy    = df_actual[(df_actual['fecha']>=f_ini_proy) & (df_actual['fecha']<=f_fin)]
dias_proy  = max((f_fin-f_ini_proy).days+1, 1)
dias_año   = 366 if año_fin_int%4==0 else 365
proyeccion = int(len(df_proy)*dias_año/dias_proy) if not df_proy.empty else 0
df_ant_año = df[df['año']==año_fin_int-1]
if es_sinotruk:
    df_ant_año = mask_sin(df_ant_año)
elif cat_sel:
    df_ant_año = df_ant_año[df_ant_año['categoria_carroceria'].isin(cat_sel)]
cierre_ant = len(df_ant_año)
var_proy   = (proyeccion-cierre_ant)/cierre_ant*100 if cierre_ant>0 else 0

var_str   = f"{'▲' if var_pct and var_pct>=0 else '▼'} {abs(var_pct or 0):.1f}%"
var_class = "kpi-var-up" if (var_pct is not None and var_pct>=0) else "kpi-var-down"

with col_kpis:
    st.markdown(f"""
    <div class="kpi-container-transparent">
      <div class="kpi-box">
        <div class="kpi-title">Período Anterior</div>
        <div class="kpi-value">{total_ant:,}</div>
        <span class="kpi-subtitle">unidades</span>
      </div>
      <div class="kpi-box">
        <div class="kpi-title">Período Actual</div>
        <div class="kpi-value">{total_act:,}</div>
        <span class="kpi-subtitle">unidades</span>
      </div>
      <div class="kpi-box">
        <div class="kpi-title">📊 Variación</div>
        <div class="{var_class}">{var_str}</div>
        <span class="kpi-subtitle">interanual</span>
      </div>
      <div class="kpi-box">
        <div class="kpi-title">🎯 Proyección {año_fin_int}</div>
        <div class="kpi-value">{proyeccion:,.0f}</div>
        <span class="kpi-subtitle" style="color:{'#4CAF50' if var_proy>=0 else '#FF5252'}">
          {var_proy:+.1f}% vs cierre ant.
        </span>
      </div>
    </div>""", unsafe_allow_html=True)
    st.caption("🎯 La proyección es una extrapolación lineal del ritmo actual — no es un pedido "
               "confirmado ni un dato oficial de cierre.")

# ── INSIGHTS (parte de la portada "🧭 Resumen Ejecutivo", ver render_resumen_ejecutivo) ────
ins = insights_ejecutivos(df_actual, df_anterior, total_act, total_ant)

if df_actual.empty:
    st.warning("⚠️ Sin datos para el período seleccionado.")
    st.stop()

año_actual = año_fin_int

# ══════════════════════════════════════════════════════════════════════════════
# MARKET SHARE detalle histórico (tendencia mensual + segmento/peso + tracción).
# Se llama entera dentro del expander "📈 Tendencias" al final del archivo.
# ══════════════════════════════════════════════════════════════════════════════
def render_market_share_detalle():
    tend = df_actual.groupby(['año','mes','mes_nombre']).size().reset_index(name='Unidades')
    tend['Año'] = tend['año'].astype(str)
    meses_ord = [m for m in MESES_NOMBRES if m in tend['mes_nombre'].unique()]
    fig_t = px.line(tend, x='mes_nombre', y='Unidades', color='Año', markers=True,
                    labels={'mes_nombre': 'Mes'},
                    color_discrete_sequence=COLOR_PALETTE, title="Tendencia Mensual Histórica")
    fig_t.update_layout(plot_bgcolor='white', height=420,
                        xaxis={'categoryorder':'array','categoryarray':meses_ord})

    # Tabla pivot: Año × Mes  +  Total  +  Var% vs año anterior
    tend_pivot = tend.pivot_table(
        index='Año', columns='mes_nombre', values='Unidades', aggfunc='sum', fill_value=0
    )
    tend_pivot = tend_pivot.reindex(columns=[m for m in MESES_NOMBRES if m in tend_pivot.columns], fill_value=0)
    tend_pivot['Total'] = tend_pivot.sum(axis=1)
    años_piv = list(tend_pivot.index)
    var_vals = []
    for i, año in enumerate(años_piv):
        if i == 0:
            var_vals.append('—')
        else:
            ant = tend_pivot.loc[años_piv[i-1], 'Total']
            act = tend_pivot.loc[año, 'Total']
            var_vals.append(f"{(act-ant)/ant*100:+.1f}%" if ant > 0 else '—')
    tend_pivot['Var% vs ant'] = var_vals
    tend_pivot = tend_pivot.reset_index()

    render_bloque("", fig_t, tend_pivot, "tend", "tendencia_mensual")
    st.divider()

    # ── Toggle carrocería / segmento peso ─────────────────────────────────────
    vista_seg = st.radio("Desglose por:", ["🚛 Carrocería", "⚖️ Segmento (Peso)"],
                         horizontal=True, key="vista_seg")

    if "Segmento" in vista_seg:
        st.markdown("##### ⚖️ Market Share por Segmento de Peso")
        st.caption("LDT 1: ≤6t · LDT 2: 6-10t · MDT 1: 10-15t · MDT 2: 15-17t · MDT 3: 17-25t · SEMI PESADO: 25-33t · PESADO: >33t")

        seg_act = df_actual['segmento_peso'].value_counts().reset_index()
        seg_act.columns = ['Segmento','Unidades']
        seg_act = seg_act[seg_act['Segmento'] != 'SIN DATO']
        seg_act['Segmento'] = pd.Categorical(seg_act['Segmento'], categories=SEG_ORDEN, ordered=True)
        seg_act = seg_act.sort_values('Segmento')
        seg_act['% Share'] = (seg_act['Unidades']/seg_act['Unidades'].sum()*100).round(1)
        seg_act['Color'] = seg_act['Segmento'].map(SEG_COLORS)

        fig_seg = px.bar(seg_act, x='Segmento', y='Unidades', text='Unidades',
                         color='Segmento', color_discrete_map=SEG_COLORS,
                         title="Mercado por Segmento de Peso (PBV kg)")
        fig_seg.update_layout(plot_bgcolor='white', showlegend=False, height=380)
        fig_seg.update_traces(textposition='outside')
        render_bloque("", fig_seg, seg_act, "seg_peso", "segmento_peso")

        with st.expander("📋 Ver tabla — Variación Anual por Segmento", expanded=False):
            años_lista = sorted([int(a) for a in df_actual['año'].dropna().unique()])
            resumen_s = []
            for seg in SEG_ORDEN[:-1]:  # excluir SIN DATO
                fila = {'Segmento': seg}
                prev = None
                for a in años_lista:
                    val = int((df_actual['año']==a).values.__and__(
                        (df_actual['segmento_peso']==seg).values).sum())
                    fila[str(a)] = val
                    if prev is not None and prev > 0:
                        fila[f"VAR {a}"] = f"{((val-prev)/prev*100):+.1f}%"
                    prev = val
                if any(fila.get(str(a),0)>0 for a in años_lista):
                    resumen_s.append(fila)
            if resumen_s:
                st.dataframe(fmt_tabla(pd.DataFrame(resumen_s)), hide_index=True, use_container_width=True)

        with st.expander("🔍 Ver tabla — Composición por Segmento (marca + modelo)", expanded=False):
            segs_disp = [s for s in SEG_ORDEN[:-1] if (df_actual['segmento_peso']==s).any()]
            seg_pick = safe_selectbox("Segmento a revisar:", segs_disp, key="seg_composicion_pick")
            sub = df_actual[df_actual['segmento_peso'] == seg_pick]
            total = len(sub)
            comp = (sub.groupby([COL_MARCA, COL_MODELO], observed=True)
                       .size().reset_index(name='Unidades')
                       .sort_values('Unidades', ascending=False))
            comp['% del segmento'] = (comp['Unidades']/total*100).round(1)
            comp.columns = ['Marca', 'Modelo', 'Unidades', '% del segmento']
            st.caption(f"{seg_pick} — {total:,} unidades")
            st.dataframe(fmt_tabla(comp), hide_index=True, use_container_width=True, height=400)

    else:
        st.markdown("##### 📋 Variación Anual por Tipo de Carrocería")
        años_lista = sorted([int(a) for a in df_actual['año'].dropna().unique()])
        resumen = []
        for cat in (cat_sel or cats_disp):
            fila = {'Carrocería': cat}
            prev = None
            for a in años_lista:
                mask = (df_actual['año']==a) & (df_actual['categoria_carroceria']==cat)
                val = int(mask.sum())
                fila[str(a)] = val
                if prev is not None and prev > 0:
                    fila[f"VAR {a}"] = f"{((val-prev)/prev*100):+.1f}%"
                prev = val
            if any(fila.get(str(a),0)>0 for a in años_lista):
                resumen.append(fila)
        if resumen:
            st.dataframe(fmt_tabla(pd.DataFrame(resumen)), hide_index=True, use_container_width=True)
        elif años_lista:
            st.info(f"Años disponibles: {años_lista}. Verifica los filtros de carrocería.")
    with st.expander("🥧 Ver más cortes (Carrocería, Combustible, Tracción)", expanded=False):
        cl, cr = st.columns(2)
        with cl:
            share = df_actual['categoria_carroceria'].value_counts().reset_index()
            share.columns = ['Carrocería','Unidades']
            share['% Share'] = (share['Unidades']/share['Unidades'].sum()*100).round(1)
            fig_p = px.pie(share, values='Unidades', names='Carrocería', hole=0.4,
                           color_discrete_sequence=COLOR_PALETTE)
            render_bloque("🥧 Por Carrocería", fig_p, share, "share", "market_share")
        with cr:
            if 'combustible_norm' in df_actual.columns:
                comb = df_actual['combustible_norm'].value_counts().reset_index()
                comb.columns = ['Combustible','Unidades']
                fig_cb = px.pie(comb[comb['Unidades']>0], values='Unidades', names='Combustible',
                                hole=0.4, color_discrete_sequence=COLOR_PALETTE)
                render_bloque("⛽ Por Combustible", fig_cb, comb, "comb", "combustible")
            if 'traccion' in df_actual.columns:
                st.divider()
                trac = df_actual['traccion'].value_counts().head(8).reset_index()
                trac.columns = ['Tracción','Unidades']
                fig_tr = px.bar(trac[trac['Unidades']>0], x='Tracción', y='Unidades',
                                text_auto=True, color_discrete_sequence=['#4A90E2'])
                fig_tr.update_layout(plot_bgcolor='white', showlegend=False)
                render_bloque("⚙️ Por Tracción", fig_tr, trac, "trac", "traccion")

def render_comparador_marcas():
    """Comparador de 2 marcas promovido a expander de primer nivel (liz-z26.7)
    -- versión liviana (unidades + FOB + share + tendencia mensual), simplificada
    a solo marcas (sin el toggle Importadores). El comparador completo (con
    carrocería/top modelos/evolución de precios, y también disponible para
    Importadores) sigue dentro de 'Competidores' -> Comparativa detallada."""
    min_uds_cmp = st.number_input("Mín. unidades para aparecer en el comparador:",
                                  min_value=1, value=20, step=5, key="min_uds_cmp")
    marcas_cmp = sorted(df_actual[df_actual[COL_MARCA].notna()][COL_MARCA].unique())
    marcas_cmp = [m for m in marcas_cmp if (df_actual[COL_MARCA] == m).sum() >= min_uds_cmp]

    if len(marcas_cmp) < 2:
        if es_sinotruk:
            st.info("Solo hay 1 marca en Modo Sinotruk — cambiá a Vista Global para comparar.")
        else:
            st.info("No hay suficientes marcas con volumen para comparar (bajá el mínimo de unidades).")
        return

    ca, cb = st.columns(2)
    with ca:
        m_a = safe_selectbox("Marca A", marcas_cmp, index=0, key="cmp_marca_a")
    with cb:
        m_b = safe_selectbox("Marca B", marcas_cmp, index=min(1, len(marcas_cmp) - 1), key="cmp_marca_b")

    if m_a == m_b:
        st.warning("Elegí dos marcas distintas para comparar.")
        return

    df_a = df_actual[df_actual[COL_MARCA] == m_a]
    df_b = df_actual[df_actual[COL_MARCA] == m_b]
    u_a, u_b = len(df_a), len(df_b)
    s_a, s_b = pct(u_a, total_act), pct(u_b, total_act)
    fob_a = df_a[COL_FOB].mean() if COL_FOB and COL_FOB in df_a.columns and df_a[COL_FOB].sum() > 0 else None
    fob_b = df_b[COL_FOB].mean() if COL_FOB and COL_FOB in df_b.columns and df_b[COL_FOB].sum() > 0 else None

    cc1, cc2 = st.columns(2)
    with cc1:
        st.metric(f"🏷️ {m_a}", f"{u_a:,} uds", f"{s_a:.1f}% share")
        if fob_a:
            st.caption(f"FOB Prom: US$ {fob_a:,.0f}")
    with cc2:
        st.metric(f"🏷️ {m_b}", f"{u_b:,} uds", f"{s_b - s_a:+.1f}pp vs {m_a[:15]}")
        if fob_b:
            st.caption(f"FOB Prom: US$ {fob_b:,.0f}")

    if MOSTRAR_GRAFICO:
        t_a = df_a.groupby('mes_nombre').size().reset_index(name=str(m_a)[:20])
        t_b = df_b.groupby('mes_nombre').size().reset_index(name=str(m_b)[:20])
        h2h = t_a.merge(t_b, on='mes_nombre', how='outer').fillna(0)
        h2h['mes_nombre'] = pd.Categorical(h2h['mes_nombre'], MESES_NOMBRES, ordered=True)
        fig_h = px.line(h2h.sort_values('mes_nombre').melt(id_vars='mes_nombre', var_name='Actor', value_name='Uds'),
                        x='mes_nombre', y='Uds', color='Actor', markers=True,
                        labels={'mes_nombre': 'Mes'},
                        color_discrete_sequence=COLOR_PALETTE, title="Tendencia mensual")
        fig_h.update_layout(plot_bgcolor='white', height=280)
        st.plotly_chart(fig_h, use_container_width=True)

    st.caption("Para el detalle completo (carrocería, top modelos, evolución de precios) "
               "y comparar por Importador, abrí '🏆 Competidores' → Comparativa detallada.")


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN PRESERVADA — COMPETENCIA (head-to-head, detalle de importadores)
# ══════════════════════════════════════════════════════════════════════════════
def render_competencia():
    cr1, cr2, cr3 = st.columns([2, 1, 1])
    with cr1:
        modo = st.radio("Ver por:", ["🏆 Marcas","🏢 Importadores"],
                        horizontal=True, label_visibility="collapsed", key="modo_comp")
    with cr2:
        top_n = st.number_input("Top N:", min_value=5, max_value=100, value=15,
                                step=5, label_visibility="visible", key="top_n")
    with cr3:
        min_uds = st.number_input("Mín. uds:", min_value=1, value=20, step=5,
                                   label_visibility="visible", key="min_uds")

    COL_ACTOR = COL_MARCA if "Marcas" in modo else 'grupo_importador'
    label_a   = "Marca"    if "Marcas" in modo else "Importador"
    años_port = sorted([int(a) for a in df_actual['año'].dropna().unique()])

    # ── Gráfico top siempre visible ───────────────────────────────────────────
    top_bar = (df_actual[COL_ACTOR].value_counts()
               .reset_index(name='TOTAL')
               .rename(columns={COL_ACTOR: label_a})
               .query("TOTAL >= @min_uds")
               .head(top_n))
    if not top_bar.empty:
        cols_bar = [COLOR_SINOTRUK if 'ISUZU' in str(r) or 'WITHMORY' in str(r) or 'SINOTRUK' in str(r)
                    else '#4A90E2' for r in top_bar[label_a]]
        fig_top = px.bar(top_bar, x=label_a, y='TOTAL', text='TOTAL',
                         title=f"Top {len(top_bar)} {label_a}s  ·  mín {min_uds} uds",
                         color='TOTAL', color_continuous_scale=['#1E448A','#4A90E2','#F6E421'])
        fig_top.update_layout(plot_bgcolor='white', height=300, showlegend=False,
                              coloraxis_showscale=False, xaxis_tickangle=-30,
                              margin=dict(t=40,b=10))
        fig_top.update_traces(textposition='outside')
        st.plotly_chart(fig_top, use_container_width=True)

    st.divider()

    # ── Ranking + Detalle ─────────────────────────────────────────────────────
    rank_act = df_actual[COL_ACTOR].value_counts().reset_index(name=str(año_actual))
    rank_ant = df_anterior[COL_ACTOR].value_counts().reset_index(name=str(año_actual-1))
    ranking  = (rank_act.merge(rank_ant, on=COL_ACTOR, how='outer')
                .fillna(0).sort_values(str(año_actual), ascending=False)
                .head(top_n).reset_index(drop=True))
    ranking = ranking[ranking[str(año_actual)] >= min_uds]
    ranking[[str(año_actual),str(año_actual-1)]] = ranking[[str(año_actual),str(año_actual-1)]].astype(int)
    ranking.insert(0,'N°',ranking.index+1)
    tot_s = ranking[str(año_actual)].sum()
    ranking['MS%'] = (ranking[str(año_actual)]/(tot_s if tot_s else 1)*100).round(1).astype(str)+'%'
    ranking['Var'] = ranking.apply(lambda r: calc_var(r,str(año_actual),str(año_actual-1)), axis=1)
    rv = ranking[['N°',COL_ACTOR,str(año_actual-1),str(año_actual),'Var','MS%']]

    col_izq, col_der = st.columns([2.2, 2.8])

    with col_izq:
        st.markdown(f"##### 📋 {label_a}s  ·  mín {min_uds} uds")
        ev = st.dataframe(fmt_tabla(rv.style.apply(destacar_sinotruk, axis=1)),
                          hide_index=True, use_container_width=True,
                          on_select="rerun", selection_mode="single-row")

    with col_der:
        filas = ev.selection.rows
        if filas:
            actor = rv.iloc[filas[0]][COL_ACTOR]
            df_f  = df_actual[df_actual[COL_ACTOR]==actor]

            st.markdown(f"#### 🔎 **{actor}**")
            c1,c2,c3 = st.columns(3)
            c1.metric("📦 Uds", f"{len(df_f):,}")
            c2.metric("📊 Share", f"{len(df_f)/total_act*100:.1f}%")

            # Selector FOB/CIF
            tiene_cif = COL_CIF and COL_CIF in df_f.columns and df_f[COL_CIF].sum()>0
            if tiene_cif:
                tipo_p = st.radio("💰", ["📦 FOB","🚢 CIF"], horizontal=True,
                                  key=f"tp_{actor}", label_visibility="collapsed",
                                  help="FOB = valor de exportación sin flete ni seguro · "
                                       "CIF = valor con flete y seguro incluido hasta destino.")
                col_p = COL_FOB if "FOB" in tipo_p else COL_CIF
                nom_p = "FOB" if "FOB" in tipo_p else "CIF"
            else:
                col_p = COL_FOB
                nom_p = "FOB"

            if col_p and col_p in df_f.columns and df_f[col_p].sum()>0:
                c3.metric(f"💰 {nom_p} Prom", f"US$ {df_f[col_p].mean():,.0f}")

            # Importadores/Marcas
            sub_col   = 'grupo_importador' if "Marcas" in modo else COL_MARCA
            sub_label = "Importadores"     if "Marcas" in modo else "Marcas"
            sub_vc = df_f[sub_col].value_counts().head(8).reset_index()
            sub_vc.columns = [sub_label,'Uds']
            fig_sub = px.bar(sub_vc, x=sub_label, y='Uds', text_auto=True,
                             color_discrete_sequence=['#4A90E2'],
                             title=f"{sub_label} de {actor[:30]}")
            fig_sub.update_layout(plot_bgcolor='white', height=180,
                                  margin=dict(t=30,b=5,l=5,r=5), showlegend=False,
                                  xaxis_tickangle=-25)
            st.plotly_chart(fig_sub, use_container_width=True)

            # Top Modelos con Carrocería + precio
            if COL_MODELO in df_f.columns:
                st.markdown("##### 🚛 Top Modelos")
                top_mod = (df_f.groupby([COL_MODELO,'categoria_carroceria'])
                           .size().reset_index(name='Uds')
                           .sort_values('Uds', ascending=False).head(10))
                top_mod = top_mod.rename(columns={COL_MODELO:'Modelo','categoria_carroceria':'Carrocería'})
                if col_p and col_p in df_f.columns:
                    fob_m = df_f.groupby(COL_MODELO)[col_p].mean().reset_index()
                    fob_m.columns = [COL_MODELO, f'{nom_p} Prom']
                    fob_m[f'{nom_p} Prom'] = fob_m[f'{nom_p} Prom'].apply(lambda x: f"US$ {x:,.0f}")
                    top_mod = top_mod.merge(fob_m, left_on='Modelo', right_on=COL_MODELO,
                                            how='left').drop(columns=COL_MODELO, errors='ignore')
                st.dataframe(fmt_tabla(top_mod), hide_index=True, use_container_width=True)

            # Explorar carrocería específica
            with st.expander("🚛 Explorar carrocería específica"):
                carr_data = df_f['categoria_carroceria'].value_counts().reset_index()
                carr_data.columns = ['Carrocería','Uds']
                carr_data = carr_data[carr_data['Uds']>0]
                if not carr_data.empty:
                    fig_carr = px.bar(carr_data, x='Carrocería', y='Uds', text_auto=True,
                                      color='Carrocería', color_discrete_sequence=COLOR_PALETTE,
                                      title=f"Carrocerías de {actor[:30]}")
                    fig_carr.update_layout(plot_bgcolor='white', height=200,
                                           margin=dict(t=30,b=5), showlegend=False)
                    st.plotly_chart(fig_carr, use_container_width=True)

                    carrs = ['TODOS'] + list(carr_data['Carrocería'].unique())
                    carr_sel = safe_selectbox("Selecciona carrocería:", carrs, key=f"carr_{actor}")
                    if carr_sel != 'TODOS' and COL_MODELO in df_f.columns:
                        df_carr = df_f[df_f['categoria_carroceria']==carr_sel]
                        st.markdown(f"##### Modelos — {carr_sel}")
                        mods_carr = df_carr.groupby(COL_MODELO).size().reset_index(name='Uds')
                        if col_p and col_p in df_carr.columns:
                            prc = df_carr.groupby(COL_MODELO)[col_p].agg(['min','mean','max']).reset_index()
                            prc.columns = [COL_MODELO, f'{nom_p} Mín', f'{nom_p} Prom', f'{nom_p} Máx']
                            mods_carr = mods_carr.merge(prc, on=COL_MODELO, how='left')
                            for c in [f'{nom_p} Mín',f'{nom_p} Prom',f'{nom_p} Máx']:
                                if c in mods_carr.columns:
                                    mods_carr[c] = mods_carr[c].apply(lambda x: f"US$ {x:,.0f}")
                        mods_carr = mods_carr.rename(columns={COL_MODELO:'Modelo'})
                        st.dataframe(fmt_tabla(mods_carr), hide_index=True, use_container_width=True)

            # Evolución anual — chart + tabla
            with st.expander("📈 Evolución anual"):
                evo = df_f.groupby(['año','mes','mes_nombre']).size().reset_index(name='n')
                evo['periodo'] = evo['mes_nombre'] + " " + evo['año'].astype(str)
                evo = evo.sort_values(['año','mes'])
                fig_evo = px.line(evo, x='periodo', y='n', markers=True,
                                  color_discrete_sequence=['#F6E421'],
                                  title=f"Importaciones mensuales — {actor[:30]}")
                fig_evo.update_layout(plot_bgcolor='white', height=220)
                st.plotly_chart(fig_evo, use_container_width=True)

                # Tabla anual por año
                tbl_anual = df_f.groupby('año').size().reset_index(name='Uds')
                tbl_anual['año'] = tbl_anual['año'].astype(str)
                tbl_wide = tbl_anual.set_index('año').T.reset_index(drop=True)
                tbl_wide.insert(0, 'Actor', actor[:30])
                st.dataframe(fmt_tabla(tbl_wide), hide_index=True, use_container_width=True)

            # Evolución de precios por modelo
            if col_p and col_p in df_f.columns and COL_MODELO in df_f.columns:
                with st.expander("💰 Evolución de precios por modelo"):
                    top5 = top_mod['Modelo'].head(5).tolist() if 'top_mod' in dir() else []
                    evp = (df_f.groupby(['año','mes','mes_nombre',COL_MODELO])[col_p]
                           .mean().reset_index())
                    evp['periodo'] = evp['mes_nombre'] + " " + evp['año'].astype(str)
                    evp = evp.sort_values(['año','mes'])
                    ver_todos_p = st.checkbox("Mostrar todos los modelos", key=f"vtp_{actor}")
                    if not ver_todos_p and top5:
                        evp = evp[evp[COL_MODELO].isin(top5)]
                    if not evp.empty:
                        fig_evp = px.line(evp, x='periodo', y=col_p, color=COL_MODELO,
                                          markers=True, color_discrete_sequence=COLOR_PALETTE,
                                          title="FOB Promedio por Modelo")
                        fig_evp.update_layout(plot_bgcolor='white', height=280,
                                              yaxis_tickprefix='US$ ', yaxis_tickformat=',.0f',
                                              legend=dict(orientation="h", y=1.02))
                        st.plotly_chart(fig_evp, use_container_width=True)

                        var_p = []
                        for mod in evp[COL_MODELO].unique():
                            dm = evp[evp[COL_MODELO]==mod].sort_values(['año','mes'])
                            if len(dm)>=2:
                                pi, pf = dm[col_p].iloc[0], dm[col_p].iloc[-1]
                                vp = (pf-pi)/pi*100 if pi>0 else 0
                                var_p.append({'Modelo':mod,'Precio Inicial':f"US$ {pi:,.0f}",
                                              'Precio Final':f"US$ {pf:,.0f}",
                                              'Variación %':f"{vp:+.1f}%",
                                              'Tendencia':'📈 Subida' if vp>0 else '📉 Bajada'})
                        if var_p:
                            df_vp = pd.DataFrame(var_p).sort_values('Variación %', ascending=False)
                            st.dataframe(fmt_tabla(df_vp), hide_index=True, use_container_width=True)
                            mx, mn = df_vp.iloc[0], df_vp.iloc[-1]
                            cm1,cm2 = st.columns(2)
                            cm1.metric(f"📈 Mayor Subida: {mx['Modelo']}", mx['Variación %'])
                            cm2.metric(f"📉 Mayor Bajada: {mn['Modelo']}", mn['Variación %'])

            # Evolución de unidades por modelo
            if COL_MODELO in df_f.columns:
                with st.expander("📦 Evolución de unidades por modelo"):
                    evu = (df_f.groupby(['año','mes','mes_nombre',COL_MODELO])
                           .size().reset_index(name='Uds'))
                    evu['periodo'] = evu['mes_nombre'] + " " + evu['año'].astype(str)
                    evu = evu.sort_values(['año','mes'])
                    top5u = top_mod['Modelo'].head(5).tolist() if 'top_mod' in dir() else []
                    ver_todos_u = st.checkbox("Mostrar todos los modelos", key=f"vtu_{actor}")
                    if not ver_todos_u and top5u:
                        evu = evu[evu[COL_MODELO].isin(top5u)]
                    if not evu.empty:
                        fig_evu = px.line(evu, x='periodo', y='Uds', color=COL_MODELO,
                                          markers=True, color_discrete_sequence=COLOR_PALETTE,
                                          title="Evolución de Unidades por Modelo")
                        fig_evu.update_layout(plot_bgcolor='white', height=280,
                                              legend=dict(orientation="h", y=1.02))
                        st.plotly_chart(fig_evu, use_container_width=True)

                        var_u = []
                        for mod in evu[COL_MODELO].unique():
                            dm = evu[evu[COL_MODELO]==mod].sort_values(['año','mes'])
                            if len(dm)>=2:
                                ui, uf = dm['Uds'].iloc[0], dm['Uds'].iloc[-1]
                                vu = (uf-ui)/ui*100 if ui>0 else 0
                                var_u.append({'Modelo':mod,'Uds Inicial':int(ui),
                                              'Uds Final':int(uf),
                                              'Variación %':f"{vu:+.1f}%",
                                              'Tendencia':'📈 Subida' if vu>0 else '📉 Bajada'})
                        if var_u:
                            df_vu = pd.DataFrame(var_u).sort_values('Variación %', ascending=False)
                            st.dataframe(fmt_tabla(df_vu), hide_index=True, use_container_width=True)
                            mu1, mu2 = df_vu.iloc[0], df_vu.iloc[-1]
                            cu1,cu2 = st.columns(2)
                            cu1.metric(f"📈 Mayor Crecimiento: {mu1['Modelo']}", mu1['Variación %'])
                            cu2.metric(f"📉 Mayor Caída: {mu2['Modelo']}", mu2['Variación %'])
        else:
            st.info(f"💡 Clic en cualquier {label_a.lower()} para ver su detalle completo.")

    # ── Comparativa head to head ───────────────────────────────────────────────
    with st.expander("⚔️ Comparativa detallada entre actores"):
        actores_hh = sorted(df_actual[df_actual[COL_ACTOR].notna()][COL_ACTOR].unique())
        actores_hh = [a for a in actores_hh
                      if df_actual[df_actual[COL_ACTOR]==a].shape[0] >= min_uds]
        if len(actores_hh) >= 2:
            ca, cb = st.columns(2)
            with ca:
                a_a = safe_selectbox(f"{label_a} A", actores_hh, index=0, key="h2h_a")
            with cb:
                a_b = safe_selectbox(f"{label_a} B", actores_hh,
                                    index=min(1,len(actores_hh)-1), key="h2h_b")
            if a_a != a_b:
                df_a = df_actual[df_actual[COL_ACTOR]==a_a]
                df_b = df_actual[df_actual[COL_ACTOR]==a_b]

                # FOB/CIF para comparativa
                tipo_pc = st.radio("💰 Valor aduanero:",["📦 FOB","🚢 CIF"],
                                   horizontal=True, key="tipo_pc",
                                   label_visibility="collapsed")
                col_pc = COL_FOB if "FOB" in tipo_pc else COL_CIF
                nom_pc = "FOB" if "FOB" in tipo_pc else "CIF"

                # Métricas
                u_a, u_b = len(df_a), len(df_b)
                p_a = df_a[col_pc].mean() if col_pc and col_pc in df_a.columns else None
                p_b = df_b[col_pc].mean() if col_pc and col_pc in df_b.columns else None
                s_a = u_a/total_act*100
                s_b = u_b/total_act*100

                st.markdown("##### 📊 Métricas Comparativas")
                mm1, mm2 = st.columns(2)
                with mm1:
                    st.markdown(f"""<div style="background:#F8F9FA;padding:15px;border-radius:10px;
                    border:1px solid #E8E8E8;text-align:center;">
                    <h4 style="margin:0 0 10px 0">🏷️ {a_a[:25]}</h4>
                    <div style="font-size:1.1rem;font-weight:600">{u_a:,}</div>
                    <div style="font-size:0.75rem;color:#888;margin-bottom:5px">📦 Unidades</div>
                    <div style="font-size:1.1rem;font-weight:600">{"US$ {:,.0f}".format(p_a) if p_a else "N/A"}</div>
                    <div style="font-size:0.75rem;color:#888;margin-bottom:5px">💰 {nom_pc} Prom</div>
                    <div style="font-size:1.1rem;font-weight:600">{s_a:.1f}%</div>
                    <div style="font-size:0.75rem;color:#888">📊 Market Share</div></div>""",
                    unsafe_allow_html=True)
                with mm2:
                    du = u_b-u_a
                    dp = (p_b-p_a) if p_a and p_b else None
                    ds = s_b-s_a
                    cu = "#4CAF50" if du>0 else "#FF5252"
                    cp_c = "#4CAF50" if dp and dp<0 else "#FF5252"
                    cs = "#4CAF50" if ds>0 else "#FF5252"
                    st.markdown(f"""<div style="background:#F8F9FA;padding:15px;border-radius:10px;
                    border:1px solid #E8E8E8;text-align:center;">
                    <h4 style="margin:0 0 10px 0">🏷️ {a_b[:25]}</h4>
                    <div style="font-size:1.1rem;font-weight:600">{u_b:,}</div>
                    <div style="font-size:0.7rem;color:{cu}">{'▲' if du>0 else '▼'} {du:+,} vs {a_a[:15]}</div>
                    <div style="font-size:0.75rem;color:#888;margin-bottom:5px">📦 Unidades</div>
                    <div style="font-size:1.1rem;font-weight:600">{"US$ {:,.0f}".format(p_b) if p_b else "N/A"}</div>
                    <div style="font-size:0.7rem;color:{cp_c}">{"US$ {:+,.0f}".format(dp) if dp else ""}</div>
                    <div style="font-size:0.75rem;color:#888;margin-bottom:5px">💰 {nom_pc} Prom</div>
                    <div style="font-size:1.1rem;font-weight:600">{s_b:.1f}%</div>
                    <div style="font-size:0.7rem;color:{cs}">{ds:+.1f} pp vs {a_a[:15]}</div>
                    <div style="font-size:0.75rem;color:#888">📊 Market Share</div></div>""",
                    unsafe_allow_html=True)

                st.markdown("##### 📈 Tendencia Mensual")
                t_a = df_a.groupby('mes_nombre').size().reset_index(name=str(a_a)[:20])
                t_b = df_b.groupby('mes_nombre').size().reset_index(name=str(a_b)[:20])
                h2h = t_a.merge(t_b, on='mes_nombre', how='outer').fillna(0)
                h2h['mes_nombre'] = pd.Categorical(h2h['mes_nombre'], MESES_NOMBRES, ordered=True)
                fig_h = px.line(h2h.melt(id_vars='mes_nombre', var_name='Actor', value_name='Uds'),
                                x='mes_nombre', y='Uds', color='Actor', markers=True,
                                labels={'mes_nombre': 'Mes'},
                                color_discrete_sequence=COLOR_PALETTE)
                fig_h.update_layout(plot_bgcolor='white', height=230)
                st.plotly_chart(fig_h, use_container_width=True)

                st.markdown("##### 🚛 Comparación por Carrocería")
                años_hh = sorted(set(df_a['año'].dropna().unique()) |
                                 set(df_b['año'].dropna().unique()))
                año_sel = safe_selectbox("Año:", [int(a) for a in años_hh],
                                       index=len(años_hh)-1, key="año_hh")
                da_año = df_a[df_a['año']==año_sel]
                db_año = df_b[df_b['año']==año_sel]
                seg_a2 = da_año['categoria_carroceria'].value_counts().reset_index()
                seg_a2.columns = ['Carrocería', str(a_a)[:15]]
                seg_b2 = db_año['categoria_carroceria'].value_counts().reset_index()
                seg_b2.columns = ['Carrocería', str(a_b)[:15]]
                seg_h = seg_a2.merge(seg_b2, on='Carrocería', how='outer').fillna(0)
                fig_seg_h = px.bar(seg_h.melt(id_vars='Carrocería',
                                              var_name='Actor', value_name='Uds'),
                                   x='Carrocería', y='Uds', color='Actor', barmode='group',
                                   color_discrete_sequence=COLOR_PALETTE,
                                   title=f"Comparación por Carrocería — {año_sel}")
                fig_seg_h.update_layout(plot_bgcolor='white', height=250)
                st.plotly_chart(fig_seg_h, use_container_width=True)

                # Tablas evolución por carrocería
                ct_a, ct_b = st.columns(2)
                for col_t, df_t, nom_t in [(ct_a, df_a, a_a), (ct_b, df_b, a_b)]:
                    with col_t:
                        st.markdown(f"**{nom_t[:25]}**")
                        ev_s = (df_t.groupby(['año','categoria_carroceria']).size()
                                .unstack(fill_value=0).reset_index())
                        ev_s.columns = ['Carrocería'] + [str(c) for c in ev_s.columns[1:]]
                        anios_t = [c for c in ev_s.columns if c != 'Carrocería']
                        if len(anios_t)>=2:
                            ev_s['Var%'] = ((ev_s[anios_t[-1]]-ev_s[anios_t[0]])/
                                            ev_s[anios_t[0]]*100).fillna(0).apply(
                                            lambda x: f"{x:+.1f}%")
                        st.dataframe(fmt_tabla(ev_s), hide_index=True, use_container_width=True)

                # Top modelos del último año
                st.markdown(f"##### 🏗️ Top Modelos — {año_sel}")
                cta2, ctb2 = st.columns(2)
                for col_t, df_t, nom_t in [(cta2, da_año, a_a), (ctb2, db_año, a_b)]:
                    with col_t:
                        st.markdown(f"**{nom_t[:25]}**")
                        if COL_MODELO in df_t.columns:
                            tm = (df_t.groupby([COL_MODELO,'categoria_carroceria'])
                                  .size().reset_index(name='Uds')
                                  .sort_values('Uds',ascending=False).head(8))
                            tm = tm.rename(columns={COL_MODELO:'Modelo',
                                                     'categoria_carroceria':'Carrocería'})
                            if col_pc and col_pc in df_t.columns:
                                fob_t = df_t.groupby(COL_MODELO)[col_pc].mean().reset_index()
                                fob_t.columns = [COL_MODELO, f'{nom_pc} Prom']
                                fob_t[f'{nom_pc} Prom'] = fob_t[f'{nom_pc} Prom'].apply(
                                    lambda x: f"US$ {x:,.0f}")
                                tm = tm.merge(fob_t, left_on='Modelo',
                                              right_on=COL_MODELO, how='left').drop(
                                              columns=COL_MODELO, errors='ignore')
                            st.dataframe(fmt_tabla(tm), hide_index=True, use_container_width=True)

                # Evolución de precios comparativa
                if col_pc and col_pc in df_a.columns and col_pc in df_b.columns:
                    with st.expander("📈 Evolución de precios en el tiempo"):
                        epc_a = df_a.groupby(['año','mes','mes_nombre'])[col_pc].mean().reset_index()
                        epc_b = df_b.groupby(['año','mes','mes_nombre'])[col_pc].mean().reset_index()
                        for d, n in [(epc_a,str(a_a)[:20]),(epc_b,str(a_b)[:20])]:
                            d['periodo'] = d['mes_nombre']+" "+d['año'].astype(str)
                            d['Actor'] = n
                        evpc = pd.concat([epc_a.sort_values(['año','mes']),
                                          epc_b.sort_values(['año','mes'])])
                        fig_pc = px.line(evpc, x='periodo', y=col_pc, color='Actor',
                                         markers=True, color_discrete_sequence=COLOR_PALETTE,
                                         title=f"Evolución {nom_pc} Promedio")
                        fig_pc.update_layout(plot_bgcolor='white', height=260,
                                             yaxis_tickprefix='US$ ', yaxis_tickformat=',.0f')
                        st.plotly_chart(fig_pc, use_container_width=True)

OBJETIVO_MS_SINOTRUK_DEFAULT = 25.0  # ver widget "Objetivo MS%" en render_sinotruk()


def calcular_estado_sinotruk(df_act, df_ant, total_act, total_ant,
                              objetivo_ms=OBJETIVO_MS_SINOTRUK_DEFAULT):
    """Métricas + semáforo de negocio de la familia Sinotruk -- extraída de
    render_sinotruk() (liz-z26.4) para reusarse también en el Resumen Ejecutivo
    sin duplicar el cálculo de market share."""
    m_sin = df_act[COL_MARCA].astype(str).str.upper().str.strip() == "SINOTRUK"
    m_sin_ant = df_ant[COL_MARCA].astype(str).str.upper().str.strip() == "SINOTRUK"
    n_sin, n_sin_ant = int(m_sin.sum()), int(m_sin_ant.sum())
    ms_act = pct(n_sin, total_act)
    ms_ant = pct(n_sin_ant, total_ant)
    delta_ms = round(ms_act - ms_ant, 1)
    if delta_ms >= 0 and ms_act >= objetivo_ms:
        estado = "🟢"
    elif delta_ms >= 0:
        estado = "🟡"
    else:
        estado = "🔴"
    return {"estado": estado, "n_sin": n_sin, "n_sin_ant": n_sin_ant,
            "ms_act": ms_act, "ms_ant": ms_ant, "delta_ms": delta_ms, "objetivo_ms": objetivo_ms}


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN PRESERVADA — SINOTRUK / WITHMORY
# ══════════════════════════════════════════════════════════════════════════════
def render_sinotruk():
    m_sin = df_actual[COL_MARCA].astype(str).str.upper().str.strip() == "SINOTRUK"
    df_sin = df_actual[m_sin]

    # Mismo filtro para período anterior
    m_sin_ant = df_anterior[COL_MARCA].astype(str).str.upper().str.strip() == "SINOTRUK"
    df_sin_ant = df_anterior[m_sin_ant]

    if df_sin.empty:
        st.warning(f"No hay registros {MARCA_PROPIA} en el período seleccionado.")
    else:
        # ── Calcular métricas clave ───────────────────────────────────────────
        n_sin      = len(df_sin)
        n_sin_ant  = len(df_sin_ant)
        ms_act     = n_sin / total_act * 100 if total_act else 0
        ms_ant     = n_sin_ant / total_ant * 100 if total_ant else 0
        delta_ms   = ms_act - ms_ant
        fob_sin    = df_sin[COL_FOB].mean() if COL_FOB and COL_FOB in df_sin.columns and df_sin[COL_FOB].sum() > 0 else None
        fob_mkt    = df_actual[COL_FOB].mean() if COL_FOB and COL_FOB in df_actual.columns and df_actual[COL_FOB].sum() > 0 else None
        w_n        = len(df_sin[df_sin['grupo_importador'].str.contains('WITHMORY', na=False)]) if 'grupo_importador' in df_sin.columns else 0
        w_share    = w_n / n_sin * 100 if n_sin else 0

        # ── Objetivo configurable ─────────────────────────────────────────────
        col_hdr, col_obj = st.columns([4, 1])
        with col_hdr:
            st.markdown(f"## 🟡 Familia {MARCA_PROPIA}")
        with col_obj:
            objetivo_ms = st.number_input("Objetivo MS%", min_value=1.0, max_value=100.0,
                                          value=25.0, step=0.5, key="obj_ms",
                                          label_visibility="visible",
                                          help="Meta de Market Share configurada manualmente — "
                                               "no está vinculada a ninguna cuota comercial real.")

        # ── Fila KPIs ─────────────────────────────────────────────────────────
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("📦 Unidades", f"{n_sin:,}",
                  delta=f"{n_sin - n_sin_ant:+,} vs ant.")
        c2.metric("📊 Market Share", f"{ms_act:.1f}%",
                  delta=f"{delta_ms:+.1f} pp vs ant.",
                  delta_color="normal")
        c3.metric("🔄 vs Periodo Anterior (pp)", f"{delta_ms:+.1f} pp",
                  delta=f"anterior: {ms_ant:.1f}%",
                  delta_color="normal")
        if fob_sin:
            delta_fob = f"US$ {fob_sin - fob_mkt:+,.0f} vs mercado" if fob_mkt else None
            c4.metric("💰 FOB Prom.", f"US$ {fob_sin:,.0f}", delta=delta_fob,
                      delta_color="off")
        else:
            c4.metric("💰 FOB Prom.", "N/A")
        c5.metric("🏢 Withmory", f"{w_n:,}",
                  delta=f"{w_share:.0f}% de familia")

        st.divider()

        # ── Withmory vs resto + Evolución MS ─────────────────────────────────────
        col_withmory, col_share_evo = st.columns([1, 2])

        with col_withmory:
            withmory_vc = pd.DataFrame({
                'Grupo': ['Withmory', 'Resto de importadores'],
                'Unidades': [w_n, n_sin - w_n],
            })
            fig_withmory = px.pie(withmory_vc, values='Unidades', names='Grupo', hole=0.5,
                                  title="Withmory vs resto de importadores",
                                  color='Grupo',
                                  color_discrete_map={'Withmory': COLOR_SINOTRUK,
                                                      'Resto de importadores': '#4A90E2'})
            fig_withmory.update_layout(height=260, margin=dict(l=10, r=10, t=40, b=10),
                                       showlegend=True, legend=dict(orientation="h", y=-0.1))
            st.plotly_chart(fig_withmory, use_container_width=True)

        with col_share_evo:
            # Cuota mensual % en el dataset completo — últimos 24 meses
            df_full_ms = df.copy()
            df_full_ms = df_full_ms[df_full_ms['fecha'].notna()].copy()
            df_full_ms['_sin'] = df_full_ms[COL_MARCA].astype(str).str.upper().str.strip() == "SINOTRUK"
            df_full_ms['_ym'] = df_full_ms['año'].astype(str) + '-' + df_full_ms['mes'].astype(str).str.zfill(2)
            ms_evo = (df_full_ms.groupby(['año','mes','mes_nombre','_ym'])
                      .agg(total=('_sin','count'), sin=('_sin','sum'))
                      .reset_index())
            ms_evo['share%'] = (ms_evo['sin'] / ms_evo['total'] * 100).round(1)
            ms_evo = ms_evo[ms_evo['total'] >= 5].sort_values(['año','mes']).tail(24)
            ms_evo['periodo'] = ms_evo['mes_nombre'] + " " + ms_evo['año'].astype(str)

            fig_ms_evo = go.Figure()
            fig_ms_evo.add_hline(y=objetivo_ms, line_dash="dot", line_color="#FF5252",
                                 annotation_text=f"Obj. {objetivo_ms:.0f}%",
                                 annotation_position="top right",
                                 annotation_font_color="#FF5252")
            fig_ms_evo.add_trace(go.Scatter(
                x=ms_evo['periodo'], y=ms_evo['share%'],
                mode='lines+markers',
                line=dict(color=COLOR_SINOTRUK, width=3),
                marker=dict(size=7, color=COLOR_SINOTRUK, line=dict(color='#333', width=1)),
                fill='tozeroy', fillcolor='rgba(246,228,33,0.15)',
                name='Sinotruk MS%',
                hovertemplate='%{x}<br>Share: <b>%{y:.1f}%</b><extra></extra>',
            ))
            fig_ms_evo.update_layout(
                title="Evolución mensual de market share (últimos 24 meses)",
                plot_bgcolor='white', paper_bgcolor='white',
                height=260, margin=dict(l=10, r=10, t=40, b=10),
                yaxis=dict(ticksuffix="%", gridcolor='#F0F0F0', range=[0, None]),
                xaxis=dict(tickangle=-35, gridcolor='#F0F0F0'),
                showlegend=False,
            )
            st.plotly_chart(fig_ms_evo, use_container_width=True)

        st.divider()

        # ── Cuánto paga Sinotruk vs el mercado (liz-z26.9: secundario, en expander) ──
        with st.expander("💰 Cuánto paga Sinotruk vs el mercado", expanded=False):
            cif_sin = df_sin[COL_CIF].mean() if COL_CIF and COL_CIF in df_sin.columns and df_sin[COL_CIF].sum() > 0 else None
            cif_mkt = df_actual[COL_CIF].mean() if COL_CIF and COL_CIF in df_actual.columns and df_actual[COL_CIF].sum() > 0 else None

            col_pf1, col_pf2 = st.columns(2)
            if fob_sin and fob_mkt:
                with col_pf1:
                    delta_fob_pct = (fob_sin - fob_mkt) / fob_mkt * 100
                    fig_fob_cmp = go.Figure(go.Bar(
                        x=['Mercado (todas las marcas)', MARCA_PROPIA],
                        y=[fob_mkt, fob_sin],
                        text=[f"US$ {fob_mkt:,.0f}", f"US$ {fob_sin:,.0f}"],
                        textposition='outside',
                        marker_color=['#4A90E2', COLOR_SINOTRUK],
                    ))
                    fig_fob_cmp.update_layout(
                        title=f"FOB Promedio — {delta_fob_pct:+.1f}% vs mercado",
                        plot_bgcolor='white', height=300, showlegend=False,
                        yaxis=dict(tickprefix="US$ ", gridcolor='#F0F0F0'),
                    )
                    st.plotly_chart(fig_fob_cmp, use_container_width=True)
            if cif_sin and cif_mkt:
                with col_pf2:
                    delta_cif_pct = (cif_sin - cif_mkt) / cif_mkt * 100
                    fig_cif_cmp = go.Figure(go.Bar(
                        x=['Mercado (todas las marcas)', MARCA_PROPIA],
                        y=[cif_mkt, cif_sin],
                        text=[f"US$ {cif_mkt:,.0f}", f"US$ {cif_sin:,.0f}"],
                        textposition='outside',
                        marker_color=['#4A90E2', COLOR_SINOTRUK],
                    ))
                    fig_cif_cmp.update_layout(
                        title=f"CIF Promedio — {delta_cif_pct:+.1f}% vs mercado",
                        plot_bgcolor='white', height=300, showlegend=False,
                        yaxis=dict(tickprefix="US$ ", gridcolor='#F0F0F0'),
                    )
                    st.plotly_chart(fig_cif_cmp, use_container_width=True)
            if not (fob_sin and fob_mkt) and not (cif_sin and cif_mkt):
                st.info("No hay datos de FOB/CIF suficientes para esta comparación.")
            else:
                precio_vs_mercado = pd.DataFrame({
                    'Grupo': ['Mercado (todas las marcas)', MARCA_PROPIA],
                    'FOB Promedio': [fob_mkt, fob_sin] if (fob_sin and fob_mkt) else [None, None],
                    'CIF Promedio': [cif_mkt, cif_sin] if (cif_sin and cif_mkt) else [None, None],
                })
                tabla_dl(precio_vs_mercado, "precio_vs_mercado", "precio_sinotruk_vs_mercado")

        st.divider()

        # ── Importadores Sinotruk — sección principal ───────────────────────────
        st.markdown("### 🏢 Importadores Sinotruk")
        imp_sin = df_sin['grupo_importador'].value_counts().reset_index()
        imp_sin.columns = ['Importador','Unidades']
        imp_sin['% Share'] = (imp_sin['Unidades'] / imp_sin['Unidades'].sum() * 100).round(1)
        colors_sin = [COLOR_SINOTRUK if 'WITHMORY' in str(x).upper() else '#4A90E2'
                      for x in imp_sin['Importador'].head(10)]

        fig_imp = px.bar(imp_sin.head(10), x='Unidades', y='Importador', orientation='h',
                         text_auto=True, title="Importadores Sinotruk")
        fig_imp.update_traces(marker_color=colors_sin)
        fig_imp.update_layout(plot_bgcolor='white', height=350,
                              yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_imp, use_container_width=True)

        with st.expander("📊 Ver tabla — Importadores Sinotruk", expanded=False):
            tabla_dl(imp_sin, "imp_sin", "importadores_sinotruk")

        st.markdown("##### 🔍 Detalle por Importador")
        importador_sel_sin = safe_selectbox(
            "Selecciona un importador para ver su detalle:",
            imp_sin['Importador'].tolist(), key="importador_sin_sel")

        if importador_sel_sin:
            df_imp_det = df_sin[df_sin['grupo_importador'] == importador_sel_sin]

            col_di1, col_di2, col_di3 = st.columns(3)
            col_di1.metric("📦 Unidades", f"{len(df_imp_det):,}")
            col_di2.metric("📂 Segmentos", f"{df_imp_det['categoria_carroceria'].nunique()}")
            n_mod_imp = df_imp_det[COL_MODELO].nunique() if COL_MODELO in df_imp_det.columns else 0
            col_di3.metric("🏗️ Modelos", f"{n_mod_imp}")

            st.markdown("###### 💰 Cuánto paga este importador por modelo")
            col_precio_imp, nombre_precio_imp = None, None
            if COL_FOB and COL_FOB in df_imp_det.columns:
                if COL_CIF and COL_CIF in df_imp_det.columns:
                    tipo_precio_imp = st.radio("Tipo de precio:", ["📦 FOB", "🚢 CIF"],
                                               horizontal=True, key="tipo_precio_imp",
                                               label_visibility="collapsed")
                    col_precio_imp = COL_FOB if "FOB" in tipo_precio_imp else COL_CIF
                    nombre_precio_imp = "FOB" if "FOB" in tipo_precio_imp else "CIF"
                else:
                    col_precio_imp, nombre_precio_imp = COL_FOB, "FOB"

            if col_precio_imp and df_imp_det[col_precio_imp].sum() > 0:
                precio_modelo_imp = (df_imp_det[df_imp_det[col_precio_imp] > 0]
                                     .groupby(COL_MODELO)
                                     .agg(Unidades=(COL_MODELO,'size'), Precio=(col_precio_imp,'mean'))
                                     .reset_index().sort_values('Unidades', ascending=False).head(10))
                precio_modelo_imp['Precio'] = precio_modelo_imp['Precio'].apply(lambda x: f"US$ {x:,.0f}")
                precio_modelo_imp.columns = ['Modelo','Unidades', f'{nombre_precio_imp} Promedio']
                tabla_dl(precio_modelo_imp, "precio_modelo_imp", f"precio_por_modelo_{importador_sel_sin}")
            else:
                st.info(f"No hay datos de {nombre_precio_imp or 'FOB/CIF'} para este importador.")

            st.markdown("###### 🏷️ Cómo lo declara este importador")
            marca_imp = df_imp_det[COL_MARCA].value_counts(normalize=True).reset_index()
            marca_imp.columns = ['Marca Declarada', '% del importador']
            marca_imp['% del importador'] = (marca_imp['% del importador'] * 100).round(1)
            tabla_dl(marca_imp, "marca_decl_imp", f"marca_declarada_{importador_sel_sin}")

            with st.expander("📊 Ver tabla — Evolución del importador", expanded=False):
                evol_imp_det = df_imp_det.groupby(['año','mes','mes_nombre']).size().reset_index(name='Unidades')
                evol_imp_det['periodo'] = evol_imp_det['mes_nombre'] + ' ' + evol_imp_det['año'].astype(str)
                evol_imp_det = evol_imp_det.sort_values(['año','mes'])
                if not evol_imp_det.empty:
                    fig_evol_imp_det = px.line(evol_imp_det, x='periodo', y='Unidades', markers=True,
                                               title=f"Evolución mensual — {importador_sel_sin}",
                                               color_discrete_sequence=[COLOR_SINOTRUK])
                    fig_evol_imp_det.update_layout(plot_bgcolor='white', height=280,
                                                   xaxis_title="Período", yaxis_title="Unidades")
                    st.plotly_chart(fig_evol_imp_det, use_container_width=True)
                    st.markdown("**Mensual**")
                    tabla_dl(evol_imp_det[['periodo','Unidades']], "evol_imp_mensual",
                            f"evolucion_mensual_{importador_sel_sin}")

                st.markdown("**Variación anual**")
                evol_anual_imp = df_imp_det.groupby('año').size().reset_index(name='Unidades').sort_values('año')
                evol_anual_imp['Var% vs año anterior'] = evol_anual_imp['Unidades'].pct_change().apply(
                    lambda x: f"{x*100:+.1f}%" if pd.notna(x) else '—')
                tabla_dl(evol_anual_imp, "evol_imp_anual", f"evolucion_anual_{importador_sel_sin}")

        st.divider()

        # ── Sub-marca declarada ──────────────────────────────────────────────────
        st.markdown("#### 🏷️ Sub-marca declarada en aduana")
        sub = df_sin['submarca'].fillna(df_sin[COL_MARCA]) \
              if 'submarca' in df_sin.columns else df_sin[COL_MARCA]
        sub_vc = sub.value_counts().reset_index()
        sub_vc.columns = ['Sub-marca','Unidades']
        fig_sub = px.pie(sub_vc.head(8), values='Unidades', names='Sub-marca', hole=0.4,
                         title="Por sub-marca declarada en aduana",
                         color_discrete_sequence=COLOR_PALETTE)
        st.plotly_chart(fig_sub, use_container_width=True)
        with st.expander("📊 Ver tabla — Sub-marca declarada", expanded=False):
            tabla_dl(sub_vc, "sub_vc", "submarca_declarada")

        st.divider()
        st.markdown("#### ★ Marca Declarada en Aduana por Importador")
        st.caption("SINOTRUK = Withmory oficial · HOWO = Andes Motor (mismo fabricante, distinto posicionamiento)")
        cross = (df_sin.groupby(['grupo_importador', COL_MARCA])
                 .size().reset_index(name='unidades')
                 .sort_values(['grupo_importador','unidades'], ascending=[True,False]))
        cross['% imp'] = cross.groupby('grupo_importador')['unidades'].transform(
            lambda x: (x / x.sum() * 100).round(1))
        with st.expander("📊 Ver tabla — Marca Declarada por Importador", expanded=False):
            tabla_dl(cross.rename(columns={'grupo_importador':'Importador',
                                           COL_MARCA:'Marca Declarada','unidades':'Uds'}),
                     "cross_marca_imp", "marca_declarada_por_importador")

        st.divider()
        st.markdown("#### 🏗️ Top Modelos Sinotruk")
        segmentos_disp_sin = ['TODOS'] + sorted(df_sin['categoria_carroceria'].dropna().unique().tolist())
        segmento_sel_sin = safe_selectbox("Segmento:", segmentos_disp_sin, key="segmento_sel_sin")
        df_sin_modelos = (df_sin if segmento_sel_sin == 'TODOS'
                          else df_sin[df_sin['categoria_carroceria'] == segmento_sel_sin])

        if COL_MODELO in df_sin_modelos.columns and not df_sin_modelos.empty:
            top_modelos_sin = df_sin_modelos.groupby([COL_MODELO,'categoria_carroceria']).size().reset_index(name='Unidades')
            top_modelos_sin = top_modelos_sin.sort_values('Unidades', ascending=False).head(15)
            top_modelos_sin = top_modelos_sin.rename(columns={COL_MODELO:'Modelo','categoria_carroceria':'Segmento'})

            col_precio_sin, nombre_precio_sin = None, None
            if COL_FOB and COL_FOB in df_sin_modelos.columns:
                tiene_cif_sin = COL_CIF and COL_CIF in df_sin_modelos.columns
                if tiene_cif_sin:
                    tipo_precio_sin = st.radio("Tipo de precio:", ["📦 FOB","🚢 CIF"],
                                               horizontal=True, key="tipo_precio_sin",
                                               label_visibility="collapsed")
                    col_precio_sin = COL_FOB if "FOB" in tipo_precio_sin else COL_CIF
                    nombre_precio_sin = "FOB" if "FOB" in tipo_precio_sin else "CIF"
                else:
                    col_precio_sin, nombre_precio_sin = COL_FOB, "FOB"

                precio_sin_modelo = df_sin_modelos.groupby(COL_MODELO)[col_precio_sin].mean().reset_index()
                precio_sin_modelo.columns = ['Modelo', f'{nombre_precio_sin} Promedio']
                top_modelos_sin = top_modelos_sin.merge(precio_sin_modelo, on='Modelo', how='left')

            format_sin = {}
            col_precio_label = f'{nombre_precio_sin} Promedio' if nombre_precio_sin else None
            if col_precio_label and col_precio_label in top_modelos_sin.columns:
                format_sin[col_precio_label] = '${:,.2f}'
            st.dataframe(fmt_tabla(top_modelos_sin, format_sin), hide_index=True, use_container_width=True)
            cx_tm, cy_tm = st.columns(2)
            with cx_tm:
                st.download_button("📥 xlsx", excel_bytes(tuple(top_modelos_sin.itertuples(index=False)), "top_modelos_sinotruk"),
                                    "top_modelos_sinotruk.xlsx", key="xl_top_modelos_sin", use_container_width=True)
            with cy_tm:
                st.download_button("📥 csv", descargar_csv(top_modelos_sin), "top_modelos_sinotruk.csv",
                                    key="csv_top_modelos_sin", use_container_width=True)

            if col_precio_sin:
                with st.expander(f"📈 Evolución de {nombre_precio_sin} por modelo", expanded=False):
                    evol_precio_sin = df_sin_modelos.groupby(['año','mes','mes_nombre',COL_MODELO])[col_precio_sin].mean().reset_index()
                    evol_precio_sin['periodo'] = evol_precio_sin['mes_nombre'] + ' ' + evol_precio_sin['año'].astype(str)
                    evol_precio_sin = evol_precio_sin.sort_values(['año','mes'])
                    ver_todos_precio_sin = st.checkbox("Mostrar todos los modelos", value=False, key="ver_todos_precio_sin")
                    if not ver_todos_precio_sin:
                        top5_modelos_sin = top_modelos_sin['Modelo'].head(5).tolist()
                        evol_precio_sin = evol_precio_sin[evol_precio_sin[COL_MODELO].isin(top5_modelos_sin)]
                    if not evol_precio_sin.empty:
                        fig_evol_precio_sin = px.line(evol_precio_sin, x='periodo', y=col_precio_sin,
                                                      color=COL_MODELO, markers=True,
                                                      title=f"Evolución de {nombre_precio_sin} por Modelo",
                                                      color_discrete_sequence=COLOR_PALETTE)
                        fig_evol_precio_sin.update_layout(plot_bgcolor='white', height=320,
                                                          xaxis_title="Período", yaxis_title=f"{nombre_precio_sin} ($)",
                                                          legend=dict(title="Modelo", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                        st.plotly_chart(fig_evol_precio_sin, use_container_width=True)
                        tabla_dl(evol_precio_sin, "evol_precio_sin", f"evolucion_{nombre_precio_sin}_por_modelo")
                    else:
                        st.info("No hay suficientes datos para mostrar la evolución de precios.")

            with st.expander("📦 Evolución de unidades por modelo", expanded=False):
                evol_uds_sin = df_sin_modelos.groupby(['año','mes','mes_nombre',COL_MODELO]).size().reset_index(name='Unidades')
                evol_uds_sin['periodo'] = evol_uds_sin['mes_nombre'] + ' ' + evol_uds_sin['año'].astype(str)
                evol_uds_sin = evol_uds_sin.sort_values(['año','mes'])
                ver_todos_uds_sin = st.checkbox("Mostrar todos los modelos", value=False, key="ver_todos_uds_sin")
                if not ver_todos_uds_sin:
                    top5_modelos_sin = top_modelos_sin['Modelo'].head(5).tolist()
                    evol_uds_sin = evol_uds_sin[evol_uds_sin[COL_MODELO].isin(top5_modelos_sin)]
                if not evol_uds_sin.empty:
                    fig_evol_uds_sin = px.line(evol_uds_sin, x='periodo', y='Unidades',
                                               color=COL_MODELO, markers=True,
                                               title="Evolución de Unidades por Modelo",
                                               color_discrete_sequence=COLOR_PALETTE)
                    fig_evol_uds_sin.update_layout(plot_bgcolor='white', height=320,
                                                   xaxis_title="Período", yaxis_title="Unidades",
                                                   legend=dict(title="Modelo", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                    st.plotly_chart(fig_evol_uds_sin, use_container_width=True)
                    tabla_dl(evol_uds_sin, "evol_uds_sin", "evolucion_unidades_por_modelo")
                else:
                    st.info("No hay suficientes datos para mostrar la evolución de unidades.")
        else:
            st.info(f"No hay modelos Sinotruk en el segmento {segmento_sel_sin} para el período seleccionado.")

        st.divider()
        carr_sin = df_sin['categoria_carroceria'].value_counts().reset_index()
        carr_sin.columns = ['Carrocería','Unidades']
        carr_sin = carr_sin[carr_sin['Unidades']>0]
        fig_cs = px.bar(carr_sin, x='Carrocería', y='Unidades',
                        text_auto=True, color='Unidades',
                        color_continuous_scale=['#333','#F6E421'],
                        title="Sinotruk por tipo de carrocería")
        fig_cs.update_layout(plot_bgcolor='white', coloraxis_showscale=False, height=280)
        st.plotly_chart(fig_cs, use_container_width=True)
        with st.expander("📊 Ver tabla — Carrocería", expanded=False):
            tabla_dl(carr_sin, "carr_sin", "carroceria_sinotruk")

        # ── Segmento por peso ─────────────────────────────────────────────────
        if 'segmento_peso' in df_sin.columns and df_sin['pb'].notna().sum() > 0:
            st.divider()
            st.markdown("#### ⚖️ Sinotruk por Segmento de Peso")
            seg_sin = df_sin[df_sin['segmento_peso']!='SIN DATO']['segmento_peso'].value_counts().reset_index()
            seg_sin.columns = ['Segmento','Unidades']
            seg_sin['Segmento'] = pd.Categorical(seg_sin['Segmento'], categories=SEG_ORDEN, ordered=True)
            seg_sin = seg_sin.sort_values('Segmento')
            seg_sin['% del total Sinotruk'] = (seg_sin['Unidades']/len(df_sin)*100).round(1)
            fig_ss = px.bar(seg_sin, x='Segmento', y='Unidades', text='Unidades',
                            color='Segmento', color_discrete_map=SEG_COLORS,
                            title="Familia Sinotruk por Peso Bruto Vehicular")
            fig_ss.update_layout(plot_bgcolor='white', showlegend=False, height=300)
            fig_ss.update_traces(textposition='outside')
            st.plotly_chart(fig_ss, use_container_width=True)
            with st.expander("📊 Ver tabla — Segmento de Peso", expanded=False):
                tabla_dl(seg_sin, "seg_sin", "segmento_de_peso_sinotruk")

        st.divider()
        st.markdown("#### 📈 Evolución Withmory vs Competencia Sinotruk")
        top_imp_sin = df_sin['grupo_importador'].value_counts().head(6).index
        evo_sin = (df_sin[df_sin['grupo_importador'].isin(top_imp_sin)]
                   .groupby(['año','grupo_importador']).size().reset_index(name='n'))
        fig_evo_sin = px.line(evo_sin, x='año', y='n', color='grupo_importador',
                              markers=True, title="Evolución anual top importadores Sinotruk",
                              color_discrete_sequence=COLOR_PALETTE)
        fig_evo_sin.update_layout(plot_bgcolor='white', height=300)
        st.plotly_chart(fig_evo_sin, use_container_width=True)
        with st.expander("📊 Ver tabla — Evolución anual por importador", expanded=False):
            tabla_dl(evo_sin.rename(columns={'grupo_importador':'Importador','n':'Unidades'}),
                     "evo_sin_anual", "evolucion_anual_por_importador")

        # Evolución de unidades por dealer (mensual)
        with st.expander("📦 Evolución mensual de unidades por dealer"):
            todos_imp_sin = ['TODOS'] + sorted(df_sin['grupo_importador'].dropna().unique().tolist())
            imp_sel_sin = safe_selectbox("Importador:", todos_imp_sin, key="imp_sel_sin")
            df_evo_dealer = df_sin if imp_sel_sin=='TODOS' else df_sin[df_sin['grupo_importador']==imp_sel_sin]

            evu_sin = (df_evo_dealer.groupby(['año','mes','mes_nombre',COL_MARCA])
                       .size().reset_index(name='Uds'))
            evu_sin['periodo'] = evu_sin['mes_nombre'] + " " + evu_sin['año'].astype(str)
            evu_sin = evu_sin.sort_values(['año','mes'])

            top5_sin = df_evo_dealer[COL_MARCA].value_counts().head(5).index.tolist()
            ver_todas_sin = st.checkbox("Mostrar todas las marcas", key="vts_sin")
            if not ver_todas_sin:
                evu_sin = evu_sin[evu_sin[COL_MARCA].isin(top5_sin)]

            if not evu_sin.empty:
                fig_evu_sin = px.line(evu_sin, x='periodo', y='Uds', color=COL_MARCA,
                                      markers=True, color_discrete_sequence=COLOR_PALETTE,
                                      title=f"Unidades mensuales — {imp_sel_sin}")
                fig_evu_sin.update_layout(plot_bgcolor='white', height=280,
                                          legend=dict(orientation="h", y=1.02))
                st.plotly_chart(fig_evu_sin, use_container_width=True)

                # Tabla variación por marca
                var_sin = []
                for mk in evu_sin[COL_MARCA].unique():
                    dm = evu_sin[evu_sin[COL_MARCA]==mk].sort_values(['año','mes'])
                    if len(dm)>=2:
                        ui, uf = dm['Uds'].iloc[0], dm['Uds'].iloc[-1]
                        vu = (uf-ui)/ui*100 if ui>0 else 0
                        var_sin.append({'Marca':mk,'Inicial':int(ui),'Final':int(uf),
                                        'Var%':f"{vu:+.1f}%",
                                        'Tend':'📈' if vu>0 else '📉'})
                if var_sin:
                    tabla_dl(pd.DataFrame(var_sin), "var_sin_dealer", f"variacion_marca_{imp_sel_sin}")

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN PRESERVADA — MAPA ORIGEN (fondo blanco, plano, filtros)
# ══════════════════════════════════════════════════════════════════════════════
def render_mapa_origen():
    if 'pais_origen' not in df_actual.columns:
        st.warning("No hay columna pais_origen")
    else:
        df_actual['_origen'] = df_actual['pais_origen'].astype(str).str.upper().str.strip()
        df_actual['_iso']    = df_actual['_origen'].map(PAIS_ISO)

        # Mapa de continentes
        CONTINENTES = {
            "TODOS": None,
            "🌏 Asia":        ["CHN","JPN","KOR","IND","THA","VNM","MYS","IDN","TWN","PAK","SGP"],
            "🌍 Europa":      ["DEU","SWE","ITA","ESP","FRA","GBR","BEL","NLD","POL","AUT","FIN","TUR","CZE","RUS"],
            "🌎 Américas":    ["USA","BRA","MEX","COL","ARG","CHL","PER","ECU","VEN","URY","PRY","BOL","CAN"],
            "🌍 África/Otros":["ZAF","AUS","NZL"],
        }

        tiene_fob = COL_FOB and COL_FOB in df_actual.columns
        agg_dict = dict(unidades=(COL_MARCA,'count'),
                        marcas=(COL_MARCA, lambda x: ', '.join(x.value_counts().head(3).index)))
        if tiene_fob:
            agg_dict['fob_prom'] = (COL_FOB,'mean')

        mapa_df_full = (df_actual.groupby(['_origen','_iso'])
                        .agg(**agg_dict).reset_index().dropna(subset=['_iso']))
        mapa_df_full['lat'] = mapa_df_full['_iso'].map(lambda x: COORDS.get(x,(0,0))[0])
        mapa_df_full['lon'] = mapa_df_full['_iso'].map(lambda x: COORDS.get(x,(0,0))[1])
        mapa_df_full = mapa_df_full.sort_values('unidades', ascending=False)

        # ── Filtros ───────────────────────────────────────────────────────────
        mc1, mc2 = st.columns([2, 3])
        with mc1:
            cont_sel = safe_selectbox("🌍 Continente:", list(CONTINENTES.keys()), key="cont_sel")
        with mc2:
            paises_disp = ["TODOS"] + sorted(mapa_df_full['_origen'].unique().tolist())
            pais_sel = safe_selectbox("🗺️ País específico:", paises_disp, key="pais_sel")

        # Aplicar filtros
        mapa_df = mapa_df_full.copy()
        if cont_sel != "TODOS" and CONTINENTES[cont_sel]:
            mapa_df = mapa_df[mapa_df['_iso'].isin(CONTINENTES[cont_sel])]
        if pais_sel != "TODOS":
            mapa_df = mapa_df[mapa_df['_origen'] == pais_sel]

        if mapa_df.empty:
            st.info("Sin datos para el filtro seleccionado.")
        else:
            max_u = mapa_df['unidades'].max()

            def hover_text(row):
                txt = f"<b>{row['_origen']}</b><br>📦 {row['unidades']:,} uds<br>🚛 {row['marcas']}"
                if 'fob_prom' in row and pd.notna(row['fob_prom']):
                    txt += f"<br>💰 FOB: US$ {row['fob_prom']:,.0f}"
                return txt

            # Mapa plano fondo blanco
            fig_map = go.Figure(go.Scattergeo(
                lon=mapa_df['lon'], lat=mapa_df['lat'],
                text=mapa_df['_origen'],
                hovertext=mapa_df.apply(hover_text, axis=1),
                mode='markers+text',
                textposition='top center',
                textfont=dict(size=9, color='#333333'),
                marker=dict(
                    size=mapa_df['unidades']/max_u*70+12,
                    color=mapa_df['unidades'],
                    colorscale=[[0,'#A9CCE3'],[0.4,'#4A90E2'],
                                [0.7,'#F39C12'],[1,'#F6E421']],
                    showscale=True,
                    colorbar=dict(
                        title=dict(text="Uds", font=dict(color='#333')),
                        tickfont=dict(color='#333'), x=0.88, len=0.6,
                    ),
                    line=dict(color='#FFFFFF', width=1.5),
                    opacity=0.85,
                ),
                hoverinfo='text+name',
                hoverlabel=dict(bgcolor='#1A1A1A', font=dict(color='white',size=13),
                                bordercolor='#F6E421'),
            ))

            # Scope dinámico por continente
            scope_map = {
                "🌏 Asia": "asia",
                "🌍 Europa": "europe",
                "🌎 Américas": "south america",
            }.get(cont_sel, "world")

            fig_map.update_layout(
                geo=dict(
                    scope=scope_map,
                    projection_type='mercator' if cont_sel != "TODOS" else 'equirectangular',
                    showland=True,      landcolor='#F0F0F0',
                    showocean=True,     oceancolor='#D6EAF8',
                    showcountries=True, countrycolor='#CCCCCC', countrywidth=0.5,
                    showframe=False,    showcoastlines=True,
                    coastlinecolor='#AAAAAA', coastlinewidth=0.8,
                    bgcolor='#FFFFFF',
                    showlakes=True,     lakecolor='#D6EAF8',
                ),
                paper_bgcolor='#FFFFFF',
                font=dict(color='#333333'),
                height=500,
                margin=dict(l=10,r=10,t=50,b=10),
                title=dict(
                    text='Importaciones por País de Origen'
                         + (f' · {cont_sel}' if cont_sel != "TODOS" else ''),
                    font=dict(size=16, color='#1A1A1A'), x=0.5, xanchor='center'
                ),
            )
            st.plotly_chart(fig_map, use_container_width=True,
                            config={'displayModeBar':True,'displaylogo':False})

            st.divider()

            # ── Si hay un país seleccionado → detalle de marcas ───────────────
            if pais_sel != "TODOS":
                st.markdown(f"### 🗺️ Detalle: **{pais_sel}**")
                df_pais = df_actual[df_actual['_origen'] == pais_sel]
                total_pais = len(df_pais)

                cp1, cp2, cp3 = st.columns(3)
                cp1.metric("📦 Unidades", f"{total_pais:,}")
                cp2.metric("📊 % del mercado", f"{total_pais/total_act*100:.1f}%")
                if tiene_fob:
                    cp3.metric("💰 FOB Prom", f"US$ {df_pais[COL_FOB].mean():,.0f}")

                cl, cr = st.columns(2)
                with cl:
                    marcas_p = df_pais[COL_MARCA].value_counts().head(12).reset_index()
                    marcas_p.columns = ['Marca','Unidades']
                    marcas_p['% del país'] = (marcas_p['Unidades']/total_pais*100).round(1)
                    fig_mp = px.bar(marcas_p, x='Marca', y='Unidades', text='Unidades',
                                    color='Unidades',
                                    color_continuous_scale=['#4A90E2','#F6E421'],
                                    title=f"Marcas importadas desde {pais_sel}")
                    fig_mp.update_layout(plot_bgcolor='white', showlegend=False,
                                         height=350, coloraxis_showscale=False,
                                         xaxis_tickangle=-30)
                    fig_mp.update_traces(textposition='outside')
                    st.plotly_chart(fig_mp, use_container_width=True)
                with cr:
                    st.markdown(f"##### 📋 Tabla de marcas — {pais_sel}")
                    marcas_p_full = df_pais[COL_MARCA].value_counts().reset_index()
                    marcas_p_full.columns = ['Marca','Unidades']
                    marcas_p_full['% País'] = (marcas_p_full['Unidades']/total_pais*100).round(1).astype(str)+'%'
                    if tiene_fob:
                        fob_p = df_pais.groupby(COL_MARCA)[COL_FOB].mean().reset_index()
                        fob_p.columns = [COL_MARCA,'FOB Prom']
                        fob_p['FOB Prom'] = fob_p['FOB Prom'].apply(lambda x: f"US$ {x:,.0f}")
                        marcas_p_full = marcas_p_full.merge(fob_p, left_on='Marca',
                                                             right_on=COL_MARCA, how='left').drop(
                                                             columns=COL_MARCA, errors='ignore')
                    st.dataframe(fmt_tabla(marcas_p_full), hide_index=True, use_container_width=True)

            else:
                # Vista general: tabla + charts
                cl, cr = st.columns(2)
                with cl:
                    fig_pb = px.bar(mapa_df.head(10).sort_values('unidades'),
                                    x='unidades', y='_origen', orientation='h',
                                    text='unidades', title='Top 10 Países',
                                    color='unidades',
                                    color_continuous_scale=['#4A90E2','#F39C12','#F6E421'])
                    fig_pb.update_layout(plot_bgcolor='white', coloraxis_showscale=False,
                                         height=380, margin=dict(t=40,b=10))
                    fig_pb.update_traces(texttemplate='%{text:,}', textposition='outside')
                    st.plotly_chart(fig_pb, use_container_width=True)
                with cr:
                    fig_pp = px.pie(mapa_df.head(8), values='unidades', names='_origen',
                                    hole=0.5, title='Share por País',
                                    color_discrete_sequence=COLOR_PALETTE)
                    fig_pp.update_layout(paper_bgcolor='white', height=380)
                    st.plotly_chart(fig_pp, use_container_width=True)

                st.divider()
                tabla_m = mapa_df[['_origen','unidades','marcas']].copy()
                tabla_m['% Share'] = (tabla_m['unidades']/tabla_m['unidades'].sum()*100).round(1).astype(str)+'%'
                if 'fob_prom' in mapa_df.columns:
                    tabla_m['FOB Prom'] = mapa_df['fob_prom'].apply(
                        lambda x: f"US$ {x:,.0f}" if pd.notna(x) else "N/A")
                tabla_m.columns = (['País','Unidades','Top Marcas','% Share']
                                   + (['FOB Prom'] if 'fob_prom' in mapa_df.columns else []))
                st.dataframe(fmt_tabla(tabla_m), hide_index=True, use_container_width=True)

                if len(mapa_df) >= 2:
                    st.divider()
                    i1,i2,i3 = st.columns(3)
                    p1, p2 = mapa_df.iloc[0], mapa_df.iloc[1]
                    conc = mapa_df.head(3)['unidades'].sum()/mapa_df['unidades'].sum()*100
                    with i1:
                        st.markdown(f"""<div class="insight-card insight-info">
                        <div class="insight-title">🌍 Principal Origen</div>
                        <div class="insight-text"><b>{p1['_origen']}</b> lidera con {p1['unidades']:,} uds
                        ({p1['unidades']/mapa_df['unidades'].sum()*100:.1f}%)<br>
                        Top: {p1['marcas']}</div></div>""", unsafe_allow_html=True)
                    with i2:
                        st.markdown(f"""<div class="insight-card insight-warning">
                        <div class="insight-title">🥈 Segundo Origen</div>
                        <div class="insight-text"><b>{p2['_origen']}</b>: {p2['unidades']:,} uds.
                        Brecha: {p1['unidades']-p2['unidades']:,} uds.</div></div>""",
                        unsafe_allow_html=True)
                    with i3:
                        st.markdown(f"""<div class="insight-card insight-positive">
                        <div class="insight-title">📊 Concentración</div>
                        <div class="insight-text">{len(mapa_df)} países · Top 3 concentra
                        <b>{conc:.1f}%</b></div></div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# COBERTURA AAP — promovida de checkbox de QA interno a sección de negocio
# real dentro de "⚠️ Riesgos" (rediseño Entrega 2): los huecos de cobertura
# por importador (Zapler, INTERNATIONAL, FREIGHTLINER, DONGFENG) son
# exactamente lo que gerencia pidió poder ver sin activar nada a mano.
# ══════════════════════════════════════════════════════════════════════════════
def render_auditoria():
    st.markdown("### 📊 Cobertura Veritrade vs. Mercado AAP")
    st.caption("Fuente AAP: Asociación Automotriz del Perú · Camiones nuevos importados")

    _aap_path = Path(__file__).parent.parent / 'data' / 'gold' / 'aap_camiones.parquet'

    if not _aap_path.exists():
        st.warning("No se encontró data/gold/aap_camiones.parquet. "
                   "Ejecuta: python pipeline/aap.py")
    else:
        @st.cache_data(ttl=3600)
        def _cargar_aap():
            return pd.read_parquet(_aap_path)

        aap_raw = _cargar_aap()

        # Filtrar por año seleccionado en sidebar
        años_aap = sorted(aap_raw["año"].dropna().unique().astype(int))
        año_aap = safe_selectbox("Año AAP", años_aap,
                               index=len(años_aap) - 1, key="año_aap")
        aap = aap_raw[aap_raw["año"] == año_aap].copy()

        meses_disp = sorted(aap["mes_num"].unique().astype(int))
        mes_labels = {1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",
                      7:"Jul",8:"Ago",9:"Set",10:"Oct",11:"Nov",12:"Dic"}
        rango_mes = st.select_slider(
            "Rango de meses",
            options=meses_disp,
            value=(meses_disp[0], meses_disp[-1]),
            format_func=lambda m: mes_labels.get(m, str(m)),
            key="rango_mes_aap",
        )
        aap = aap[aap["mes_num"].between(rango_mes[0], rango_mes[1])]

        # Totales AAP por marca
        aap_marca = (
            aap.groupby("marca_norm", observed=True)["unidades"]
            .sum()
            .reset_index()
            .rename(columns={"marca_norm": "marca", "unidades": "aap_total"})
        )

        # Totales Veritrade por marca (mismo período)
        df_v = df.copy()
        if "año" in df_v.columns and "mes" in df_v.columns:
            df_v = df_v[
                (df_v["año"] == año_aap)
                & (df_v["mes"].between(rango_mes[0], rango_mes[1]))
            ]

        col_marca = next((c for c in ["marca_normalizada", "marca_declarada", "marca"]
                          if c in df_v.columns), None)

        if col_marca:
            vt_marca = (
                df_v.groupby(col_marca, observed=True)
                .size()
                .reset_index(name="vt_total")
                .rename(columns={col_marca: "marca"})
            )
            vt_marca["marca"] = vt_marca["marca"].str.upper().str.strip()
        else:
            vt_marca = pd.DataFrame(columns=["marca", "vt_total"])

        # Merge
        comp = pd.merge(aap_marca, vt_marca, on="marca", how="outer").fillna(0)
        comp["aap_total"] = comp["aap_total"].astype(int)
        comp["vt_total"]  = comp["vt_total"].astype(int)
        aap_safe = comp["aap_total"].astype(float).where(comp["aap_total"] > 0)
        comp["cobertura_pct"] = (comp["vt_total"].astype(float) / aap_safe * 100).round(1)
        comp = comp[comp["aap_total"] > 0].sort_values("aap_total", ascending=False)

        # KPIs globales
        total_aap = int(comp["aap_total"].sum())
        total_vt  = int(comp["vt_total"].sum())
        cob_global = round(total_vt / total_aap * 100, 1) if total_aap else 0

        k1, k2, k3 = st.columns(3)
        k1.metric("Total AAP (mercado)", f"{total_aap:,}")
        k2.metric("Veritrade (registros DUA)", f"{total_vt:,}")
        k3.metric("Cobertura global", f"{cob_global}%",
                  help="% de unidades AAP con registro en Veritrade")

        st.divider()

        # Gráfico comparativo
        top_n = min(15, len(comp))
        comp_top = comp.head(top_n).sort_values("aap_total")

        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(
            y=comp_top["marca"], x=comp_top["aap_total"],
            name="AAP (mercado total)", orientation="h",
            marker_color="#9E9E9E", opacity=0.7,
        ))
        fig_comp.add_trace(go.Bar(
            y=comp_top["marca"], x=comp_top["vt_total"],
            name="Veritrade (DUAs)", orientation="h",
            marker_color="#1565C0",
        ))
        fig_comp.update_layout(
            barmode="overlay",
            title=f"AAP vs Veritrade — Top {top_n} marcas · {año_aap}",
            xaxis_title="Unidades",
            height=max(400, top_n * 32),
            legend=dict(orientation="h", y=1.08),
            margin=dict(l=10, r=20, t=60, b=20),
        )
        st.plotly_chart(fig_comp, use_container_width=True)

        # Tabla detalle con cobertura %
        st.markdown("#### Detalle por marca")
        comp_show = comp.copy()
        comp_show["cobertura_pct"] = comp_show["cobertura_pct"].apply(
            lambda x: f"{x:.1f}%" if pd.notna(x) else "—"
        )
        comp_show = comp_show.rename(columns={
            "marca": "Marca",
            "aap_total": "AAP (uds)",
            "vt_total": "Veritrade (DUAs)",
            "cobertura_pct": "Cobertura %",
        })
        st.dataframe(
            fmt_tabla(comp_show[["Marca", "AAP (uds)", "Veritrade (DUAs)", "Cobertura %"]]),
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            "⚠️ Veritrade registra a nivel DUA (por expediente de importación), "
            "no por unidad individual. La cobertura % puede superar 100% si un DUA "
            "incluye múltiples unidades del mismo modelo."
        )

# ══════════════════════════════════════════════════════════════════════════════
# SECCIONES NUEVAS — las 8 pestañas del reporte de gerencia que sí tienen datos
# hoy (ver guia estructura antes ppt.txt). Reusan df_actual/df_anterior, los
# helpers y las columnas ya normalizadas por cargar() -- no recalculan nada
# desde cero.
# ══════════════════════════════════════════════════════════════════════════════
SEGMENTO_GUIA_MAP = {"TRACTOCAMIÓN": "Tractos", "VOLQUETE": "Volquetes"}

def _bucket_segmento_guia(cat):
    return SEGMENTO_GUIA_MAP.get(cat, "Camiones")

def render_mercado():
    st.markdown("## 🏠 Mercado")
    st.caption(f"Ranking Top {TOP_N} marcas del mercado total, resto agrupado en 'Otros competidores' "
               "(regla del reporte de gerencia).")

    rank_act = vc_reales(df_actual[COL_MARCA])
    rank_ant = vc_reales(df_anterior[COL_MARCA])
    ultimo_mes = df_actual['mes'].max() if not df_actual.empty else None
    uds_ultimo_mes = (vc_reales(df_actual[df_actual['mes'] == ultimo_mes][COL_MARCA])
                       if ultimo_mes is not None else pd.Series(dtype=int))

    top15 = rank_act.sort_values(ascending=False).head(TOP_N)
    total_mercado = int(rank_act.sum())
    resto = total_mercado - int(top15.sum())

    filas = []
    for i, (marca, uds) in enumerate(top15.items(), start=1):
        ant = int(rank_ant.get(marca, 0))
        filas.append({
            'Ranking': str(i), 'Marca': marca,
            'Último Mes': str(int(uds_ultimo_mes.get(marca, 0))),
            'Acumulado': int(uds),
            'Market Share (%)': pct(uds, total_mercado),
            'Var. % vs Año Anterior': calc_var({'a': uds, 'b': ant}, 'a', 'b'),
        })
    if resto > 0:
        filas.append({'Ranking': '—', 'Marca': 'Otros competidores', 'Último Mes': '—',
                       'Acumulado': resto,
                       'Market Share (%)': pct(resto, total_mercado),
                       'Var. % vs Año Anterior': '—'})
    filas.append({'Ranking': '—', 'Marca': 'Total General', 'Último Mes': '—',
                   'Acumulado': total_mercado, 'Market Share (%)': 100.0,
                   'Var. % vs Año Anterior': '—'})
    tabla = pd.DataFrame(filas)

    render_kpi_cards([
        {'titulo': 'Mercado Total', 'valor': f"{total_act:,}", 'subtitulo': 'unidades acumuladas'},
        {'titulo': 'Marca Líder', 'valor': str(top15.index[0]) if not top15.empty else '—',
         'subtitulo': f"{round(top15.iloc[0]/total_mercado*100,1)}% share" if total_mercado and not top15.empty else ''},
        {'titulo': '2do Competidor', 'valor': str(top15.index[1]) if len(top15) > 1 else '—',
         'subtitulo': f"{int(top15.iloc[1]):,} uds" if len(top15) > 1 else ''},
        {'titulo': 'Marcas Activas', 'valor': f"{rank_act.shape[0]:,}", 'subtitulo': 'con al menos 1 unidad'},
    ])
    tabla_dl(tabla, 'mercado_top15', 'mercado_top15')

    if MOSTRAR_GRAFICO:
        st.divider()
        st.markdown("##### 📈 Tendencia mensual histórica")
        tend = df_actual.groupby(['año','mes','mes_nombre']).size().reset_index(name='Unidades')
        tend['Año'] = tend['año'].astype(str)
        meses_ord = [m for m in MESES_NOMBRES if m in tend['mes_nombre'].unique()]
        fig_t = px.line(tend, x='mes_nombre', y='Unidades', color='Año', markers=True,
                        labels={'mes_nombre': 'Mes'},
                        color_discrete_sequence=COLOR_PALETTE)
        fig_t.update_layout(plot_bgcolor='white', height=350,
                            xaxis={'categoryorder':'array','categoryarray':meses_ord})
        st.plotly_chart(fig_t, use_container_width=True)

def render_segmentos():
    st.markdown("## 📊 Mercado por Segmento")
    st.caption("Camiones = resto de carrocerías rígidas (Chasis Cabina, Hormigonera, Grúa, "
               "Cisterna, Furgón, Otros) · Tractos = Tractocamión · Volquetes = Volquete.")

    seg_act = df_actual['categoria_carroceria'].apply(_bucket_segmento_guia).value_counts()
    seg_ant = df_anterior['categoria_carroceria'].apply(_bucket_segmento_guia).value_counts()
    total = int(seg_act.sum())

    filas = []
    for seg in ['Camiones', 'Tractos', 'Volquetes']:
        act = int(seg_act.get(seg, 0))
        ant = int(seg_ant.get(seg, 0))
        filas.append({
            'Segmento': seg,
            'Unidades Año Anterior': ant,
            'Unidades Año Actual': act,
            'Participación por Segmento (%)': pct(act, total),
            'Crecimiento Absoluto': act - ant,
        })
    tabla = pd.DataFrame(filas)

    render_kpi_cards([{'titulo': seg, 'valor': f"{int(seg_act.get(seg,0)):,}", 'subtitulo': 'unidades'}
                      for seg in ['Camiones','Tractos','Volquetes']]
                      + [{'titulo':'Total','valor':f"{total:,}",'subtitulo':'unidades'}])
    tabla_dl(tabla, 'segmentos_guia', 'mercado_por_segmento')

    if MOSTRAR_GRAFICO:
        fig = px.bar(tabla, x='Segmento', y='Unidades Año Actual', text='Unidades Año Actual',
                    color='Segmento', color_discrete_sequence=COLOR_PALETTE)
        fig.update_layout(plot_bgcolor='white', showlegend=False, height=350)
        _ev_seg = st.plotly_chart(fig, use_container_width=True, on_select="rerun",
                                   selection_mode="points", key="click_segmento")
        _puntos_seg = _ev_seg.selection.points if _ev_seg and _ev_seg.selection else []
        if _puntos_seg:
            _seg_click = _puntos_seg[0].get("x")
            if _seg_click in ['Camiones', 'Tractos', 'Volquetes']:
                st.session_state["segmento_foco"] = _seg_click
        else:
            # Deseleccionar la barra (click de nuevo / click afuera) debe limpiar
            # el foco -- si no, Competidores/Tendencias quedan filtrados por un
            # segmento que el gráfico ya no muestra como seleccionado (rompe-dashboard).
            st.session_state.pop("segmento_foco", None)
        st.caption("💡 Click en una barra para filtrar Competidores/Tendencias por ese segmento "
                   "(drill-down).")

    with st.expander("🔍 Ver detalle completo por carrocería (8 categorías)", expanded=False):
        detalle = vc_reales(df_actual['categoria_carroceria']).reset_index()
        detalle.columns = ['Carrocería','Unidades']
        st.dataframe(fmt_tabla(detalle), hide_index=True, use_container_width=True)

def render_marca_segmento():
    st.markdown("## 🏆 Análisis por Marca y Segmento")
    st.caption(f"Top {TOP_N} marcas del mercado pesado, con su participación dentro de cada segmento.")

    df_seg = df_actual.copy()
    df_seg['_seg_guia'] = df_seg['categoria_carroceria'].apply(_bucket_segmento_guia)
    top10_marcas = vc_reales(df_seg[COL_MARCA]).head(TOP_N).index.tolist()
    totales_seg = df_seg['_seg_guia'].value_counts()

    filas = []
    suma_top = {seg: 0 for seg in ['Camiones','Tractos','Volquetes']}
    for marca in top10_marcas:
        df_m = df_seg[df_seg[COL_MARCA] == marca]
        fila = {'Marca': marca}
        for seg in ['Camiones','Tractos','Volquetes']:
            uds = int((df_m['_seg_guia'] == seg).sum())
            tot_seg = int(totales_seg.get(seg, 0))
            suma_top[seg] += uds
            fila[f'{seg} — Unidades'] = uds
            fila[f'{seg} — % Share'] = pct(uds, tot_seg)
        filas.append(fila)
    tabla = pd.DataFrame(filas)

    # "Otros" -- lo que queda del Top N no cubre, para que Total General sí
    # cierre con la suma de las filas de arriba (mismo criterio que Mercado).
    fila_otros = {'Marca': 'Otros competidores'}
    hay_otros = False
    for seg in ['Camiones','Tractos','Volquetes']:
        tot_seg = int(totales_seg.get(seg, 0))
        resto = tot_seg - suma_top[seg]
        hay_otros = hay_otros or resto > 0
        fila_otros[f'{seg} — Unidades'] = resto
        fila_otros[f'{seg} — % Share'] = pct(resto, tot_seg)
    if hay_otros:
        tabla = pd.concat([tabla, pd.DataFrame([fila_otros])], ignore_index=True)

    fila_total = {'Marca': 'Total General'}
    for seg in ['Camiones','Tractos','Volquetes']:
        fila_total[f'{seg} — Unidades'] = int(totales_seg.get(seg, 0))
        fila_total[f'{seg} — % Share'] = 100.0
    tabla = pd.concat([tabla, pd.DataFrame([fila_total])], ignore_index=True)

    tabla_dl(tabla, 'marca_segmento', 'analisis_marca_segmento')

def render_camiones():
    st.markdown("## 🚚 Camiones Rígidos (Chasis Cabina)")
    st.caption(f"Distinto del bucket 'Camiones' de la sección Segmentos (ese incluye Hormigonera, "
               f"Grúa, Cisterna, Furgón y Otros además de Chasis Cabina) — acá es solo Chasis Cabina. "
               f"Top {TOP_N} modelos comerciales.")
    df_cam = df_actual[df_actual['categoria_carroceria'] == 'CHASIS CABINA']
    if df_cam.empty:
        st.info("Sin registros de Chasis Cabina en el período/filtro seleccionado.")
        return
    total_cam = len(df_cam)
    ultimo_mes = df_cam['mes'].max()

    acumulado = (df_cam.groupby([COL_MARCA, COL_MODELO, 'segmento_peso'], observed=True)
                 .size().reset_index(name='Unidades Acumuladas'))
    ult_mes = (df_cam[df_cam['mes'] == ultimo_mes]
               .groupby([COL_MARCA, COL_MODELO], observed=True)
               .size().reset_index(name='Unidades Último Mes'))
    top = acumulado.merge(ult_mes, on=[COL_MARCA, COL_MODELO], how='left')
    top['Unidades Último Mes'] = top['Unidades Último Mes'].fillna(0).astype(int)
    top = top.sort_values('Unidades Acumuladas', ascending=False).head(TOP_N)
    top['% Share Segmento'] = (top['Unidades Acumuladas']/total_cam*100).round(1)
    top = top.rename(columns={COL_MARCA:'Marca', COL_MODELO:'Modelo', 'segmento_peso':'Configuración/Peso'})
    top = top[['Marca','Modelo','Configuración/Peso','Unidades Último Mes','Unidades Acumuladas','% Share Segmento']]

    modelo_lider = f"{top.iloc[0]['Modelo']} ({top.iloc[0]['Marca']})" if not top.empty else '—'
    render_kpi_cards([
        {'titulo':'Camiones (Chasis Cabina)','valor':f"{total_cam:,}",'subtitulo':'unidades'},
        {'titulo':'Marca Líder','valor':str(df_cam[COL_MARCA].value_counts().idxmax()),'subtitulo':''},
        {'titulo':'Modelo Líder','valor':modelo_lider,'subtitulo':''},
        {'titulo':'Modelos distintos','valor':f"{df_cam[COL_MODELO].nunique():,}",'subtitulo':''},
    ])
    tabla_dl(top, 'top_camiones', 'top_modelos_camiones')

def render_tractos():
    st.markdown("## 🚛 Tractos")
    st.caption(f"Top {TOP_N} marcas líderes en tractocamiones/remolcadores, apertura por tren motriz.")
    df_seg = df_actual[df_actual['categoria_carroceria'] == 'TRACTOCAMIÓN']
    df_seg_ant = df_anterior[df_anterior['categoria_carroceria'] == 'TRACTOCAMIÓN']
    if df_seg.empty:
        st.info("Sin registros de Tractocamión en el período/filtro seleccionado.")
        return
    total_seg = len(df_seg)
    rank = vc_reales(df_seg[COL_MARCA]).head(TOP_N)
    rank_ant = vc_reales(df_seg_ant[COL_MARCA])

    render_kpi_cards([
        {'titulo':'Tractos','valor':f"{total_seg:,}",'subtitulo':'unidades'},
        {'titulo':'Marca Líder','valor':str(rank.index[0]) if not rank.empty else '—',
         'subtitulo':f"{round(rank.iloc[0]/total_seg*100,1)}% share" if not rank.empty else ''},
        {'titulo':f'Marcas en el Top {TOP_N}','valor':f"{len(rank)}",'subtitulo':''},
        {'titulo':'Configuraciones distintas','valor':f"{df_seg['traccion'].nunique()}",'subtitulo':'tren motriz'},
    ])

    filas = [{'Marca': marca, 'Unidades Acumuladas': int(uds),
              '% Share Tractos': round(uds/total_seg*100, 1),
              'Variación vs Año Anterior': calc_var({'a':uds,'b':int(rank_ant.get(marca,0))}, 'a','b')}
             for marca, uds in rank.items()]
    tabla_dl(pd.DataFrame(filas), 'top5_tractos', 'top5_tractos')

    st.markdown("##### Apertura por configuración (tren motriz)")
    for marca in rank.index:
        trac = df_seg[df_seg[COL_MARCA] == marca]['traccion'].value_counts()
        if trac.empty:
            continue
        with st.expander(f"{marca} — {int(rank[marca]):,} uds"):
            tabla_t = trac.reset_index()
            tabla_t.columns = ['Configuración', 'Unidades']
            st.dataframe(fmt_tabla(tabla_t), hide_index=True, use_container_width=True)

def render_volquetes():
    st.markdown("## 🏗️ Volquetes")
    st.caption(f"Top {TOP_N} marcas líderes en volquetes, apertura 6x4 / 8x4.")
    df_seg = df_actual[df_actual['categoria_carroceria'] == 'VOLQUETE']
    if df_seg.empty:
        st.info("Sin registros de Volquete en el período/filtro seleccionado.")
        return
    total_seg = len(df_seg)
    rank = vc_reales(df_seg[COL_MARCA]).head(TOP_N)

    render_kpi_cards([
        {'titulo':'Volquetes','valor':f"{total_seg:,}",'subtitulo':'unidades'},
        {'titulo':'Marca Líder','valor':str(rank.index[0]) if not rank.empty else '—','subtitulo':''},
        {'titulo':'% en 6x4','valor':f"{round((df_seg['traccion']=='6X4').mean()*100,1)}%",'subtitulo':''},
        {'titulo':'% en 8x4','valor':f"{round((df_seg['traccion']=='8X4').mean()*100,1)}%",'subtitulo':''},
    ])

    filas = []
    for marca, uds in rank.items():
        df_m = df_seg[df_seg[COL_MARCA] == marca]
        filas.append({
            'Marca': marca, 'Total Unidades Acumuladas': int(uds),
            '6x4': int((df_m['traccion']=='6X4').sum()),
            '8x4': int((df_m['traccion']=='8X4').sum()),
            '% Market Share Volquetes': round(uds/total_seg*100, 1),
        })
    tabla_dl(pd.DataFrame(filas), 'top5_volquetes', 'top5_volquetes')

def render_origen():
    st.markdown("## 🌍 Volquetes por Origen")
    st.caption("País de manufactura del vehículo, agrupado en macro-regiones, filtrado a Volquetes "
               "(igual criterio que el reporte de gerencia). Para ver todos los vehículos, "
               "usá la sección 'Mapa Origen (todos los vehículos)'.")
    if 'pais_origen' not in df_actual.columns:
        st.warning("No hay columna pais_origen")
        return
    df_vol = df_actual[df_actual['categoria_carroceria'] == 'VOLQUETE'].copy()
    if df_vol.empty:
        st.info("Sin registros de Volquete en el período/filtro seleccionado.")
        return
    df_vol['_pais'] = df_vol['pais_origen'].astype(str).str.upper().str.strip()
    df_vol['_region'] = df_vol['_pais'].map(PAIS_A_REGION).fillna('Otros')
    total_vol = len(df_vol)

    filas = []
    for region in ['China','Europa','Brasil','Japón/Corea','Otros']:
        df_r = df_vol[df_vol['_region'] == region]
        if df_r.empty:
            continue
        marcas_rep = ', '.join(vc_reales(df_r[COL_MARCA]).head(3).index.tolist())
        filas.append({
            'Origen': region, 'Marcas Representativas': marcas_rep,
            'Unidades Acumuladas': len(df_r),
            '% Share de Origen': round(len(df_r)/total_vol*100, 1),
        })
    tabla = pd.DataFrame(filas).sort_values('Unidades Acumuladas', ascending=False)

    render_kpi_cards([
        {'titulo':'Volquetes (total)','valor':f"{total_vol:,}",'subtitulo':'unidades'},
        {'titulo':'Región Líder','valor':str(tabla.iloc[0]['Origen']) if not tabla.empty else '—','subtitulo':''},
        {'titulo':'Regiones activas','valor':f"{len(tabla)}",'subtitulo':''},
        {'titulo':'Países distintos','valor':f"{df_vol['_pais'].nunique()}",'subtitulo':''},
    ])
    tabla_dl(tabla, 'volquetes_origen', 'volquetes_por_origen')

    if MOSTRAR_GRAFICO and not tabla.empty:
        fig = px.pie(tabla, values='Unidades Acumuladas', names='Origen', hole=0.4,
                    color_discrete_sequence=COLOR_PALETTE)
        st.plotly_chart(fig, use_container_width=True)

def render_combustible():
    st.markdown("## ⛽ Comparativo por Tipo de Combustible")
    st.caption("Período actual vs período anterior (mismo filtro de fechas de todo el dashboard).")
    if 'combustible_norm' not in df_actual.columns:
        st.warning("No hay columna combustible_norm")
        return
    CATS_GUIA = ['DIESEL', 'GNV', 'HÍBRIDO', 'ELÉCTRICO']
    comb_act = df_actual['combustible_norm'].value_counts()
    comb_ant = df_anterior['combustible_norm'].value_counts()
    tot_act = int(comb_act.sum())
    tot_ant = int(comb_ant.sum())

    filas = []
    for cat in CATS_GUIA:
        act = int(comb_act.get(cat, 0))
        ant = int(comb_ant.get(cat, 0))
        pct_act = pct(act, tot_act)
        pct_ant = pct(ant, tot_ant)
        filas.append({
            'Tecnología': cat.title() if cat not in ('GNV',) else cat,
            '% Participación Periodo Anterior': pct_ant,
            '% Participación Periodo Actual': pct_act,
            'Unidades Reales Período Actual': act,
            'Desplazamiento (pp)': round(pct_act - pct_ant, 1),
        })
    tabla = pd.DataFrame(filas)

    render_kpi_cards([
        {'titulo':'Diesel','valor':f"{tabla.iloc[0]['% Participación Periodo Actual']}%",'subtitulo':'del período actual'},
        {'titulo':'GNV','valor':f"{tabla.iloc[1]['% Participación Periodo Actual']}%",'subtitulo':''},
        {'titulo':'Híbrido + Eléctrico',
         'valor':f"{round(tabla.iloc[2]['% Participación Periodo Actual']+tabla.iloc[3]['% Participación Periodo Actual'],1)}%",
         'subtitulo':'transición energética'},
        {'titulo':'Total unidades','valor':f"{tot_act:,}",'subtitulo':''},
    ])
    tabla_dl(tabla, 'combustible_comparativo', 'comparativo_combustible')

    if MOSTRAR_GRAFICO:
        fig = px.bar(tabla, x='Tecnología',
                    y=['% Participación Periodo Anterior','% Participación Periodo Actual'],
                    barmode='group', color_discrete_sequence=['#9E9E9E', COLOR_SINOTRUK])
        fig.update_layout(plot_bgcolor='white', height=350)
        st.plotly_chart(fig, use_container_width=True)

def render_resumen_ejecutivo(alertas_continuidad: pd.DataFrame):
    """Portada del informe: semáforo de negocio + insights + Top N marcas + mix
    de segmento + teaser de Riesgos. Reusa agregados livianos (no toca
    render_mercado/render_segmentos)."""
    # FIX: en Modo Sinotruk, df_actual/df_anterior quedan reducidos a una
    # sola marca -- calcular "líder"/"Competencia" contra ese subset hacía
    # que la propia Sinotruk se comparara consigo misma ("Competencia:
    # SINOTRUK +0.0pp"). Se usa el snapshot de mercado total en su lugar.
    df_comp_act = df_mercado_actual if es_sinotruk else df_actual
    df_comp_ant = df_mercado_anterior if es_sinotruk else df_anterior

    rank_act_sem = vc_reales(df_comp_act[COL_MARCA])
    total_mercado_sem = int(rank_act_sem.sum())
    lider = rank_act_sem.sort_values(ascending=False).index[0] if not rank_act_sem.empty else None

    if var_pct is None:
        estado_mercado, txt_mercado = "⚪", "sin histórico"
    elif var_pct > 5:
        estado_mercado, txt_mercado = "🟢", f"{var_pct:+.1f}% YoY"
    elif var_pct >= -5:
        estado_mercado, txt_mercado = "🟡", f"{var_pct:+.1f}% YoY"
    else:
        estado_mercado, txt_mercado = "🔴", f"{var_pct:+.1f}% YoY"

    if lider:
        ms_lider_act = pct(int(rank_act_sem.get(lider, 0)), total_mercado_sem)
        rank_ant_sem = vc_reales(df_comp_ant[COL_MARCA])
        total_mercado_ant_sem = int(rank_ant_sem.sum())
        ms_lider_ant = pct(int(rank_ant_sem.get(lider, 0)), total_mercado_ant_sem)
        delta_lider = round(ms_lider_act - ms_lider_ant, 1)
        if delta_lider >= 0:
            estado_comp = "🟢"
        elif delta_lider >= -2:
            estado_comp = "🟡"
        else:
            estado_comp = "🔴"
        txt_comp = f"{lider} {delta_lider:+.1f}pp"
    else:
        estado_comp, txt_comp = "⚪", "sin datos"

    # FIX: calcular_estado_sinotruk() espera un df CON todas las marcas para
    # medir el share de Sinotruk dentro del total -- pasarle df_actual ya
    # filtrado a Sinotruk (como hacía antes en Modo Sinotruk) daba ~100%
    # share siempre, no el share real de mercado.
    _est_sin = calcular_estado_sinotruk(df_comp_act, df_comp_ant, len(df_comp_act), len(df_comp_ant))

    cs1, cs2, cs3 = st.columns(3)
    cs1.metric(f"{estado_mercado} Mercado", txt_mercado)
    cs2.metric(f"{estado_comp} Competencia", txt_comp, help=f"Marca líder: {lider or '—'}")
    cs3.metric(f"{_est_sin['estado']} Sinotruk (share)", f"{_est_sin['delta_ms']:+.1f}pp",
               help=f"MS actual {_est_sin['ms_act']:.1f}% (objetivo {_est_sin['objetivo_ms']:.0f}%)")

    if ins:
        cols_i = st.columns(min(len(ins), 4))
        for i, item in enumerate(ins):
            with cols_i[i % 4]:
                st.markdown(f"""
                <div class="insight-card insight-{item['tipo']}">
                  <div class="insight-title">{item['titulo']}</div>
                  <div class="insight-text">{item['texto']}</div>
                </div>""", unsafe_allow_html=True)

    bullets_marca = insights_por_marca(df_actual, df_anterior)
    if bullets_marca:
        st.markdown("###### 📌 Hallazgos del período")
        for b in bullets_marca:
            st.markdown(f"- {b}")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    rank_act = rank_act_sem
    total_mercado = total_mercado_sem

    seg_act = df_actual['categoria_carroceria'].apply(_bucket_segmento_guia).value_counts()
    total_seg = int(seg_act.sum())

    c1, c2 = st.columns(2)
    with c1:
        top_hdr, top_sel = st.columns([2, 2])
        with top_sel:
            top_resumen = st.radio("Top", [5, 10, 15, 20], index=1, horizontal=True,
                                   key="top_resumen_ejecutivo", label_visibility="collapsed")
        with top_hdr:
            st.markdown(f"##### 👑 Top {top_resumen} marcas")
        topN_resumen = rank_act.sort_values(ascending=False).head(top_resumen)
        filas_topN = [
            {'Marca': m, 'Unidades': int(u), 'Share (%)': pct(u, total_mercado)}
            for m, u in topN_resumen.items()
        ]
        # FIX: "Regla del Top Desplazable" (guia estructura antes ppt.txt) --
        # toda tabla Top N de un informe gerencial cierra con "Otros"/"Total
        # General"; a esta portada le faltaba, a diferencia de "🏠 Mercado".
        resto_resumen = total_mercado - int(topN_resumen.sum())
        if resto_resumen > 0:
            filas_topN.append({'Marca': 'Otros competidores', 'Unidades': resto_resumen,
                               'Share (%)': pct(resto_resumen, total_mercado)})
        filas_topN.append({'Marca': 'Total General', 'Unidades': total_mercado, 'Share (%)': 100.0})
        tabla_topN = pd.DataFrame(filas_topN)
        st.dataframe(fmt_tabla(tabla_topN), hide_index=True, use_container_width=True)
    with c2:
        st.markdown("##### 📊 Mercado por segmento")
        if MOSTRAR_GRAFICO and total_seg:
            fig = px.pie(names=['Camiones', 'Tractos', 'Volquetes'],
                        values=[int(seg_act.get(s, 0)) for s in ['Camiones', 'Tractos', 'Volquetes']],
                        hole=0.5, color_discrete_sequence=COLOR_PALETTE)
            fig.update_layout(height=280, margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            for s in ['Camiones', 'Tractos', 'Volquetes']:
                st.caption(f"{s}: {int(seg_act.get(s, 0)):,} uds")

    n_nuevas = int((alertas_continuidad['categoria'] == 'nuevo').sum()) if not alertas_continuidad.empty else 0
    if n_nuevas:
        st.warning(f"⚠️ {n_nuevas} alerta(s) nueva(s) de continuidad por importador — ver sección "
                   f"'⚠️ Riesgos' más abajo.")
    else:
        st.caption("✅ Sin alertas nuevas de continuidad por importador en el período más reciente "
                   "disponible — ver detalle en '⚠️ Riesgos'.")


def render_riesgos(alertas_continuidad: pd.DataFrame):
    _periodo = obtener_periodo_riesgos()
    if _periodo:
        _anio_r, _mes_r = _periodo
        st.info(f"📅 Analizando: Ene–{MESES_NOMBRES[_mes_r - 1]} {_anio_r} — "
                f"**independiente** del filtro de fechas de arriba (Continuidad, "
                f"Conflictos de exclusión y Embudo siempre miran el último período "
                f"disponible en camiones.parquet).")

    conflictos = obtener_conflictos_exclusion()
    embudo = obtener_embudo_importador()
    nuevas = alertas_continuidad[alertas_continuidad['categoria'] == 'nuevo'] \
        if not alertas_continuidad.empty else alertas_continuidad

    c1, c2, c3 = st.columns(3)
    with c1:
        n = len(nuevas)
        st.metric(f"{'🔴' if n else '🟢'} Continuidad", f"{n}", "alerta(s) nueva(s)")
    with c2:
        n = len(conflictos)
        st.metric(f"{'🟡' if n else '🟢'} Conflictos de exclusión", f"{n}", "término(s)")
    with c3:
        st.metric("📊 Auditoría", "ver abajo", "cobertura vs AAP")

    render_auditoria()
    st.divider()

    with st.expander("🔁 Continuidad por importador (ceros sospechosos)", expanded=False):
        if alertas_continuidad.empty:
            st.info("Sin ceros sospechosos en el período más reciente.")
        else:
            tabla_dl(alertas_continuidad, 'riesgos_continuidad', 'continuidad_importador')

    with st.expander("⚠️ Conflictos de exclusión (término genérico tapa partida legítima)", expanded=False):
        if not hay_qa_silver():
            st.caption("No disponible en este entorno — requiere data/silver/*_qa.xlsx, "
                       "no versionado en git.")
        elif conflictos.empty:
            st.info("Sin conflictos detectados.")
        else:
            st.caption("Ojo: esto NO significa que sean bugs — solo candidatos a revisar.")
            tabla_dl(conflictos, 'riesgos_conflictos', 'conflictos_exclusion')

    with st.expander("🔻 Embudo por importador (bronze → gold)", expanded=False):
        if not hay_qa_silver():
            st.caption("La columna 'excluidas_silver' no está disponible en este entorno "
                       "(requiere data/silver/*_qa.xlsx, no versionado en git) — puede mostrar 0 "
                       "sin que signifique que nada se excluyó en esa etapa.")
        if embudo.empty:
            st.info("Sin datos de embudo disponibles.")
        else:
            tabla_dl(embudo, 'riesgos_embudo', 'embudo_importador')


# ── PANEL LATERAL — Hallazgos clave (sidebar reactivado a propósito, liz-z26.6:
# revierte la decisión previa de ocultarlo, solo para este panel de solo lectura;
# los filtros de fecha/vista siguen arriba, sin moverse) ────────────────────────
with st.sidebar:
    st.markdown("### 📌 Hallazgos clave")
    st.caption("Se actualiza según los filtros elegidos arriba.")
    if ins:
        for _item in ins:
            st.markdown(f"**{_item['titulo']}**")
            st.caption(_item['texto'])
    for _b in insights_por_marca(df_actual, df_anterior, top_n=3):
        st.markdown(f"- {_b}")


# ══════════════════════════════════════════════════════════════════════════════
# INFORME EJECUTIVO — solo Resumen Ejecutivo + el ranking de Mercado quedan
# siempre visibles (como portada de un informe); Mercado en Detalle, Comparar
# Marcas, Competidores, Tendencias y Riesgos se abren bajo demanda para reducir
# carga cognitiva, en vez de navegación por tabs/sidebar (rediseño Entrega 2,
# Ronda 2 -- liz-z26.1 corrigió la densidad excesiva de la Ronda 1: antes había
# 7 secciones seguidas siempre visibles antes del primer expander).
# ══════════════════════════════════════════════════════════════════════════════
if es_sinotruk:
    st.info("🟡 Estás en modo Sinotruk: todo lo de abajo queda reducido a esa sola marca "
            "(100% share). Para el detalle real de importadores, Withmory y evolución de "
            "market share, abrí '🏆 Competidores' más abajo.")

_alertas_continuidad = obtener_alertas_continuidad(("SINOTRUK",) if es_sinotruk else None)

st.markdown("## 🧭 Resumen Ejecutivo")
render_resumen_ejecutivo(_alertas_continuidad)
st.divider()

render_mercado()
st.divider()

_n_nuevas = int((_alertas_continuidad['categoria'] == 'nuevo').sum()) if not _alertas_continuidad.empty else 0
_badge_riesgos = f" ({_n_nuevas} nueva(s))" if _n_nuevas else ""

with st.expander("📦 Mercado en Detalle (Segmentos, Marca x Segmento, Combustible, Origen)", expanded=False):
    for _fn in [render_segmentos, render_marca_segmento, render_combustible]:
        _fn()
        st.divider()
    render_mapa_origen()
    st.divider()
    render_origen()

with st.expander("⚔️ Comparar Marcas", expanded=False):
    render_comparador_marcas()

# ── DRILL-DOWN (liz-z26.10): click en una barra de render_segmentos() guarda
# session_state["segmento_foco"] -- filtra Competidores/Tendencias por ese
# segmento (misma taxonomía _bucket_segmento_guia/SEGMENTO_GUIA_MAP que usa
# render_segmentos, para que el foco sea exactamente lo que el usuario vio).
# Riesgos NO se filtra: es auditoría de datos, no un corte de negocio. ─────────
_segmento_foco = st.session_state.get("segmento_foco")
_df_actual_full, _df_anterior_full = df_actual, df_anterior
_total_act_full, _total_ant_full = total_act, total_ant

if _segmento_foco:
    _m_foco_act = df_actual['categoria_carroceria'].apply(_bucket_segmento_guia) == _segmento_foco
    _m_foco_ant = df_anterior['categoria_carroceria'].apply(_bucket_segmento_guia) == _segmento_foco
    df_actual = df_actual[_m_foco_act]
    df_anterior = df_anterior[_m_foco_ant]
    total_act = len(df_actual)
    total_ant = len(df_anterior)
    if total_act == 0:
        st.warning(f"🔎 Foco '{_segmento_foco}' no tiene datos con los filtros actuales — se quitó "
                   f"automáticamente.")
        st.session_state.pop("segmento_foco", None)
        df_actual, df_anterior = _df_actual_full, _df_anterior_full
        total_act, total_ant = _total_act_full, _total_ant_full
        _segmento_foco = None
    else:
        _col_foco, _btn_foco = st.columns([5, 1])
        with _col_foco:
            st.info(f"🔎 Foco activo: **{_segmento_foco}** — Competidores y Tendencias de abajo "
                    f"muestran solo este segmento ({total_act:,} uds).")
        with _btn_foco:
            if st.button("✕ Quitar filtro", key="quitar_foco_segmento"):
                del st.session_state["segmento_foco"]
                st.rerun()

with st.expander("🏆 Competidores", expanded=False):
    render_camiones()
    st.divider()
    render_tractos()
    st.divider()
    render_volquetes()
    st.divider()
    render_competencia()
    st.divider()
    render_sinotruk()

with st.expander("📈 Tendencias", expanded=False):
    render_market_share_detalle()

# Restaurar el universo completo antes de Riesgos (no se filtra por segmento).
df_actual, df_anterior = _df_actual_full, _df_anterior_full
total_act, total_ant = _total_act_full, _total_ant_full

with st.expander(f"⚠️ Riesgos{_badge_riesgos}", expanded=False):
    render_riesgos(_alertas_continuidad)

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.divider()
f_d = datetime.fromtimestamp(ULTIMA_ACT).strftime('%d/%m/%Y %H:%M') if ULTIMA_ACT else "—"
st.caption(f"Dashboard Camiones v2.0 · {len(df):,} registros · Veritrade · {f_d}")