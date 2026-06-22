#!/usr/bin/env python3
"""Auditoría de CALIDAD del Pipeline - Verifica coherencia de clasificaciones
   [VERSIÓN MEJORADA - Con checks de flags, llenado de campos y submarcas]"""

import pandas as pd
import sys
from pathlib import Path
from collections import Counter

# ============================================================
# CONSTANTES
# ============================================================
VOLQUETE_PESADO_MIN_KG = 25000
CAMPOS_CRITICOS = ['marca', 'modelo', 'carroceria', 'traccion', 'combustible', 
                   'clasificacion', 'caja', 'kg_bruto', 'vin', 'chasis']

CARROCERIAS_ESTANDAR = [
    'TRACTOCAMIÓN', 'VOLQUETE', 'BARANDA', 'FURGÓN', 'FURGON',
    'CISTERNA', 'PLATAFORMA', 'CAJA', 'ESTACAS', 'REFRIGERADO',
    'HORMIGONERA', 'GRÚA', 'CHASIS CABINA', 'CAMA BAJA',
    'ISOTERMICO', 'GANADERA', 'PORTACONTENEDOR', 'COMPACTADOR',
    'FRIGORÍFICO', 'MEZCLADORA', 'CARRO BOMBA', 'MAQUINARIA',
    'PLATAFORMA ELEVADORA', 'REMOLQUE',
]

# ============================================================
# FUNCIONES DE AUDITORÍA
# ============================================================

def verificar_columna(df, columna):
    """Verifica si una columna existe en el DataFrame"""
    return columna in df.columns

def obtener_columna(df, columna, default=None):
    """Obtiene una columna de forma segura"""
    return df[columna] if columna in df.columns else default

