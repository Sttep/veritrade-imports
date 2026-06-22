#!/usr/bin/env python3
"""Auditoría masiva de todos los archivos estructurados en outputs/"""

import pandas as pd
import sys
from pathlib import Path

def auditar_archivo(archivo):
    """Audita un solo archivo estructurado"""
    try:
        df = pd.read_excel(archivo, sheet_name='estructurado')
    except Exception as e:
        print(f"  ERROR: {e}")
        return None
    
    total = len(df)
    if total == 0:
        return None
    
    # Calcular métricas
    marca_ok = df['marca'].notna().sum() if 'marca' in df.columns else 0
    modelo_ok = df['modelo'].notna().sum() if 'modelo' in df.columns else 0
    carroceria_ok = df['carroceria'].notna().sum() if 'carroceria' in df.columns else 0
    anio_ok = df['anio_modelo'].notna().sum() if 'anio_modelo' in df.columns else 0
    combustible_ok = df['combustible'].notna().sum() if 'combustible' in df.columns else 0
    km_ok = df['kilometraje'].notna().sum() if 'kilometraje' in df.columns else 0
    
    # Score completo
    clave = ['marca', 'modelo', 'carroceria', 'anio_modelo', 'combustible']
    clave_presentes = [c for c in clave if c in df.columns]
    completos = df[clave_presentes].notna().all(axis=1).sum() if clave_presentes else 0
    
    # Sin clasificar
    sin_marca = df['marca'].isna() if 'marca' in df.columns else pd.Series([True]*total)
    sin_modelo = df['modelo'].isna() if 'modelo' in df.columns else pd.Series([True]*total)
    sin_carr = df['carroceria'].isna() if 'carroceria' in df.columns else pd.Series([True]*total)
    sin_nada = (sin_marca & sin_modelo & sin_carr).sum()
    
    return {
        'archivo': archivo.name,
        'total': total,
        'marca_pct': marca_ok/total*100,
        'modelo_pct': modelo_ok/total*100,
        'carroceria_pct': carroceria_ok/total*100,
        'anio_pct': anio_ok/total*100,
        'combustible_pct': combustible_ok/total*100,
        'km_pct': km_ok/total*100,
        'score_completo_pct': completos/total*100,
        'sin_clasificar_pct': sin_nada/total*100,
        'sin_clasificar_n': sin_nada,
    }

def auditar_outputs(carpeta="outputs"):
    """Audita todos los archivos _estructurado.xlsx en la carpeta"""
    ruta = Path(carpeta)
    archivos = sorted(ruta.glob("*_estructurado.xlsx"))
    
    if not archivos:
        print(f"\nNo se encontraron archivos *_estructurado.xlsx en {carpeta}/")
        print("Archivos disponibles:")
        for f in ruta.glob("*.xlsx"):
            print(f"  - {f.name}")
        return
    
    print(f"\n{'='*80}")
    print(f"  AUDITORIA MASIVA - PIPELINE CAMIONES")
    print(f"{'='*80}")
    print(f"  Carpeta: {carpeta}/")
    print(f"  Archivos encontrados: {len(archivos)}")
    print(f"{'='*80}")
    
    resultados = []
    for archivo in archivos:
        print(f"\n  Procesando: {archivo.name}...")
        r = auditar_archivo(archivo)
        if r:
            resultados.append(r)
            print(f"    Registros: {r['total']:,} | Modelos: {r['modelo_pct']:.1f}% | Score: {r['score_completo_pct']:.1f}%")
    
    if not resultados:
        print("\n  No se pudo procesar ningun archivo.")
        return
    
    # Tabla resumen
    print(f"\n{'='*80}")
    print(f"  RESUMEN POR ARCHIVO")
    print(f"{'='*80}")
    print(f"  {'Archivo':<45} {'Registros':>8} {'Modelos':>8} {'Marcas':>8} {'Score':>8} {'Sin clas.':>8}")
    print(f"  {'─'*45} {'─'*8} {'─'*8} {'─'*8} {'─'*8} {'─'*8}")
    
    total_registros = 0
    total_modelos_ok = 0
    total_marcas_ok = 0
    total_completos = 0
    total_sin_nada = 0
    
    for r in resultados:
        nombre = r['archivo'][:45]
        print(f"  {nombre:<45} {r['total']:>8,} {r['modelo_pct']:>7.1f}% {r['marca_pct']:>7.1f}% {r['score_completo_pct']:>7.1f}% {r['sin_clasificar_pct']:>7.1f}%")
        
        total_registros += r['total']
        total_modelos_ok += int(r['total'] * r['modelo_pct'] / 100)
        total_marcas_ok += int(r['total'] * r['marca_pct'] / 100)
        total_completos += int(r['total'] * r['score_completo_pct'] / 100)
        total_sin_nada += r['sin_clasificar_n']
    
    # Totales
    print(f"  {'─'*45} {'─'*8} {'─'*8} {'─'*8} {'─'*8} {'─'*8}")
    pct_modelos_total = total_modelos_ok / total_registros * 100 if total_registros > 0 else 0
    pct_marcas_total = total_marcas_ok / total_registros * 100 if total_registros > 0 else 0
    pct_completos_total = total_completos / total_registros * 100 if total_registros > 0 else 0
    pct_sin_total = total_sin_nada / total_registros * 100 if total_registros > 0 else 0
    
    print(f"  {'TOTAL':<45} {total_registros:>8,} {pct_modelos_total:>7.1f}% {pct_marcas_total:>7.1f}% {pct_completos_total:>7.1f}% {pct_sin_total:>7.1f}%")
    
    # Comparativa con maquinaria
    print(f"\n{'='*80}")
    print(f"  COMPARATIVA FINAL")
    print(f"{'='*80}")
    print(f"  | Metrica            | Maquinaria | Camiones   | Diferencia |")
    print(f"  |--------------------|------------|------------|------------|")
    
    dif_modelos = 95.5 - pct_modelos_total
    dif_marcas = 96.2 - pct_marcas_total
    
    print(f"  | Modelos detectados |    95.5%   |   {pct_modelos_total:>6.1f}%   |   {dif_modelos:>+6.1f}%   |")
    print(f"  | Marcas detectadas  |    96.2%   |   {pct_marcas_total:>6.1f}%   |   {dif_marcas:>+6.1f}%   |")
    print(f"  | Diccionario        |  881 mod.  |  En codigo |            |")
    print(f"  | Fase B (IA)        |    Si      |    No      |            |")
    print(f"  | Dashboard          |    Si      |    No      |            |")
    print(f"  | Total registros    |  20,497    |  {total_registros:>6,}   |            |")
    print(f"{'='*80}")
    
    # Recomendación
    print(f"\n  RECOMENDACION:")
    if pct_modelos_total < 80:
        print(f"  [URGENTE] Modelos <80%. Externalizar diccionario a Excel y activar Fase B (IA).")
    elif pct_modelos_total < 90:
        print(f"  [MEDIO] Modelos {pct_modelos_total:.1f}%. Expandir diccionario + Fase B opcional.")
    else:
        print(f"  [BUENO] Modelos >90%. Dashboard + Parquet es la prioridad.")
    
    if pct_sin_total > 5:
        print(f"  [URGENTE] {pct_sin_total:.1f}% sin clasificar. Revisar exclusiones y regex.")
    
    print(f"")

if __name__ == "__main__":
    carpeta = sys.argv[1] if len(sys.argv) > 1 else "outputs"
    auditar_outputs(carpeta)