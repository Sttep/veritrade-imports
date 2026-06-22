import pandas as pd
from pathlib import Path

partidas_a_revisar = [
    '8704319000', '8704322000', '8704329000',
    '8704411000', '8704419000', '8704420000',
    '8704520000', '8704601000', '8704609000',
    '8704901000', '8704909000', '8705901100',
    '8705901900', '8705909000', '8704211090',
    '8704219000', '8704222000', '8704229000'
]

for archivo in sorted(Path("inputs").glob("*.xlsx")):
    df = pd.read_excel(archivo, header=5)
    
    # Filtrar por partidas sospechosas
    for partida in partidas_a_revisar:
        df_partida = df[df['Partida Aduanera'] == int(partida)]
        if len(df_partida) > 0:
            print(f"{archivo.name} - {partida}: {len(df_partida)} registros")