def auditar_calidad(archivo, mostrar_ejemplos=10):
    """Audita la calidad de las clasificaciones en un archivo estructurado"""
    
    print(f"\n{'='*80}")
    print(f"  AUDITORIA DE CALIDAD - PIPELINE")
    print(f"{'='*80}")
    
    try:
        df = pd.read_excel(archivo, sheet_name='estructurado')
    except Exception as e:
        print(f"  ERROR: {e}")
        return []
    
    total = len(df)
    print(f"  Archivo: {Path(archivo).name}")
    print(f"  Registros: {total:,}")
    
    problemas = []
    
    # ============================================================
    # 0. % DE LLENADO DE CAMPOS CRÍTICOS (NUEVO)
    # ============================================================
    print(f"\n{'─'*80}")
    print(f"  [0] PORCENTAJE DE LLENADO DE CAMPOS CRÍTICOS")
    print(f"{'─'*80}")
    
    for campo in CAMPOS_CRITICOS:
        if campo in df.columns:
            pct = df[campo].notna().mean() * 100
            emoji = "✅" if pct >= 95 else "⚠️" if pct >= 80 else "🔴"
            print(f"  {emoji} {campo:<15} {pct:>6.1f}%")
            if pct < 80:
                problemas.append(f"Bajo llenado de {campo}: {pct:.1f}%")
        else:
            print(f"  ❌ {campo:<15}   COLUMNA NO EXISTE")
            problemas.append(f"Columna faltante: {campo}")
    
    # ============================================================
    # 0.5. VALIDACIÓN DE BANDERAS (modelo_flag) (NUEVO)
    # ============================================================
    print(f"\n{'─'*80}")
    print(f"  [0.5] DISTRIBUCIÓN DE BANDERAS (modelo_flag)")
    print(f"{'─'*80}")
    
    if 'modelo_flag' in df.columns:
        flags = df['modelo_flag'].value_counts()
        total_flags = flags.sum()
        ok_count = flags.get('ok', 0)
        ok_pct = (ok_count / total_flags * 100) if total_flags > 0 else 0
        
        for flag_name in ['ok', 'low', 'nomatch', 'alias', 'sin_dato']:
            count = flags.get(flag_name, 0)
            pct = (count / total_flags * 100) if total_flags > 0 else 0
            print(f"  {flag_name:<10} {count:>6} ({pct:>5.1f}%)")
        
        if ok_pct < 70:
            problemas.append(f"⚠️ Bajo % de OK en flags: {ok_pct:.1f}%")
        elif ok_pct >= 90:
            print(f"  ✅ Excelente: {ok_pct:.1f}% de registros OK")
    else:
        print("  ❌ Columna 'modelo_flag' NO EXISTE")
        problemas.append("Columna faltante: modelo_flag")
    
    # ============================================================
    # 0.6. VALIDACIÓN DE SUBMARCA SINOTRUK (NUEVO)
    # ============================================================
    print(f"\n{'─'*80}")
    print(f"  [0.6] SINOTRUK - SUBMARCAS Y TIPOS DE IMPORTADOR")
    print(f"{'─'*80}")
    
    if 'marca' in df.columns and 'submarca_sinotruk' in df.columns:
        sinotruks = df[df['marca'].str.upper().str.contains('SINOTRUK|SITRAK|HOWO|HONAN|WANGPAI', na=False)]
        if len(sinotruks) > 0:
            print(f"  Registros SINOTRUK: {len(sinotruks)}")
            
            # Verificar submarcas
            sin_submarca = sinotruks[sinotruks['submarca_sinotruk'].isna()]
            if len(sin_submarca) > 0:
                print(f"  ⚠️ {len(sin_submarca)} registros SINOTRUK SIN submarca asignada")
                problemas.append(f"Sinotruk sin submarca: {len(sin_submarca)} registros")
            else:
                print(f"  ✅ Todos los SINOTRUK tienen submarca")
            
            # Mostrar submarcas
            print(f"  Submarcas:")
            for s, c in sinotruks['submarca_sinotruk'].value_counts().items():
                print(f"    {s:<25} {c:>5}")
            
            # Verificar importadores
            if 'tipo_importador_sinotruk' in df.columns:
                sin_importador = sinotruks[sinotruks['tipo_importador_sinotruk'].isna()]
                if len(sin_importador) > 0:
                    print(f"  ⚠️ {len(sin_importador)} registros SINOTRUK SIN tipo de importador")
                    problemas.append(f"Sinotruk sin importador: {len(sin_importador)} registros")
                else:
                    print(f"  ✅ Todos los SINOTRUK tienen tipo de importador")
                
                print(f"  Tipos de importador:")
                for t, c in sinotruks['tipo_importador_sinotruk'].value_counts().items():
                    print(f"    {t:<15} {c:>5}")
        else:
            print(f"  ℹ️ No hay registros SINOTRUK en este archivo")
    else:
        print("  ❌ Columnas 'marca' o 'submarca_sinotruk' NO EXISTEN")
    
    # ============================================================
    # 1. MARCAS CON POCOS REGISTROS (posibles errores de tipeo)
    # ============================================================
    print(f"\n{'─'*80}")
    print(f"  [1] MARCAS SOSPECHOSAS (pocos registros, posibles errores)")
    print(f"{'─'*80}")
    
    if 'marca' in df.columns:
        marcas_count = df['marca'].value_counts()
        marcas_raras = marcas_count[marcas_count <= 3]
        
        if len(marcas_raras) > 0:
            print(f"  Marcas con 3 o menos registros: {len(marcas_raras)}")
            for marca, count in marcas_raras.head(20).items():
                if pd.notna(marca):
                    print(f"    - {str(marca)[:40]:<42} {count:>5} regs.")
                    problemas.append(f"Marca rara: {marca} ({count} regs)")
        else:
            print(f"  ✅ Sin marcas sospechosas")
    else:
        print("  ❌ Columna 'marca' NO EXISTE")
    
    # ============================================================
    # 2. CARROCERÍAS ASIGNADAS A MARCAS INCORRECTAS
    # ============================================================
    print(f"\n{'─'*80}")
    print(f"  [2] MARCAS QUE APARECEN COMO CARROCERÍA (ERROR CONOCIDO)")
    print(f"{'─'*80}")
    
    if 'carroceria' in df.columns and 'marca' in df.columns:
        marcas_set = set(df['marca'].dropna().str.upper().unique())
        carr_marcas = df[df['carroceria'].notna() & df['carroceria'].str.upper().isin(marcas_set)]
        
        if len(carr_marcas) > 0:
            print(f"  ⚠️  {len(carr_marcas)} registros tienen una MARCA como CARROCERÍA:")
            for carr, count in carr_marcas['carroceria'].value_counts().head(10).items():
                print(f"    - Carrocería='{carr}' en {count} registros (¿es una marca!)")
                problemas.append(f"Marca como carrocería: {carr} ({count} regs)")
        else:
            print(f"  ✅ Sin marcas asignadas como carrocería")
    
    # ============================================================
    # 3. VOLQUETES LIVIANOS (posible mala clasificación)
    # ============================================================
    print(f"\n{'─'*80}")
    print(f"  [3] VOLQUETES LIVIANOS (<25 Ton) - ¿Son realmente volquetes?")
    print(f"{'─'*80}")
    
    if 'carroceria' in df.columns and 'kg_bruto' in df.columns:
        volq = df[df['carroceria'].str.upper().str.contains('VOLQUETE|VOLQUETA', na=False)]
        if len(volq) > 0:
            volq_livianos = volq[pd.to_numeric(volq['kg_bruto'], errors='coerce') < VOLQUETE_PESADO_MIN_KG]
            if len(volq_livianos) > 0:
                pct = len(volq_livianos) / len(volq) * 100
                print(f"  ⚠️  {len(volq_livianos)} de {len(volq)} volquetes son <25 Ton ({pct:.1f}%)")
                print(f"  Ejemplos:")
                for _, row in volq_livianos.head(5).iterrows():
                    desc = str(row.get('_descripcion', ''))[:100]
                    kg = row.get('kg_bruto', '?')
                    print(f"    - {kg} kg | {desc}")
                    problemas.append(f"Volquete liviano: {kg}kg - {desc[:80]}")
            else:
                print(f"  ✅ Todos los volquetes son >=25 Ton")
        else:
            print(f"  ℹ️ No hay volquetes en este archivo")
    
    # ============================================================
    # 4. TRACTOCAMIONES CON CARGA ÚTIL
    # ============================================================
    print(f"\n{'─'*80}")
    print(f"  [4] TRACTOCAMIONES CON CARGA ÚTIL (¿mal clasificados?)")
    print(f"{'─'*80}")
    
    if 'carroceria' in df.columns and 'carga_util' in df.columns:
        tractos = df[df['carroceria'].str.upper().str.contains('TRACTOCAMI|TRACTOR|REMOLCADOR', na=False)]
        if len(tractos) > 0:
            tractos_con_carga = tractos[tractos['carga_util'].notna() & (tractos['carga_util'] > 0)]
            if len(tractos_con_carga) > 0:
                print(f"  ⚠️  {len(tractos_con_carga)} tractocamiones tienen carga útil (raro)")
                for _, row in tractos_con_carga.head(5).iterrows():
                    desc = str(row.get('_descripcion', ''))[:100]
                    cu = row.get('carga_util', '?')
                    print(f"    - Carga útil: {cu} | {desc}")
                    problemas.append(f"Tracto con carga útil: {cu} - {desc[:80]}")
            else:
                print(f"  ✅ Sin tractocamiones con carga útil")
        else:
            print(f"  ℹ️ No hay tractocamiones en este archivo")
    
    # ============================================================
    # 5. KILOMETRAJES SOSPECHOSOS
    # ============================================================
    print(f"\n{'─'*80}")
    print(f"  [5] KILOMETRAJES ANÓMALOS")
    print(f"{'─'*80}")
    
    if 'kilometraje' in df.columns:
        km = pd.to_numeric(df['kilometraje'], errors='coerce')
        km_altos = df[km > 500000]
        km_negativos = df[km < 0]
        
        if len(km_altos) > 0:
            print(f"  ⚠️  {len(km_altos)} vehículos con >500,000 km:")
            for _, row in km_altos.head(5).iterrows():
                desc = str(row.get('_descripcion', ''))[:100]
                kms = row.get('kilometraje', '?')
                print(f"    - {kms} km | {desc}")
                problemas.append(f"KM muy alto: {kms} - {desc[:80]}")
        
        if len(km_negativos) > 0:
            print(f"  ⚠️  {len(km_negativos)} vehículos con km negativo (ERROR)")
            problemas.append(f"KM negativo: {len(km_negativos)} registros")
        
        if len(km_altos) == 0 and len(km_negativos) == 0:
            print(f"  ✅ Sin anomalías de kilometraje")
    
    # ============================================================
    # 6. AÑOS FUTUROS O MUY ANTIGUOS
    # ============================================================
    print(f"\n{'─'*80}")
    print(f"  [6] AÑOS MODELO SOSPECHOSOS")
    print(f"{'─'*80}")
    
    if 'anio_modelo' in df.columns:
        anio = pd.to_numeric(df['anio_modelo'], errors='coerce')
        anios_futuros = df[anio > 2027]
        anios_antiguos = df[anio < 2000]
        
        if len(anios_futuros) > 0:
            print(f"  ⚠️  {len(anios_futuros)} vehículos con año >2027 (¿futuro?)")
            for _, row in anios_futuros.head(5).iterrows():
                desc = str(row.get('_descripcion', ''))[:100]
                a = row.get('anio_modelo', '?')
                print(f"    - Año {a} | {desc}")
                problemas.append(f"Año futuro: {a} - {desc[:80]}")
        
        if len(anios_antiguos) > 0:
            print(f"  ⚠️  {len(anios_antiguos)} vehículos con año <2000")
            if len(anios_antiguos) <= 10:
                for _, row in anios_antiguos.iterrows():
                    desc = str(row.get('_descripcion', ''))[:100]
                    a = row.get('anio_modelo', '?')
                    print(f"    - Año {a} | {desc}")
        
        if len(anios_futuros) == 0 and len(anios_antiguos) == 0:
            print(f"  ✅ Sin años sospechosos")
        elif len(anios_antiguos) > 10:
            print(f"  (mostrando solo conteo, son {len(anios_antiguos)} registros)")
    
    # ============================================================
    # 7. MARCAS CON MODELOS QUE NO COINCIDEN
    # ============================================================
    print(f"\n{'─'*80}")
    print(f"  [7] COMBINACIONES MARCA-MODELO INUSUALES")
    print(f"{'─'*80}")
    
    if 'marca' in df.columns and 'modelo' in df.columns:
        # Optimizado: solo si hay menos de 10,000 registros o con muestreo
        if len(df) > 10000:
            print(f"  ℹ️ {len(df)} registros - muestreando para rendimiento...")
            df_sample = df.sample(min(5000, len(df)))
        else:
            df_sample = df
        
        modelo_marcas = df_sample.groupby('modelo')['marca'].apply(lambda x: list(set(x.dropna()))).reset_index()
        modelo_marcas['num_marcas'] = modelo_marcas['marca'].apply(len)
        conflictivos = modelo_marcas[modelo_marcas['num_marcas'] > 1].sort_values('num_marcas', ascending=False)
        
        if len(conflictivos) > 0:
            print(f"  ⚠️  {len(conflictivos)} modelos aparecen con MÚLTIPLES marcas (muestra):")
            for _, row in conflictivos.head(15).iterrows():
                modelo = row['modelo']
                marcas_lista = row['marca'][:5]
                num = row['num_marcas']
                print(f"    - {str(modelo)[:30]:<32} ({num} marcas) → {', '.join(str(m)[:20] for m in marcas_lista)}")
                if num > 3:
                    problemas.append(f"Modelo multi-marca: {modelo} ({num} marcas)")
        else:
            print(f"  ✅ Cada modelo pertenece a una sola marca")
    
    # ============================================================
    # 8. REGISTROS DUPLICADOS
    # ============================================================
    print(f"\n{'─'*80}")
    print(f"  [8] REGISTROS DUPLICADOS (VIN/Chasis repetido)")
    print(f"{'─'*80}")
    
    for campo_id in ['vin', 'chasis']:
        if campo_id in df.columns:
            dups = df[df[campo_id].notna() & df[campo_id].duplicated(keep=False)]
            if len(dups) > 0:
                print(f"  ⚠️  {len(dups)} registros con {campo_id} duplicado")
                problemas.append(f"{campo_id} duplicados: {len(dups)} registros")
            else:
                print(f"  ✅ Sin {campo_id} duplicados")
    
    # ============================================================
    # 9. ESTADO vs KILOMETRAJE
    # ============================================================
    print(f"\n{'─'*80}")
    print(f"  [9] INCONSISTENCIAS ESTADO vs KILOMETRAJE")
    print(f"{'─'*80}")
    
    if 'estado' in df.columns and 'kilometraje' in df.columns:
        nuevos = df[df['estado'].str.upper().str.contains('NUEVO|NEW|0 KM', na=False)]
        if len(nuevos) > 0:
            km_nuevos = pd.to_numeric(nuevos['kilometraje'], errors='coerce')
            nuevos_km_altos = nuevos[km_nuevos > 1000]
            
            if len(nuevos_km_altos) > 0:
                print(f"  ⚠️  {len(nuevos_km_altos)} vehículos 'NUEVOS' con >1,000 km:")
                for _, row in nuevos_km_altos.head(5).iterrows():
                    desc = str(row.get('_descripcion', ''))[:100]
                    kms = row.get('kilometraje', '?')
                    est = row.get('estado', '?')
                    print(f"    - Estado: {est} | KM: {kms} | {desc}")
                    problemas.append(f"Nuevo con {kms}km - {desc[:80]}")
            else:
                print(f"  ✅ Sin inconsistencias estado/km")
        else:
            print(f"  ℹ️ No hay vehículos 'NUEVOS' en este archivo")
    
    # ============================================================
    # 10. CARROCERÍAS NO MAPEADAS
    # ============================================================
    print(f"\n{'─'*80}")
    print(f"  [10] CARROCERÍAS NO ESTÁNDAR (posibles errores)")
    print(f"{'─'*80}")
    
    if 'carroceria' in df.columns:
        carr = df['carroceria'].dropna()
        if len(carr) > 0:
            carr_upper = carr.str.upper()
            estandar_upper = [c.upper() for c in CARROCERIAS_ESTANDAR]
            no_estandar = carr[~carr_upper.isin(estandar_upper)]
            
            if len(no_estandar) > 0:
                print(f"  ⚠️  {len(no_estandar)} registros con carrocerías no estándar:")
                for c, count in no_estandar.value_counts().head(15).items():
                    print(f"    - {str(c)[:40]:<42} {count:>5} regs.")
                    if count <= 3:
                        problemas.append(f"Carrocería rara: {c} ({count} regs)")
            else:
                print(f"  ✅ Todas las carrocerías son estándar")
        else:
            print(f"  ℹ️ No hay carrocerías en este archivo")
    
    # ============================================================
    # RESUMEN FINAL
    # ============================================================
    print(f"\n{'='*80}")
    print(f"  RESUMEN DE CALIDAD")
    print(f"{'='*80}")
    print(f"  Registros totales: {total:,}")
    print(f"  Problemas encontrados: {len(problemas)}")
    
    if len(problemas) == 0:
        print(f"\n  🟢 CALIDAD EXCELENTE - No se encontraron problemas.")
    elif len(problemas) <= 10:
        print(f"\n  🟡 CALIDAD BUENA - {len(problemas)} problemas menores.")
    elif len(problemas) <= 30:
        print(f"\n  🟠 CALIDAD REGULAR - {len(problemas)} problemas. Revisar.")
    else:
        print(f"\n  🔴 CALIDAD BAJA - {len(problemas)} problemas. Requiere atención.")
    
    if problemas:
        print(f"\n  Lista de problemas:")
        for i, p in enumerate(problemas[:20], 1):
            print(f"    {i:2}. {p[:100]}")
        if len(problemas) > 20:
            print(f"    ... y {len(problemas)-20} problemas más")
    
    print(f"\n{'='*80}")
    
    return problemas


