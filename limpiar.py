#!/usr/bin/env python3
"""Limpia outputs/ y cache/ para ejecutar el pipeline desde cero"""

import shutil
import os
from pathlib import Path

OUTPUTS_DIR = "outputs"
CACHE_DIR = "cache"
INPUTS_DIR = "inputs"

def limpiar_outputs():
    """Elimina todos los archivos en outputs/"""
    out_dir = Path(OUTPUTS_DIR)
    
    if not out_dir.exists():
        print(f"  ℹ️ {OUTPUTS_DIR}/ no existe, creando...")
        out_dir.mkdir(parents=True, exist_ok=True)
        return
    
    archivos = list(out_dir.glob("*"))
    
    if not archivos:
        print(f"  ℹ️ {OUTPUTS_DIR}/ ya está vacío")
        return
    
    print(f"  📁 {OUTPUTS_DIR}/ contiene {len(archivos)} archivos")
    
    for archivo in archivos:
        if archivo.is_file():
            archivo.unlink()
            print(f"    🗑️ Eliminado: {archivo.name}")
        elif archivo.is_dir():
            shutil.rmtree(archivo)
            print(f"    🗑️ Eliminado directorio: {archivo.name}/")
    
    print(f"  ✅ {OUTPUTS_DIR}/ limpiado completamente")

def limpiar_cache():
    """Elimina la caché de LLM"""
    cache_dir = Path(CACHE_DIR)
    
    if not cache_dir.exists():
        print(f"  ℹ️ {CACHE_DIR}/ no existe, creando...")
        cache_dir.mkdir(parents=True, exist_ok=True)
        return
    
    archivos = list(cache_dir.glob("*"))
    
    if not archivos:
        print(f"  ℹ️ {CACHE_DIR}/ ya está vacío")
        return
    
    print(f"  📁 {CACHE_DIR}/ contiene {len(archivos)} archivos")
    
    for archivo in archivos:
        if archivo.is_file():
            archivo.unlink()
            print(f"    🗑️ Eliminado: {archivo.name}")
        elif archivo.is_dir():
            shutil.rmtree(archivo)
            print(f"    🗑️ Eliminado directorio: {archivo.name}/")
    
    print(f"  ✅ {CACHE_DIR}/ limpiado completamente")

def mostrar_resumen():
    """Muestra el estado actual de las carpetas"""
    print("\n" + "="*60)
    print("  📊 ESTADO ACTUAL")
    print("="*60)
    
    # Inputs
    inputs_dir = Path(INPUTS_DIR)
    if inputs_dir.exists():
        archivos_inputs = list(inputs_dir.glob("*.xlsx"))
        print(f"  📥 inputs/: {len(archivos_inputs)} archivos .xlsx")
        for a in archivos_inputs[:5]:
            print(f"      - {a.name}")
        if len(archivos_inputs) > 5:
            print(f"      ... y {len(archivos_inputs)-5} más")
    else:
        print(f"  ❌ {INPUTS_DIR}/ no existe")
    
    # Outputs
    outputs_dir = Path(OUTPUTS_DIR)
    if outputs_dir.exists():
        archivos_outputs = list(outputs_dir.glob("*.xlsx"))
        print(f"  📤 outputs/: {len(archivos_outputs)} archivos .xlsx")
    else:
        print(f"  ℹ️ outputs/: vacío")
    
    # Cache
    cache_dir = Path(CACHE_DIR)
    if cache_dir.exists():
        archivos_cache = list(cache_dir.glob("*"))
        print(f"  💾 cache/: {len(archivos_cache)} archivos")
    else:
        print(f"  ℹ️ cache/: vacío")
    
    print("="*60)

def main():
    import argparse
    
    ap = argparse.ArgumentParser(description="Limpia outputs y cache para pipeline")
    ap.add_argument("--outputs", action="store_true", help="Limpiar solo outputs/")
    ap.add_argument("--cache", action="store_true", help="Limpiar solo cache/")
    ap.add_argument("--all", action="store_true", help="Limpiar todo (outputs y cache)")
    ap.add_argument("--dry-run", action="store_true", help="Mostrar qué se va a eliminar sin hacerlo")
    args = ap.parse_args()
    
    # Si no hay argumentos, mostrar ayuda
    if not any([args.outputs, args.cache, args.all]):
        print("""
🧹 LIMPIADOR DE PIPELINE

Uso:
  python limpiar.py --all       # Limpia outputs/ y cache/
  python limpiar.py --outputs   # Limpia solo outputs/
  python limpiar.py --cache     # Limpia solo cache/
  python limpiar.py --dry-run   # Muestra qué se va a eliminar

Ejemplo:
  python limpiar.py --all       # Correr pipeline desde cero
""")
        mostrar_resumen()
        return
    
    print("\n" + "="*60)
    print("  🧹 LIMPIANDO PIPELINE")
    print("="*60)
    
    if args.dry_run:
        print("  ℹ️ MODO DRY-RUN (no se elimina nada)\n")
    
    # Limpiar outputs
    if args.all or args.outputs:
        if args.dry_run:
            print(f"  🔍 Simulando limpieza de {OUTPUTS_DIR}/...")
        else:
            limpiar_outputs()
    
    # Limpiar cache
    if args.all or args.cache:
        if args.dry_run:
            print(f"  🔍 Simulando limpieza de {CACHE_DIR}/...")
        else:
            limpiar_cache()
    
    # Mostrar resumen final
    if not args.dry_run:
        print("\n" + "="*60)
        print("  ✅ LIMPIEZA COMPLETADA")
        print("="*60)
        print("  Ahora puedes ejecutar:")
        print("    python fase1.py")
        print("    python fase2.py")
        print("="*60)
    
    mostrar_resumen()

if __name__ == "__main__":
    main()