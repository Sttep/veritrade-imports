#!/usr/bin/env python3
"""Exporta archivos estructurados con columna categoria_withmory (SIN LLM)"""

import pandas as pd
from pathlib import Path

def clasificar_withmory(row):
    """
    Clasifica según la lógica WITHMORY usando SOLO datos de la Fase 1
    """
    carroceria = str(row.get('carroceria', '')).upper()
    kg_bruto = row.get('kg_bruto', 0)
    categoria_peso = row.get('categoria_peso', '')
    
    # 1. TRACTOCAMIÓN
    if any(x in carroceria for x in ['TRACTOCAMIÓN', 'TRACTOCAMION', 'REMOLCADOR', 'TRACTOR']):
        return 'TRACTOCAMIÓN'
    
    # 2. VOLQUETE (todos los volquetes, sin importar peso)
    if 'VOLQUETE' in carroceria or 'VOLQUETA' in carroceria:
        return 'VOLQUETE'
    
    # 3. Si no es tracto ni volquete, usar categoria_peso
    if pd.notna(categoria_peso) and str(categoria_peso).strip():
        return str(categoria_peso).strip()
    
    return 'SIN_CATEGORIA'

def exportar_categoria_fase1():
    """Procesa todos los archivos estructurados y exporta con categoría"""
    
    print("=" * 80)
    print("EXPORTANDO ARCHIVOS ESTRUCTURADOS CON CATEGORÍA WITHMORY (SIN LLM)")
    print("=" * 80)
    
    archivos = sorted(Path("outputs").glob("*_estructurado.xlsx"))
    
    if not archivos:
        print("❌ No se encontraron archivos _estructurado.xlsx en outputs/")
        return
    
    print(f"\n📁 Archivos encontrados: {len(archivos)}")
    
    lista_dfs = []
    total_registros = 0
    conteo_categorias = {}
    
    for archivo in archivos:
        print(f"\n📄 Procesando: {archivo.name}")
        
        try:
            df = pd.read_excel(archivo, sheet_name="estructurado")
            
            # Agregar columna categoria_withmory
            df['categoria_withmory'] = df.apply(clasificar_withmory, axis=1)
            
            # Contar categorías
            conteo = df['categoria_withmory'].value_counts()
            for cat, count in conteo.items():
                conteo_categorias[cat] = conteo_categorias.get(cat, 0) + count
            
            print(f"  ✅ Registros: {len(df):,}")
            print(f"  📊 Categorías:")
            for cat, count in list(conteo.items())[:5]:
                print(f"      - {cat}: {count}")
            if len(conteo) > 5:
                print(f"      ... y {len(conteo)-5} categorías más")
            
            df['archivo_origen'] = archivo.name
            lista_dfs.append(df)
            total_registros += len(df)
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    if not lista_dfs:
        print("\n❌ No se pudo procesar ningún archivo")
        return
    
    df_combinado = pd.concat(lista_dfs, ignore_index=True)
    
    print("\n" + "=" * 80)
    print("COMBINANDO ARCHIVOS...")
    print("=" * 80)
    print(f"✅ Total registros combinados: {len(df_combinado):,}")
    
    print("\n📊 DISTRIBUCIÓN DE CATEGORÍAS WITHMORY:")
    print("-" * 40)
    for cat, count in sorted(conteo_categorias.items(), key=lambda x: x[1], reverse=True):
        pct = (count / total_registros * 100) if total_registros > 0 else 0
        print(f"  {cat:<25} {count:>8,} ({pct:>5.1f}%)")
    
    output_file = "outputs/combinado_categoria_fase1.xlsx"
    print(f"\n💾 Exportando a: {output_file}")
    
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        df_combinado.to_excel(writer, sheet_name="combinado", index=False)
        
        resumen = pd.DataFrame([
            {"metrica": "total_registros", "valor": total_registros},
            {"metrica": "total_archivos", "valor": len(archivos)},
        ])
        for cat, count in sorted(conteo_categorias.items(), key=lambda x: x[1], reverse=True):
            resumen = pd.concat([resumen, pd.DataFrame([{"metrica": f"categoria_{cat}", "valor": count}])])
        resumen.to_excel(writer, sheet_name="resumen", index=False)
    
    print(f"✅ Exportado correctamente a: {output_file}")
    print("=" * 80)
    
    print("\n📋 MUESTRA DE DATOS (primeras 10 filas):")
    columnas_mostrar = ['marca', 'modelo', 'carroceria', 'categoria_peso', 'categoria_withmory']
    columnas_existentes = [col for col in columnas_mostrar if col in df_combinado.columns]
    print(df_combinado[columnas_existentes].head(10).to_string(index=False))
    
    return df_combinado

if __name__ == "__main__":
    exportar_categoria_fase1()
    