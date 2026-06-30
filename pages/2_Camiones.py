"""
dashboard_camiones_v2.py — Dashboard Importaciones Camiones Perú
Uso: streamlit run dashboard_camiones_v2.py
"""
import warnings; warnings.filterwarnings("ignore")
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from calendar import monthrange
from pathlib import Path
import io, re

# ── CONFIG ────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Importaciones de Camiones - Dashboard",
                   page_icon="🚛", layout="wide",
                   initial_sidebar_state="collapsed")

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
SINOTRUK_KW      = ["SINOTRUK","HOWO","SITRAK","SINOTRUCK","WANGPAI","HONAN","HOMAN"]

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

MAPEO_COLS = {
    'marca_norm':          ['marca_norm','marca_normalizada','marca_declarada'],
    'modelo':              ['modelo_match','modelo','modelo_norm'],
    'categoria_maquinaria':['categoria_maquinaria','carroceria_normalizada','carroceria'],
    'grupo_importador':    ['grupo_importador','importador_grupo','importador'],
    'valor_fob':           ['valor_fob','fob','fob_usd'],
    'valor_cif':           ['valor_cif','cif','cif_usd'],
    'pb':                  ['peso_bruto_desc','kg_bruto_col','kg_bruto'],
}

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""<style>
.block-container{padding:0.5rem 1.5rem!important;max-width:100%!important;}
.main{background-color:#F5F5F5;}
[data-testid="stSidebar"],[data-testid="collapsedControl"]{display:none;}
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
  background:linear-gradient(90deg,#2D2D2D 0%,#1A1A1A 100%);color:white;
  padding:10px 15px;border-radius:8px;margin-bottom:15px;
  box-shadow:0 2px 8px rgba(0,0,0,0.2);border:1px solid #333;}
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
.stTabs [data-baseweb="tab-list"]{gap:8px;background-color:#FFFFFF;
  padding:10px;border-radius:8px;border:1px solid #E0E0E0;}
.stTabs [data-baseweb="tab"]{background-color:#F5F5F5;border-radius:6px;
  padding:8px 16px;color:#1A1A1A;font-weight:600;}
.stTabs [aria-selected="true"]{
  background:linear-gradient(135deg,#1A1A1A,#2D2D2D)!important;
  color:#FFFFFF!important;}
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
    if not v or v in ("NAN","NONE",""): return "OTROS"
    if any(k in v for k in ["TRACTO","REMOLCADOR","CABEZAL","TRACTOREMOLCADOR"]):
        return "TRACTOCAMIÓN"
    if any(k in v for k in ["VOLQUETE","VOLQUETA","DUMPER","TOLVA"]):
        return "VOLQUETE"
    if any(k in v for k in ["CHASIS CAB","CHASIS MOT","CHASIS MOTORIZ"]):
        return "CHASIS CABINA"
    if "CHASIS" in v and "CABINA" in v:  return "CHASIS CABINA"
    if "CABINADO" in v:                  return "CHASIS CABINA"
    if "HORMIGON" in v or "MEZCLAD" in v or "MIXER" in v: return "HORMIGONERA"
    if "GRÚA" in v or "GRUA" in v or "AUXILIO MECANIC" in v: return "GRÚA"
    if "CISTERNA" in v or "TANQUE" in v: return "CISTERNA"
    if "FURGON" in v or "FURGÓN" in v:  return "FURGÓN"
    if v.startswith("CHASIS"):           return "CHASIS CABINA"
    # COMPACTADOR, BARREDERA, MINIBUS, EXPLOSIVOS, PICK UP → OTROS
    return "OTROS"

def clasificar_segmento(pb) -> str:
    """Clasifica por Peso Bruto Vehicular (kg) según rangos Withmory."""
    try:
        pb = float(pb)
    except (TypeError, ValueError):
        return "SIN DATO"
    if pb <= 0:     return "SIN DATO"
    if pb <= 6000:  return "LDT 1"
    if pb <= 10000: return "LDT 2"
    if pb <= 15000: return "MDT 1"
    if pb <= 17000: return "MDT 2"
    if pb <= 25000: return "MDT 3"
    if pb <= 33000: return "SEMI PESADO"
    return "PESADO"

def normalizar_combustible(val):
    v = str(val).upper()
    if "GNL" in v:                      return "GNL"
    if "GNV" in v or "GAS NAT" in v:    return "GNV"
    if "ELECT" in v:                    return "ELÉCTRICO"
    if "GASOL" in v:                    return "GASOLINA"
    if "DIESEL" in v or "PETROL" in v:  return "DIESEL"
    if "HIBRID" in v:                   return "HÍBRIDO"
    return "OTRO"

def calc_var(row, col_act, col_ant):
    ant, act = row[col_ant], row[col_act]
    if ant == 0: return "+100%" if act > 0 else "0%"
    return f"{((act-ant)/ant*100):+.1f}%"

def destacar_sinotruk(row):
    for col in [COL_MARCA,'Marca','Actor Comercial']:
        if col in row.index and row[col] == MARCA_PROPIA:
            return ['background-color:#FFF8E1;font-weight:bold;']*len(row)
    return ['']*len(row)

def descargar_csv(df):
    return df.to_csv(index=False).encode('utf-8')

@st.cache_data
def excel_bytes(df_tuple, hoja="Datos"):
    df = pd.DataFrame(df_tuple)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as w:
        df.to_excel(w, sheet_name=hoja, index=False)
    return buf.getvalue()

def render_bloque(titulo, fig, df_tabla, key, nombre="datos"):
    raw = df_tabla.data if hasattr(df_tabla,'data') else df_tabla
    c1, c2 = st.columns([6,1])
    with c1:
        if titulo:
            st.markdown(f'<div class="section-header"><p class="section-title-text">{titulo}</p></div>',
                        unsafe_allow_html=True)
    with c2:
        with st.popover("📥", use_container_width=True):
            cx, cy = st.columns(2)
            with cx:
                try: st.download_button("xlsx", excel_bytes(tuple(raw.itertuples(index=False)), nombre[:30]),
                                        f"{nombre}.xlsx", key=f"xl_{key}", use_container_width=True)
                except: pass
            with cy:
                try: st.download_button("csv", descargar_csv(raw), f"{nombre}.csv",
                                        key=f"csv_{key}", use_container_width=True)
                except: pass
    if fig:
        st.plotly_chart(fig, use_container_width=True,
                        config={'displayModeBar':True,'displaylogo':False})
    with st.expander("📊 Ver tabla", expanded=False):
        st.dataframe(df_tabla, hide_index=True, use_container_width=True)

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
        # Familia completa Sinotruk (mismo criterio que el tab)
        mask_sin_act = df_act[COL_MARCA].astype(str).str.upper().str.contains(
            "|".join(SINOTRUK_KW), na=False)
        mask_sin_ant = df_ant[COL_MARCA].astype(str).str.upper().str.contains(
            "|".join(SINOTRUK_KW), na=False) if COL_MARCA in df_ant.columns else pd.Series(False)
        if 'submarca_sinotruk' in df_act.columns:
            mask_sin_act = mask_sin_act | (df_act['submarca_sinotruk'].notna() &
                                           (df_act['submarca_sinotruk'].str.strip()!=""))
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

# ── CARGA ─────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def cargar():
    ruta_parquet = Path(__file__).parent.parent / 'data' / 'gold' / 'camiones.parquet'
    if ruta_parquet.exists():
        df = pd.read_parquet(ruta_parquet)
        ultima = ruta_parquet.stat().st_mtime
    else:
        ruta = Path(__file__).parent.parent / 'data' / 'silver'
        if not ruta.exists(): ruta = Path('.')
        archivos = sorted(ruta.glob('*_fase1.xlsx'))
        if not archivos: return pd.DataFrame(), None

        frames, ultima = [], 0
        for f in archivos:
            try:
                d = pd.read_excel(f, sheet_name='estructurado', dtype=str)
                frames.append(d)
                ultima = max(ultima, f.stat().st_mtime)
            except: pass
        if not frames: return pd.DataFrame(), None
        df = pd.concat(frames, ignore_index=True)
    if 'dua_dam' in df.columns:
        df['_k'] = df.apply(lambda r: f"{r.get('dua_dam','')}|{r.get('vin') or r.get('chasis') or ''}", axis=1)
        df = df.drop_duplicates('_k').drop(columns='_k')

    if 'fecha_dua' in df.columns:
        df['fecha'] = pd.to_datetime(df['fecha_dua'], errors='coerce')
        df['año']   = df['fecha'].dt.year.astype('Int64')
        df['mes']   = df['fecha'].dt.month.astype('Int64')
        df['mes_nombre'] = df['mes'].map({i+1:m for i,m in enumerate(MESES_NOMBRES)})

    df = normalizar_columnas(df, MAPEO_COLS)
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()]

    for col in ['categoria_maquinaria','marca_norm','grupo_importador']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.upper().str.strip()
            df[col] = df[col].replace(['NAN','NONE','NULL','',' '], pd.NA)

    if 'categoria_maquinaria' in df.columns:
        df['categoria_maquinaria'] = df['categoria_maquinaria'].apply(normalizar_carroceria)
    if 'combustible' in df.columns:
        df['combustible_norm'] = df['combustible'].apply(normalizar_combustible)
    if 'traccion' in df.columns:
        df['traccion'] = df['traccion'].astype(str).str.upper().str.strip().fillna('N/D')

    # ── Peso bruto y segmento ─────────────────────────────────────────────────
    if 'pb' in df.columns:
        df['pb'] = pd.to_numeric(df['pb'], errors='coerce')
    else:
        df['pb'] = pd.NA
    df['segmento_peso'] = df['pb'].apply(clasificar_segmento)

    for c in ['valor_fob','valor_cif','fob_usd','cif_usd']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

    # ── Año como int nativo (evita bugs de tipo en comparaciones) ────────────
    if 'año' in df.columns:
        df['año'] = df['año'].apply(lambda x: int(x) if pd.notna(x) else pd.NA).astype('Int64')

    for col in ['categoria_maquinaria','marca_norm','grupo_importador']:
        if col in df.columns: df[col] = df[col].astype('category')

    return df, ultima

df, ULTIMA_ACT = cargar()
if df is None or df.empty:
    st.error("No se encontraron archivos *_fase1.xlsx en outputs/"); st.stop()

COL_MARCA = 'marca_norm' if 'marca_norm' in df.columns else 'marca'
COL_MODELO= 'modelo'
COL_FOB   = 'valor_fob' if 'valor_fob' in df.columns else None
COL_CIF   = 'valor_cif' if 'valor_cif' in df.columns else None

# ── HEADER ────────────────────────────────────────────────────────────────────
# FIX CRÍTICO: años como int nativo (evita numpy.float64 en monthrange)
años_disp = sorted([int(a) for a in df['año'].dropna().unique()])
cats_disp = sorted([c for c in df['categoria_maquinaria'].dropna().unique()
                    if c in CAT_REQUERIDAS])

st.markdown('<div style="padding-top:8px"></div>', unsafe_allow_html=True)
col_titulo, col_desde, col_hasta, col_btn = st.columns([2.8, 0.9, 0.9, 0.4])

with col_desde:
    st.markdown('<div style="font-size:0.6rem;color:#888;font-weight:700;margin-bottom:2px;">📅 Desde</div>',
                unsafe_allow_html=True)
    c1, c2 = st.columns([1,1.1], gap="small")
    with c1: mes_ini = st.selectbox("Mi", MESES_NOMBRES, index=0, label_visibility="collapsed", key="mes_ini")
    with c2: año_ini = st.selectbox("Ai", años_disp, index=0, label_visibility="collapsed", key="año_ini")

with col_hasta:
    st.markdown('<div style="font-size:0.6rem;color:#888;font-weight:700;margin-bottom:2px;">📅 Hasta</div>',
                unsafe_allow_html=True)
    c3, c4 = st.columns([1,1.1], gap="small")
    with c3: mes_fin = st.selectbox("Mf", MESES_NOMBRES, index=len(MESES_NOMBRES)-1, label_visibility="collapsed", key="mes_fin")
    with c4: año_fin = st.selectbox("Af", años_disp, index=len(años_disp)-1, label_visibility="collapsed", key="año_fin")

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
        st.cache_data.clear(); st.rerun()

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

df_actual   = df[(df['fecha']>=f_ini)   & (df['fecha']<=f_fin)]
df_anterior = df[(df['fecha']>=f_ini_a) & (df['fecha']<=f_fin_a)]

# Filtro Sinotruk si aplica
es_sinotruk = "Sinotruk" in vista
if es_sinotruk:
    def mask_sin(d):
        m = d[COL_MARCA].astype(str).str.upper().str.contains("|".join(SINOTRUK_KW), na=False)
        if 'submarca_sinotruk' in d.columns:
            m = m | (d['submarca_sinotruk'].notna() & (d['submarca_sinotruk'].str.strip()!=""))
        return d[m]
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
            df_actual   = df_actual[df_actual['categoria_maquinaria'].isin(cat_sel)]
            df_anterior = df_anterior[df_anterior['categoria_maquinaria'].isin(cat_sel)]

total_act = len(df_actual)
total_ant = len(df_anterior)
var_pct   = (total_act-total_ant)/total_ant*100 if total_ant>0 else None

dias = max((f_fin-f_ini).days+1, 1)
dias_año = 366 if año_fin_int%4==0 else 365
proyeccion = int(total_act*dias_año/dias) if total_act>0 else 0
df_ant_año = df[df['año']==año_fin_int-1]
if cat_sel:
    df_ant_año = df_ant_año[df_ant_año['categoria_maquinaria'].isin(cat_sel)]
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

# ── INSIGHTS ──────────────────────────────────────────────────────────────────
ins = insights_ejecutivos(df_actual, df_anterior, total_act, total_ant)
if ins:
    st.markdown("### 🔍 Resumen Ejecutivo del Período")
    cols_i = st.columns(min(len(ins),4))
    for i, item in enumerate(ins):
        with cols_i[i%4]:
            st.markdown(f"""
            <div class="insight-card insight-{item['tipo']}">
              <div class="insight-title">{item['titulo']}</div>
              <div class="insight-text">{item['texto']}</div>
            </div>""", unsafe_allow_html=True)
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

if df_actual.empty:
    st.warning("⚠️ Sin datos para el período seleccionado."); st.stop()

año_actual = año_fin_int

# ── TABS ──────────────────────────────────────────────────────────────────────
if es_sinotruk:
    tab3, tab1, tab2, tab4, tab5 = st.tabs(["🟡 SINOTRUK / WITHMORY",
                                             "📈 Market Share","🏆 Competencia",
                                             "🗺️ Mapa Origen","📊 Cobertura AAP"])
else:
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Market Share","🏆 Competencia",
                                             "🟡 SINOTRUK / WITHMORY","🗺️ Mapa Origen",
                                             "📊 Cobertura AAP"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — MARKET SHARE
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    tend = df_actual.groupby(['año','mes','mes_nombre']).size().reset_index(name='Unidades')
    tend['Año'] = tend['año'].astype(str)
    meses_ord = [m for m in MESES_NOMBRES if m in tend['mes_nombre'].unique()]
    fig_t = px.line(tend, x='mes_nombre', y='Unidades', color='Año', markers=True,
                    color_discrete_sequence=COLOR_PALETTE, title="Tendencia Mensual Histórica")
    fig_t.update_layout(plot_bgcolor='white', height=420,
                        xaxis={'categoryorder':'array','categoryarray':meses_ord})
    render_bloque("", fig_t, tend, "tend", "tendencia_mensual")
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

        st.markdown("##### 📋 Variación Anual por Segmento")
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
            st.dataframe(pd.DataFrame(resumen_s), hide_index=True, use_container_width=True)

    else:
        st.markdown("##### 📋 Variación Anual por Tipo de Carrocería")
        años_lista = sorted([int(a) for a in df_actual['año'].dropna().unique()])
        resumen = []
        for cat in (cat_sel or cats_disp):
            fila = {'Carrocería': cat}
            prev = None
            for a in años_lista:
                mask = (df_actual['año']==a) & (df_actual['categoria_maquinaria']==cat)
                val = int(mask.sum())
                fila[str(a)] = val
                if prev is not None and prev > 0:
                    fila[f"VAR {a}"] = f"{((val-prev)/prev*100):+.1f}%"
                prev = val
            if any(fila.get(str(a),0)>0 for a in años_lista):
                resumen.append(fila)
        if resumen:
            st.dataframe(pd.DataFrame(resumen), hide_index=True, use_container_width=True)
        elif años_lista:
            st.info(f"Años disponibles: {años_lista}. Verifica los filtros de carrocería.")
    st.divider()

    cl, cr = st.columns(2)
    with cl:
        share = df_actual['categoria_maquinaria'].value_counts().reset_index()
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

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — COMPETENCIA (estilo maquinaria)
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
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
        ev = st.dataframe(rv.style.apply(destacar_sinotruk, axis=1),
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
                                  key=f"tp_{actor}", label_visibility="collapsed")
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
                top_mod = (df_f.groupby([COL_MODELO,'categoria_maquinaria'])
                           .size().reset_index(name='Uds')
                           .sort_values('Uds', ascending=False).head(10))
                top_mod = top_mod.rename(columns={COL_MODELO:'Modelo','categoria_maquinaria':'Carrocería'})
                if col_p and col_p in df_f.columns:
                    fob_m = df_f.groupby(COL_MODELO)[col_p].mean().reset_index()
                    fob_m.columns = [COL_MODELO, f'{nom_p} Prom']
                    fob_m[f'{nom_p} Prom'] = fob_m[f'{nom_p} Prom'].apply(lambda x: f"US$ {x:,.0f}")
                    top_mod = top_mod.merge(fob_m, left_on='Modelo', right_on=COL_MODELO,
                                            how='left').drop(columns=COL_MODELO, errors='ignore')
                st.dataframe(top_mod, hide_index=True, use_container_width=True)

            # Explorar carrocería específica
            with st.expander("🚛 Explorar carrocería específica"):
                carr_data = df_f['categoria_maquinaria'].value_counts().reset_index()
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
                    carr_sel = st.selectbox("Selecciona carrocería:", carrs, key=f"carr_{actor}")
                    if carr_sel != 'TODOS' and COL_MODELO in df_f.columns:
                        df_carr = df_f[df_f['categoria_maquinaria']==carr_sel]
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
                        st.dataframe(mods_carr, hide_index=True, use_container_width=True)

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
                st.dataframe(tbl_wide, hide_index=True, use_container_width=True)

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
                                          title=f"FOB Promedio por Modelo")
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
                            st.dataframe(df_vp, hide_index=True, use_container_width=True)
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
                                          title=f"Evolución de Unidades por Modelo")
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
                            st.dataframe(df_vu, hide_index=True, use_container_width=True)
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
            with ca: a_a = st.selectbox(f"{label_a} A", actores_hh, index=0, key="h2h_a")
            with cb: a_b = st.selectbox(f"{label_a} B", actores_hh,
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
                s_a = u_a/total_act*100; s_b = u_b/total_act*100

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
                    du = u_b-u_a; dp = (p_b-p_a) if p_a and p_b else None
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
                                color_discrete_sequence=COLOR_PALETTE)
                fig_h.update_layout(plot_bgcolor='white', height=230)
                st.plotly_chart(fig_h, use_container_width=True)

                st.markdown("##### 🚛 Comparación por Carrocería")
                años_hh = sorted(set(df_a['año'].dropna().unique()) |
                                 set(df_b['año'].dropna().unique()))
                año_sel = st.selectbox("Año:", [int(a) for a in años_hh],
                                       index=len(años_hh)-1, key="año_hh")
                da_año = df_a[df_a['año']==año_sel]
                db_año = df_b[df_b['año']==año_sel]
                seg_a2 = da_año['categoria_maquinaria'].value_counts().reset_index()
                seg_a2.columns = ['Carrocería', str(a_a)[:15]]
                seg_b2 = db_año['categoria_maquinaria'].value_counts().reset_index()
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
                        ev_s = (df_t.groupby(['año','categoria_maquinaria']).size()
                                .unstack(fill_value=0).reset_index())
                        ev_s.columns = ['Carrocería'] + [str(c) for c in ev_s.columns[1:]]
                        anios_t = [c for c in ev_s.columns if c != 'Carrocería']
                        if len(anios_t)>=2:
                            ev_s['Var%'] = ((ev_s[anios_t[-1]]-ev_s[anios_t[0]])/
                                            ev_s[anios_t[0]]*100).fillna(0).apply(
                                            lambda x: f"{x:+.1f}%")
                        st.dataframe(ev_s, hide_index=True, use_container_width=True)

                # Top modelos del último año
                st.markdown(f"##### 🏗️ Top Modelos — {año_sel}")
                cta2, ctb2 = st.columns(2)
                for col_t, df_t, nom_t in [(cta2, da_año, a_a), (ctb2, db_año, a_b)]:
                    with col_t:
                        st.markdown(f"**{nom_t[:25]}**")
                        if COL_MODELO in df_t.columns:
                            tm = (df_t.groupby([COL_MODELO,'categoria_maquinaria'])
                                  .size().reset_index(name='Uds')
                                  .sort_values('Uds',ascending=False).head(8))
                            tm = tm.rename(columns={COL_MODELO:'Modelo',
                                                     'categoria_maquinaria':'Carrocería'})
                            if col_pc and col_pc in df_t.columns:
                                fob_t = df_t.groupby(COL_MODELO)[col_pc].mean().reset_index()
                                fob_t.columns = [COL_MODELO, f'{nom_pc} Prom']
                                fob_t[f'{nom_pc} Prom'] = fob_t[f'{nom_pc} Prom'].apply(
                                    lambda x: f"US$ {x:,.0f}")
                                tm = tm.merge(fob_t, left_on='Modelo',
                                              right_on=COL_MODELO, how='left').drop(
                                              columns=COL_MODELO, errors='ignore')
                            st.dataframe(tm, hide_index=True, use_container_width=True)

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

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — SINOTRUK / WITHMORY
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    m_sin = df_actual[COL_MARCA].astype(str).str.upper().str.contains("|".join(SINOTRUK_KW), na=False)
    if 'submarca_sinotruk' in df_actual.columns:
        m_sin = m_sin | (df_actual['submarca_sinotruk'].notna() &
                         (df_actual['submarca_sinotruk'].str.strip()!=""))
    df_sin = df_actual[m_sin]

    # Mismo filtro para período anterior
    m_sin_ant = df_anterior[COL_MARCA].astype(str).str.upper().str.contains("|".join(SINOTRUK_KW), na=False)
    if 'submarca_sinotruk' in df_anterior.columns:
        m_sin_ant = m_sin_ant | (df_anterior['submarca_sinotruk'].notna() &
                                 (df_anterior['submarca_sinotruk'].str.strip()!=""))
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
                                          label_visibility="visible")

        # ── Fila KPIs ─────────────────────────────────────────────────────────
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("📦 Unidades", f"{n_sin:,}",
                  delta=f"{n_sin - n_sin_ant:+,} vs ant.")
        c2.metric("📊 Market Share", f"{ms_act:.1f}%",
                  delta=f"{delta_ms:+.1f} pp vs ant.",
                  delta_color="normal")
        c3.metric("🎯 vs Objetivo", f"{ms_act - objetivo_ms:+.1f} pp",
                  delta=f"objetivo: {objetivo_ms:.0f}%",
                  delta_color="off")
        if fob_sin:
            delta_fob = f"US$ {fob_sin - fob_mkt:+,.0f} vs mercado" if fob_mkt else None
            c4.metric("💰 FOB Prom.", f"US$ {fob_sin:,.0f}", delta=delta_fob,
                      delta_color="off")
        else:
            c4.metric("💰 FOB Prom.", "N/A")
        c5.metric("🏢 Withmory", f"{w_n:,}",
                  delta=f"{w_share:.0f}% de familia")

        st.divider()

        # ── Gauge + Cuota mensual ─────────────────────────────────────────────
        col_gauge, col_share_evo = st.columns([1, 2])

        with col_gauge:
            gauge_color = ("#4CAF50" if ms_act >= objetivo_ms
                           else "#FFA500" if ms_act >= objetivo_ms * 0.8
                           else "#FF5252")
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=round(ms_act, 1),
                number=dict(suffix="%", font=dict(size=32, color=gauge_color)),
                delta=dict(reference=objetivo_ms, suffix=" pp vs obj.",
                           increasing=dict(color="#4CAF50"),
                           decreasing=dict(color="#FF5252")),
                gauge=dict(
                    axis=dict(range=[0, max(ms_act * 1.5, objetivo_ms * 1.3)],
                              ticksuffix="%", tickcolor="#666"),
                    bar=dict(color=gauge_color, thickness=0.25),
                    bgcolor="white",
                    borderwidth=1, bordercolor="#DDD",
                    steps=[
                        dict(range=[0, objetivo_ms * 0.8], color="#FFEBEE"),
                        dict(range=[objetivo_ms * 0.8, objetivo_ms], color="#FFF8E1"),
                        dict(range=[objetivo_ms, max(ms_act * 1.5, objetivo_ms * 1.3)], color="#E8F5E9"),
                    ],
                    threshold=dict(line=dict(color="#1A1A1A", width=3),
                                   thickness=0.85, value=objetivo_ms),
                ),
                title=dict(text=f"Market Share<br><span style='font-size:0.8em;color:#888'>Objetivo: {objetivo_ms:.0f}%</span>",
                           font=dict(size=14)),
            ))
            fig_gauge.update_layout(height=260, margin=dict(l=20, r=20, t=40, b=10),
                                    paper_bgcolor="white", font=dict(color="#333"))
            st.plotly_chart(fig_gauge, use_container_width=True)

        with col_share_evo:
            # Cuota mensual % en el dataset completo — últimos 24 meses
            df_full_ms = df.copy()
            df_full_ms = df_full_ms[df_full_ms['fecha'].notna()].copy()
            df_full_ms['_sin'] = df_full_ms[COL_MARCA].astype(str).str.upper().str.contains(
                "|".join(SINOTRUK_KW), na=False)
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

        # ── Cuota vs Top Competidores — barras mensuales apiladas ─────────────
        st.markdown("#### 📈 Cuota mensual vs Top Competidores")
        top_marcas_comp = (df_actual[COL_MARCA].value_counts().head(6).index.tolist())
        if MARCA_PROPIA not in top_marcas_comp:
            top_marcas_comp = [MARCA_PROPIA] + top_marcas_comp[:5]

        df_comp_ms = df.copy()
        df_comp_ms = df_comp_ms[df_comp_ms['fecha'].notna()]
        df_comp_ms['_marca_grp'] = df_comp_ms[COL_MARCA].astype(str).apply(
            lambda m: MARCA_PROPIA if any(k in m.upper() for k in SINOTRUK_KW)
            else m.upper().strip() if m.upper().strip() in top_marcas_comp
            else 'OTROS')
        df_comp_ms = df_comp_ms[df_comp_ms['_marca_grp'] != 'OTROS']
        evo_comp = (df_comp_ms.groupby(['año','mes','mes_nombre','_marca_grp'])
                   .size().reset_index(name='Uds'))
        evo_comp = evo_comp.sort_values(['año','mes']).tail(24 * len(top_marcas_comp))
        evo_comp['periodo'] = evo_comp['mes_nombre'] + " " + evo_comp['año'].astype(str)

        color_comp = {MARCA_PROPIA: COLOR_SINOTRUK}
        pal_rest = [c for c in COLOR_PALETTE if c != COLOR_SINOTRUK]
        for i, m in enumerate([m for m in top_marcas_comp if m != MARCA_PROPIA]):
            color_comp[m] = pal_rest[i % len(pal_rest)]

        fig_comp_evo = px.line(evo_comp, x='periodo', y='Uds', color='_marca_grp',
                               markers=True, color_discrete_map=color_comp,
                               title="Unidades mensuales — Sinotruk vs competencia")
        fig_comp_evo.update_traces(selector=dict(name=MARCA_PROPIA),
                                   line=dict(width=4), marker=dict(size=9))
        fig_comp_evo.update_layout(plot_bgcolor='white', height=320,
                                   xaxis_tickangle=-35,
                                   legend=dict(orientation="h", y=1.08, title_text=""),
                                   yaxis=dict(gridcolor='#F0F0F0'))
        st.plotly_chart(fig_comp_evo, use_container_width=True)

        st.divider()

        # ── Precio FOB comparativo ────────────────────────────────────────────
        if COL_FOB and COL_FOB in df_actual.columns and df_actual[COL_FOB].sum() > 0:
            st.markdown("#### 💰 Precio FOB Promedio vs Competencia")
            fob_comp = (df_actual[df_actual[COL_FOB] > 0]
                        .groupby(COL_MARCA)[COL_FOB]
                        .agg(fob_prom='mean', n='count')
                        .reset_index()
                        .query("n >= 5")
                        .sort_values('fob_prom', ascending=False)
                        .head(12))
            fob_comp['es_sin'] = fob_comp[COL_MARCA].astype(str).str.upper().str.contains(
                "|".join(SINOTRUK_KW), na=False)
            fob_comp['color'] = fob_comp['es_sin'].map({True: COLOR_SINOTRUK, False: '#4A90E2'})
            fob_comp['label'] = fob_comp['fob_prom'].apply(lambda x: f"US$ {x:,.0f}")

            fig_fob = go.Figure(go.Bar(
                y=fob_comp[COL_MARCA],
                x=fob_comp['fob_prom'],
                orientation='h',
                text=fob_comp['label'],
                textposition='outside',
                marker_color=fob_comp['color'].tolist(),
            ))
            if fob_mkt:
                fig_fob.add_vline(x=fob_mkt, line_dash="dot", line_color="#888",
                                  annotation_text=f"Prom. mercado US$ {fob_mkt:,.0f}",
                                  annotation_position="top right")
            fig_fob.update_layout(
                plot_bgcolor='white', height=max(300, len(fob_comp) * 32),
                xaxis=dict(tickprefix="US$ ", tickformat=",.0f", gridcolor='#F0F0F0'),
                yaxis=dict(autorange="reversed"),
                margin=dict(l=10, r=120, t=20, b=10),
                showlegend=False,
            )
            st.plotly_chart(fig_fob, use_container_width=True)
            st.divider()

        # ── Sub-marcas + Importadores ─────────────────────────────────────────
        cl, cr = st.columns(2)
        with cl:
            sub = df_sin['submarca_sinotruk'].fillna(df_sin[COL_MARCA]) \
                  if 'submarca_sinotruk' in df_sin.columns else df_sin[COL_MARCA]
            sub_vc = sub.value_counts().reset_index()
            sub_vc.columns = ['Sub-marca','Unidades']
            fig_sub = px.pie(sub_vc.head(8), values='Unidades', names='Sub-marca', hole=0.4,
                             title="Por sub-marca declarada en aduana",
                             color_discrete_sequence=COLOR_PALETTE)
            st.plotly_chart(fig_sub, use_container_width=True)
        with cr:
            imp_sin = df_sin['grupo_importador'].value_counts().head(10).reset_index()
            imp_sin.columns = ['Importador','Unidades']
            colors_sin = [COLOR_SINOTRUK if 'WITHMORY' in str(x).upper() else '#4A90E2'
                          for x in imp_sin['Importador']]
            fig_imp = px.bar(imp_sin, x='Unidades', y='Importador', orientation='h',
                             text_auto=True, title="Importadores Sinotruk")
            fig_imp.update_traces(marker_color=colors_sin)
            fig_imp.update_layout(plot_bgcolor='white', height=350,
                                  yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_imp, use_container_width=True)

        st.divider()
        st.markdown("#### ★ Marca Declarada en Aduana por Importador")
        st.caption("SINOTRUK = Withmory oficial · HOWO = Andes Motor (mismo fabricante, distinto posicionamiento)")
        cross = (df_sin.groupby(['grupo_importador', COL_MARCA])
                 .size().reset_index(name='unidades')
                 .sort_values(['grupo_importador','unidades'], ascending=[True,False]))
        cross['% imp'] = cross.groupby('grupo_importador')['unidades'].transform(
            lambda x: (x / x.sum() * 100).round(1))
        st.dataframe(cross.rename(columns={'grupo_importador':'Importador',
                                           COL_MARCA:'Marca Declarada','unidades':'Uds'}),
                     hide_index=True, use_container_width=True)

        st.divider()
        carr_sin = df_sin['categoria_maquinaria'].value_counts().reset_index()
        carr_sin.columns = ['Carrocería','Unidades']
        fig_cs = px.bar(carr_sin[carr_sin['Unidades']>0], x='Carrocería', y='Unidades',
                        text_auto=True, color='Unidades',
                        color_continuous_scale=['#333','#F6E421'],
                        title="Sinotruk por tipo de carrocería")
        fig_cs.update_layout(plot_bgcolor='white', coloraxis_showscale=False, height=280)
        st.plotly_chart(fig_cs, use_container_width=True)

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
            st.dataframe(seg_sin, hide_index=True, use_container_width=True)

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

        # Evolución de unidades por dealer (mensual)
        with st.expander("📦 Evolución mensual de unidades por dealer"):
            todos_imp_sin = ['TODOS'] + sorted(df_sin['grupo_importador'].dropna().unique().tolist())
            imp_sel_sin = st.selectbox("Importador:", todos_imp_sin, key="imp_sel_sin")
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
                    st.dataframe(pd.DataFrame(var_sin), hide_index=True,
                                 use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — MAPA DE BURBUJAS (fondo blanco, plano, filtros)
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
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
            cont_sel = st.selectbox("🌍 Continente:", list(CONTINENTES.keys()), key="cont_sel")
        with mc2:
            paises_disp = ["TODOS"] + sorted(mapa_df_full['_origen'].unique().tolist())
            pais_sel = st.selectbox("🗺️ País específico:", paises_disp, key="pais_sel")

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
                    text=f'Importaciones por País de Origen'
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
                    st.dataframe(marcas_p_full, hide_index=True, use_container_width=True)

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
                st.dataframe(tabla_m, hide_index=True, use_container_width=True)

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

# ── TAB 5: COBERTURA AAP ──────────────────────────────────────────────────────
with tab5:
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
        año_aap = st.selectbox("Año AAP", años_aap,
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
        comp["cobertura_pct"] = (
            (comp["vt_total"] / comp["aap_total"].replace(0, pd.NA)) * 100
        ).round(1)
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
            comp_show[["Marca", "AAP (uds)", "Veritrade (DUAs)", "Cobertura %"]],
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            "⚠️ Veritrade registra a nivel DUA (por expediente de importación), "
            "no por unidad individual. La cobertura % puede superar 100% si un DUA "
            "incluye múltiples unidades del mismo modelo."
        )

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.divider()
f_d = datetime.fromtimestamp(ULTIMA_ACT).strftime('%d/%m/%Y %H:%M') if ULTIMA_ACT else "—"
st.caption(f"Dashboard Camiones v2.0 · {len(df):,} registros · Veritrade · {f_d}")