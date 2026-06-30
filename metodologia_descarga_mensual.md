# Metodología de Descarga Mensual — Veritrade vs. AAP
**Segmento:** Camiones y Tractocamiones Nuevos — Perú
**Frecuencia:** Mensual (al publicarse el nuevo reporte AAP)

---

## 1. Trigger de actualización

Descargar cuando la AAP publique el reporte mensual de importaciones (generalmente primera semana del mes siguiente). El archivo se deposita en `refs/` con el nombre:
```
refs/05-7-importacion-de-vehiculos-livianos-y-pesados-MMMMM-YYYY.xlsx
```
Luego ejecutar `python pipeline/aap.py` para regenerar `data/gold/aap_camiones.parquet`.

---

## 2. Partidas arancelarias a descargar de Veritrade

Buscar en Veritrade → **Importaciones** → filtro por **Partida Arancelaria** → período = mes nuevo (o el período completo si es la primera descarga).

### 2a. Partidas OBLIGATORIAS (alto volumen — cubren ~95% del mercado)

| Partida | Descripción | Marcas principales | Volumen aprox. |
|---|---|---|---|
| **8704230000** | Camiones diesel, PBV > 20t | SINOTRUK, VOLVO, SCANIA, MERCEDES-BENZ, FAW, SHACMAN, FOTON | ~15,500 DUAs |
| **8704222000** | Camiones diesel, 5t < PBV ≤ 20t | ISUZU, HINO, FUSO, JAC, DONGFENG, FOTON | ~15,900 DUAs |
| **8704229000** | Otros camiones diesel, 5t < PBV ≤ 20t | SINOTRUK, ISUZU, HINO, VOLKSWAGEN | ~12,600 DUAs |
| **8701210000** | Tractocamiones, PBV > 5t | MERCEDES-BENZ Actros/Arocs, VOLVO FH, SCANIA, INTERNATIONAL | ~8,300 DUAs |
| **8704221000** | Camiones diesel, PBV ≤ 5t (categoría media) | ISUZU, JMC, FORLAND | ~3,400 DUAs |

### 2b. Partidas COMPLEMENTARIAS (volumen medio — cubren marcas específicas)

| Partida | Descripción | Marcas principales | Por qué es importante |
|---|---|---|---|
| **8704211010** | Pickups diesel, PBV ≤ 5t | **VW AMAROK**, MAXUS T60 | Gap VW cerrado con esta partida (junio 2026) |
| **8704211090** | Otros pickups diesel, PBV ≤ 5t | VW CRAFTER, MAXUS C-100 | Complementa 8704211010 |
| **8704311010** | Pickups gasolina, PBV ≤ 5t | **VW SAVEIRO**, MAXUS T60 GNC | Gap VW cerrado con esta partida |
| **8701290000** | Tractocamiones (otros tipos) | **IVECO** AS-Way/Hi-Way, SITRAK | Gap IVECO cerrado con esta partida |
| **8704329000** | Camiones gasolina > 5t | **IVECO TECTOR GNC** | Modelos GNC de IVECO |
| **8705400000** | Vehículos especiales — hormigoneras/bombas | ZOOMLION (chasis SINOTRUK), SANY | Equipos sobre chasis camión |
| **8706009200** | Chasis con motor para camiones | SINOTRUK, HINO, FUSO | Chasis importados por carroceros |
| **8706009900** | Otros chasis con motor | VARIOS | Complementa 8706009200 |

### 2c. Partidas MENORES (bajo volumen — descargar solo si hay brecha detectada)

| Partida | Descripción | Marcas |
|---|---|---|
| 8701230000 | Tractocamiones (otro subtipo) | SINOTRUK, VOLVO |
| 8704100000 | Camiones de un eje | SANY (minería) |
| 8704601000 | Camiones eléctricos | MAXUS EV30, BYD |
| 8704311090 | Otros pickups gasolina ≤ 5t | KARRY |
| 8705909000 | Vehículos especiales (otros) | SANY (grúas) |
| 8705100000 | Camiones cisterna/contra incendios | NAFFCO, E-ONE (bomberos) |

---

## 3. Procedimiento de descarga en Veritrade

### Paso 1 — Descarga por partida (método principal)

1. Ingresar a Veritrade → **Importaciones Perú**
2. Filtro: **Partida Arancelaria** = código a descargar
3. **Período**: el mes nuevo completo (ej. `01/06/2026 - 30/06/2026`)
   - Si es una partida nueva nunca descargada: usar `01/01/2023 - fecha actual`
4. Exportar → Excel
5. Guardar en `data/bronze/` con nombre descriptivo:
   ```
   Veritrade_XXXXXXXX_PARTIDA_PERIODO.xlsx
   ```
   Ejemplo: `Veritrade_20260705_8704230000_JUN2026.xlsx`

> **Nota:** para el mes nuevo basta descargar solo ese mes. El pipeline detecta duplicados por DUA+VIN y no duplica registros.

### Paso 2 — Descarga por importador (método complementario)

Usar **solo si** después de correr la validación alguna marca queda < 88%.

Importadores críticos por marca:

| Marca con brecha | Importadores a buscar en Veritrade |
|---|---|
| VOLKSWAGEN | `EURO MOTORS S.A.` |
| IVECO | `ANDES MOTOR PERU S.A.C.` |
| SINOTRUK | `CAMIONES CHINOS PERU S.A.C.`, `PREMIER MOTORS S.A.`, `CORPORATION WITHMORY S.R.L.`, `CORIEX DS S.A.C.`, `COMINKA MOTORS S.A.C.`, `ZOOMLION HEAVY INDUSTRY PERU S.A.C.` |
| HOWO MAX | `ZAPLER S.A.C.` |
| MERCEDES-BENZ | Incluida en partida 8701210000 y 8704230000 |
| INTERNATIONAL / FREIGHTLINER | Incluidas en 8701210000 |

