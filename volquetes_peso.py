import pandas as pd
from pathlib import Path

print("=" * 70)
print("COMPARACIÓN: PESO BRUTO VS PESO NETO EN VOLQUETES")
print("=" * 70)

for archivo in sorted(Path("outputs").glob("*_estructurado.xlsx")):
    df = pd.read_excel(archivo, sheet_name="estructurado")
    volq = df[df['carroceria'].str.contains('VOLQUETE', na=False)]
    
    if len(volq) > 0:
        print(f"\n📁 {archivo.name}")
        print(f"  Volquetes: {len(volq)}")
        
        # Ver si existe kg_neto
        if 'kg_neto' in volq.columns:
            print(f"  Peso bruto promedio: {volq['kg_bruto'].mean():.0f} kg")
            print(f"  Peso neto promedio:  {volq['kg_neto'].mean():.0f} kg")
            
            # Ver casos donde neto > bruto (imposible físicamente)
            casos_raros = volq[volq['kg_neto'] > volq['kg_bruto']]
            if len(casos_raros) > 0:
                print(f"  ⚠️ {len(casos_raros)} casos donde peso NETO > BRUTO (intercambiados)")
        else:
            print(f"  ⚠️ No hay columna 'kg_neto'")