def auditar_calidad_outputs(carpeta="outputs"):
    """Audita la calidad de todos los archivos estructurados"""
    ruta = Path(carpeta)
    archivos = sorted(ruta.glob("*_estructurado.xlsx"))
    
    if not archivos:
        print(f"\nNo se encontraron archivos *_estructurado.xlsx en {carpeta}/")
        return
    
    print(f"\n{'='*80}")
    print(f"  AUDITORIA DE CALIDAD MASIVA")
    print(f"{'='*80}")
    print(f"  Carpeta: {carpeta}/")
    print(f"  Archivos: {len(archivos)}")
    
    todos_problemas = []
    for archivo in archivos:
        problemas = auditar_calidad(archivo)
        if problemas:
            todos_problemas.extend(problemas)
    
    print(f"\n{'='*80}")
    print(f"  TOTAL PROBLEMAS ENCONTRADOS: {len(todos_problemas)}")
    print(f"{'='*80}")
    
    if todos_problemas:
        print(f"\n  Problemas más frecuentes:")
        for prob, count in Counter(todos_problemas).most_common(10):
            print(f"    - [{count}x] {prob[:100]}")
    else:
        print(f"\n  🟢 No se encontraron problemas de calidad en ningún archivo.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "outputs" or Path(sys.argv[1]).is_dir():
            auditar_calidad_outputs(sys.argv[1])
        else:
            auditar_calidad(sys.argv[1])
    else:
        auditar_calidad_outputs("outputs")