Procedimiento:
1. Filtro: **Importador** = nombre exacto
2. Período: mes nuevo (o full-year si nunca se descargó)
3. **No** filtrar por partida — bajar todo el importador
4. Guardar en `data/bronze/` con nombre del importador

---

## 4. Pipeline de procesamiento

Una vez que los archivos están en `data/bronze/`, ejecutar:

```bash
# Opción A — Pipeline completo (Bronze → Silver → Gold con LLM)
python pipeline/run.py

# Opción B — Solo extracción (sin LLM, más rápido para validar)
python pipeline/run.py --silver-only
```

> Para actualizar el parquet consolidado se requiere un paso adicional de consolidación (actualmente manual — ver nota al pie).

---

## 5. Validación de cobertura

Después de procesar, verificar con el script de auditoría:

```python
import pandas as pd
from pathlib import Path

ROOT = Path(".")
aap = pd.read_parquet(ROOT / "data/gold/aap_camiones.parquet")
vt  = pd.read_parquet(ROOT / "data/gold/camiones.parquet")

# Filtrar al período del nuevo reporte AAP
MES_NUEVO = 6   # <-- cambiar cada mes
ANIO = 2026     # <-- cambiar si corresponde

aap_per = aap[(aap["año"] == ANIO) & (aap["mes_num"] <= MES_NUEVO)]
vt["_dt"] = pd.to_datetime(vt["fecha_dua"], errors="coerce")
vt_per = vt[(vt["_dt"].dt.year == ANIO) & (vt["_dt"].dt.month <= MES_NUEVO)]

aap_tot = aap_per.groupby("marca_norm")["unidades"].sum()
vt_tot  = vt_per.groupby("marca_normalizada").size()

merged = pd.DataFrame({"aap": aap_tot, "vt": vt_tot}).fillna(0).astype(int)
merged["cob"] = (merged["vt"] / merged["aap"] * 100).round(1)
merged = merged[merged["aap"] > 5].sort_values("aap", ascending=False)
print(merged.to_string())
print(f"\nGlobal: {merged['vt'].sum()} / {merged['aap'].sum()} = {merged['vt'].sum()/merged['aap'].sum()*100:.1f}%")
```

### Umbrales de alerta

| Cobertura | Acción |
|---|---|
| ≥ 95% | OK — sin acción requerida |
| 88–94% | Revisar — posible rezago de DUAs del mes más reciente, esperar 2 semanas y re-verificar |
| < 88% | Acción requerida — descargar por importador (ver Paso 2) |
| > 115% | Revisar — posible doble conteo o marca AAP diferente a VT |

### Excepciones conocidas y permanentes

| Marca | Cobertura esperada | Razón |
|---|---|---|
| HOWO MAX | ~50% | WITHMORY declara como SINOTRUK en aduana; esas unidades están en el conteo SINOTRUK |
| SINOTRUK (familia) | ~90–92% | Rezago metodológico AAP (registro MTC) vs Veritrade (fecha DUA) |
| RAM | ~11% | Vehículos de rescate/bomberos (partida 8705300000) — segmento irrelevante para análisis comercial |
| FORD | 0% | 1 unidad histórica, insignificante |
| Marcas con 1–5 unidades | Variable | Volumen mínimo, no representativo |

---

## 6. Checklist mensual

```
[ ] 1. Descargar nuevo reporte AAP → guardar en refs/ → ejecutar pipeline/aap.py
[ ] 2. Descargar partidas OBLIGATORIAS para el nuevo mes (sección 2a)
[ ] 3. Descargar partidas COMPLEMENTARIAS (sección 2b) — solo el mes nuevo
[ ] 4. Integrar al parquet (pipeline/run.py o script de consolidación)
[ ] 5. Correr validación de cobertura (sección 5)
[ ] 6. Si alguna marca < 88%: descargar por importador (sección 3 Paso 2)
[ ] 7. Actualizar informe_auditoria_cobertura.md con la fecha y resultados
[ ] 8. git commit + git push
```

---

## 7. Estado de referencia (Ene–May 2026, tras auditoría completa)

| Marca | AAP | VT | Cobertura | Nota |
|---|---|---|---|---|
| ISUZU | 1,775 | 1,790 | 100.8% | ✅ |
| SINOTRUK | 1,640 | 1,505 | 91.8% | ✅ ver excepción |
| FOTON | 1,135 | 1,218 | 107.3% | ✅ |
| FUSO | 1,016 | 1,040 | 102.4% | ✅ |
| VOLVO | 937 | 944 | 100.7% | ✅ |
| SHACMAN | 902 | 895 | 99.2% | ✅ |
| JAC | 827 | 825 | 99.8% | ✅ |
| HINO | 682 | 730 | 107.0% | ✅ |
| MERCEDES-BENZ | 547 | 559 | 102.2% | ✅ |
| FAW | 495 | 461 | 93.1% | ✅ leve |
| SCANIA | 445 | 507 | 113.9% | ✅ |
| DONGFENG | 400 | 399 | 99.8% | ✅ |
| HYUNDAI | 263 | 330 | 125.5% | ✅ |
| INTERNATIONAL | 220 | 198 | 90.0% | ✅ leve |
| VOLKSWAGEN | 119 | 130 | 109.2% | ✅ |
| IVECO | 65 | 68 | 104.6% | ✅ |
| HOWO MAX | 70 | 37 | 52.9% | ✅ ver excepción |
| **GLOBAL** | **12,508** | **12,843** | **102.7%** | ✅ |
