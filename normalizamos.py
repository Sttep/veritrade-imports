import pandas as pd

archivo = 'Métricas y resumen de gastos 2026(Desglose por campañas Mayo).csv'

print("📂 Leyendo archivo original...")
# Usamos 'latin-1' para evitar conflictos con caracteres especiales y eñes
df = pd.read_csv(archivo, header=None, encoding='latin-1')

print("🔄 Procesando datos con limpieza relacional estricta...")

datos = []
linea_actual = "DESCONOCIDO"
zona_actual = "-"

for idx, row in df.iterrows():
    # Convertimos toda la fila a un string unido en mayúsculas para buscar palabras clave fácilmente
    fila_completa_str = " ".join([str(val).upper() for val in row.values if pd.notna(val)])
    
    col0 = str(row[0]).strip() if pd.notna(row[0]) else ''
    col1 = str(row[1]).strip() if pd.notna(row[1]) else ''
    
    # 1. IGNORAR RESÚMENES GENERALES Y TOTALES
    if "RESUMEN" in fila_completa_str or "TOTAL" in col0.upper() or "LÍNEA / ZONA" in col0:
        continue
        
    # 2. DETECTAR CAMBIO DE BLOQUE DE CAMPAÑA
    if "CAMPAÑA" in col0.upper():
        # Identificar Línea
        if "CAMIONES" in col0.upper() or "SINOTRUK" in col0.upper():
            linea_actual = "CAMIONES"
        elif "MAQUINARIA" in col0.upper():
            linea_actual = "MAQUINARIA"
        elif "REPUESTOS" in col0.upper():
            linea_actual = "REPUESTOS"
        else:
            linea_actual = "OTROS"
            
        # Identificar Zona
        if "LIMA" in col0.upper():
            zona_actual = "LIMA"
        elif "NORTE" in col0.upper():
            zona_actual = "NORTE"
        else:
            zona_actual = "-"
        continue

    # 3. CAPTURAR FILAS GRANULARES DE PRODUCTO
    if col0 and col0 != 'Campaña':
        # Validar si la columna de alcance o impresiones es numérica limpia
        val_col1 = col1.replace(',', '').replace(' ', '')
        if val_col1.replace('.', '', 1).isdigit():
            try:
                alcance = float(col1.replace(',', '').strip())
                impresiones = float(str(row[2]).replace(',', '').strip())
                inversion = float(str(row[3]).replace(',', '').strip())
                leads = float(str(row[4]).replace(',', '').strip())
                cpr = float(str(row[5]).replace(',', '').strip())
                
                datos.append({
                    'Línea': linea_actual,
                    'Zona': zona_actual,
                    'Campaña': col0,
                    'Alcance': alcance,
                    'Impresiones': impresiones,
                    'Inversión_USD': inversion,
                    'Leads': leads,
                    'CPR_USD': cpr
                })
            except Exception as e:
                continue

# Crear DataFrame consolidado
df_final = pd.DataFrame(datos)

# Filtrar para evitar que se cuele cualquier residuo no deseado si quedó fuera de bloque
df_final = df_final[df_final['Línea'] != 'DESCONOCIDO']

# Limpieza final de duplicados y ordenamiento
df_final = df_final.drop_duplicates()
df_final = df_final.sort_values(['Línea', 'Zona', 'Campaña']).reset_index(drop=True)

# Redondear campos financieros
df_final[['Inversión_USD', 'CPR_USD']] = df_final[['Inversión_USD', 'CPR_USD']].round(2)

# Guardar salida normalizada
df_final.to_csv('data_normalizada.csv', index=False, encoding='utf-8-sig')

print(f'\n✅ ¡PROCESO COMPLETADO! Se guardaron {len(df_final)} filas reales en data_normalizada.csv')
print('\n📊 Vista del DataFrame Tabular:')
print(df_final.to_string())

print('\n📌 Resumen Ejecutivo Real (Métricas de BI Agregadas):')
resumen = df_final.groupby(['Línea', 'Zona']).agg({
    'Inversión_USD': 'sum',
    'Leads': 'sum'
})
resumen['CPR_Real_USD'] = (resumen['Inversión_USD'] / resumen['Leads']).round(2)
print(resumen)