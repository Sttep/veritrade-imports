#!/usr/bin/env python3
"""
Auditor de Descripciones Comerciales - Creado para Liz
Este script lee los vehículos "No Categorizados" y detecta qué códigos 
(conocidos y desconocidos) están escribiendo los agentes de aduanas.
"""

import pandas as pd
import re
import sys
from pathlib import Path
from collections import Counter

# --- CONFIGURACIÓN ---
ARCHIVO_ENTRADA = Path("inputs") / "Libro2-encontrados no categorizados.xlsx"
ARCHIVO_SALIDA = Path("analisis") / "Auditoria_Codigos_Aduanas.xlsx"

# Los códigos que tu sistema principal YA conoce
CODIGOS_CONOCIDOS = {
    "MARCA", "MODELO", "VERSION", "AÑO MOD", "AÑO", "VI", "CH", "CH/VIN",
    "MO", "CO", "COMB", "C1", "NC", "CC", "PM", "EJ", "FR", "TT",
    "CA", "AS", "PA", "PB", "PN", "CU", "LA", "AN", "AL", "DE", "KILOMETRAJE"
}

def encontrar_columna_descripcion(df):
    """Busca automáticamente cuál es la columna de la descripción comercial."""
    for col in df.columns:
        nombre_col = str(col).lower()
        if 'descripci' in nombre_col or 'comercial' in nombre_col:
            return col
    return None

def extraer_codigos(texto):
    """Busca patrones como 'PALABRA:' y extrae la 'PALABRA'."""
    if pd.isna(texto):
        return []
    # Busca cualquier palabra seguida de dos puntos
    matches = re.findall(r'([A-Za-z0-9/.]+)\s*:', str(texto))
    return [m.upper().strip() for m in matches]

def extraer_valor(texto, codigo):
    """Extrae lo que está escrito justo después de un código específico."""
    if pd.isna(texto):
        return None
    match = re.search(rf'{codigo}\s*:\s*([^,;]+)', str(texto), re.IGNORECASE)
    return match.group(1).strip() if match else None

def main():
    print("\n" + "="*50)
    print(" 🕵️‍♀️ INICIANDO AUDITORÍA DE DATOS REBELDES")
    print("="*50)

    # 1. Validar que el archivo exista
    if not ARCHIVO_ENTRADA.exists():
        print(f"\n❌ ERROR: No encuentro el archivo.")
        print(f"Por favor, asegúrate de que exista en esta ruta exacta: {ARCHIVO_ENTRADA}")
        sys.exit(1)

    # 2. Leer el Excel (ignorando posibles encabezados basura arriba)
    print("📖 Leyendo el archivo Excel...")
    try:
        df = pd.read_excel(ARCHIVO_ENTRADA)
    except Exception as e:
        print(f"❌ Error al leer el Excel: {e}")
        sys.exit(1)

    # 3. Encontrar la columna de descripción
    col_desc = encontrar_columna_descripcion(df)
    if not col_desc:
        print("❌ ERROR: No pude encontrar una columna llamada 'Descripción Comercial'.")
        sys.exit(1)

    print(f"✅ Columna encontrada: '{col_desc}'. Analizando {len(df)} filas...\n")

    descripciones = df[col_desc].dropna().astype(str)

    # 4. Extraer la información
    contador_todos_codigos = Counter()
    marcas = Counter()
    modelos = Counter()
    carrocerias = Counter()

    for desc in descripciones:
        # Contar códigos
        codigos_encontrados = extraer_codigos(desc)
        contador_todos_codigos.update(codigos_encontrados)
        
        # Extraer valores clave
        marca = extraer_valor(desc, "MARCA")
        if marca: marcas[marca.upper()] += 1
            
        modelo = extraer_valor(desc, "MODELO")
        if modelo: modelos[modelo.upper()] += 1
            
        carroceria = extraer_valor(desc, "CA")
        if carroceria: carrocerias[carroceria.upper()] += 1

    # Separar conocidos de desconocidos
    cod_desconocidos = {k: v for k, v in contador_todos_codigos.items() if k not in CODIGOS_CONOCIDOS}
    cod_conocidos = {k: v for k, v in contador_todos_codigos.items() if k in CODIGOS_CONOCIDOS}

    # 5. Imprimir el resumen en la pantalla negra
    print("--- 🚨 TOP 10 CÓDIGOS INVENTADOS (Desconocidos) ---")
    for cod, freq in Counter(cod_desconocidos).most_common(10):
        print(f"   {cod:<15} aparece {freq} veces")

    print("\n--- 🏭 TOP 5 MARCAS SIN CATEGORIZAR ---")
    for m, f in marcas.most_common(5):
        print(f"   {m:<15} aparece {f} veces")

    print("\n--- 🚜 TOP 5 MODELOS SIN CATEGORIZAR ---")
    for m, f in modelos.most_common(5):
        print(f"   {m:<15} aparece {f} veces")

    # 6. Exportar todo a un Excel hermoso
    print("\n💾 Guardando reporte detallado en Excel...")
    ARCHIVO_SALIDA.parent.mkdir(exist_ok=True) # Crea la carpeta 'analisis' si no existe
    
    with pd.ExcelWriter(ARCHIVO_SALIDA, engine='openpyxl') as writer:
        pd.DataFrame(Counter(cod_desconocidos).most_common(), columns=['Código Desconocido', 'Frecuencia']).to_excel(writer, sheet_name='Códigos Raros', index=False)
        pd.DataFrame(Counter(cod_conocidos).most_common(), columns=['Código Conocido', 'Frecuencia']).to_excel(writer, sheet_name='Códigos Normales', index=False)
        pd.DataFrame(marcas.most_common(), columns=['Marca', 'Frecuencia']).to_excel(writer, sheet_name='Top Marcas', index=False)
        pd.DataFrame(modelos.most_common(), columns=['Modelo', 'Frecuencia']).to_excel(writer, sheet_name='Top Modelos', index=False)
        pd.DataFrame(carrocerias.most_common(), columns=['Carrocería (CA)', 'Frecuencia']).to_excel(writer, sheet_name='Top Carrocerías', index=False)

    print(f"✅ ¡Éxito! Tu reporte te espera en: {ARCHIVO_SALIDA}")
    print("="*50)

if __name__ == "__main__":
    main()