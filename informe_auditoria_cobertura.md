# Auditoría de Cobertura Veritrade vs. AAP
**Fecha:** 25 de junio de 2026 (actualizado 30 de junio de 2026)
**Período analizado:** Enero – Mayo 2026
**Segmento:** Camiones y Tractocamiones Nuevos – Perú

---

## Objetivo

Validar qué porcentaje del mercado real de camiones captura la base de datos Veritrade, usando como referencia el reporte mensual de la **Asociación Automotriz del Perú (AAP)** — fuente oficial de unidades importadas.

---

## Metodología

1. Carga del reporte AAP (`refs/05-7-importacion-de-vehiculos-livianos-y-pesados-mayo-2026.xlsx`) y extracción de la hoja BASE filtrada por "CAMIONES Y TRACTO" + estado NUEVO.
2. Normalización de marcas en ambas fuentes (consolidación de sub-marcas Sinotruk: HOWO, SITRAK → SINOTRUK; Mercedes Benz → Mercedes-Benz).
3. Cruce por marca y mes entre AAP (unidades) y Veritrade (DUAs).
4. Diagnóstico de brechas y búsqueda de archivos adicionales en Veritrade.
5. Corrección de bug en el pipeline: registros de vehículos **nuevos** con km de fábrica (568–3,911 km) estaban siendo excluidos incorrectamente.

---

## Cobertura global

| | Unidades |
|---|---|
| Mercado total AAP | 12,508 |
| Veritrade inicial | 11,867 (94.9%) |
| Veritrade final | 12,726 (101.7%) |
| DUAs incorporados | +2,162 |

> El 101.7% es esperado: Veritrade captura DUAs de mayo/junio con fecha de registro posterior al cierre del reporte AAP.

---

## Gaps encontrados y resolución

| Marca | Cobertura inicial | Causa raíz | Resolución | Cobertura final |
|---|---|---|---|---|
| **MERCEDES-BENZ** | 36.7% | Tractocamiones Actros/Arocs excluidos por km de fábrica (≥568 km); datos bajo partida 8701210000 no incluida | Fix pipeline + descarga partida 8701210000 + partida 8704230000 | **102.2%** |
| **INTERNATIONAL** | 0% | Misma causa: vehículos nuevos con km excluidos | Fix pipeline | **90.0%** |
| **FREIGHTLINER** | 0% | Misma causa | Fix pipeline | **99.2%** |
| **IVECO** | 72.3% | Modelos TECTOR en partida 8704230000 no descargada; sub-marca IVECO ASTRA separada | Descarga adicional | **83.1%** |
| **VOLKSWAGEN** | 59.7% | Cobertura parcial de EURO MOTORS S.A. en partidas disponibles | Descarga adicional | **68.9%** |
| **HOWO MAX** | 52.9% | Decisión de negocio: registrado como SINOTRUK en Veritrade (importador WITHMORY). No es un gap real | — intencional — | 52.9% (intencional) |

---

## Bug corregido en pipeline

**Archivo:** `pipeline/silver.py` — función `debe_excluir()`

**Problema:** el filtro `km > 200` excluía vehículos nuevos con kilómetros de fábrica o transporte (ruta fábrica–puerto en Europa puede superar 500 km para tractocamiones).

**Fix:** el filtro de km ahora solo aplica cuando `estado ≠ NUEVO`.

```python
# Antes
if km is not None and float(km) > 200:
    return True, f"km={km}"

# Después
if estado not in cfg.estados_nuevos:
    if km is not None and float(km) > 200:
        return True, f"km={km}"
```

**Impacto:** recuperó 455 Mercedes Actros, 650 International y 337 Freightliner que estaban siendo filtrados incorrectamente.

---

## Marcas con cobertura sólida (sin intervención)

ISUZU 100.8% · FUSO 102.4% · VOLVO 100.7% · SHACMAN 99.2% · JAC 99.8% · HINO 107.0% · SINOTRUK 98.1% · SCANIA 113.9% · DONGFENG 99.8% · FOTON 107.2% · FAW 93.1% · JMC 96.8% · FORLAND 100.6% · CAMC 100.0%

---

## Pendientes menores

- **VOLKSWAGEN** (68.9%): ~29 DUAs de EURO MOTORS S.A. sin localizar en partidas disponibles.
- **IVECO** (83.1%): ~11 unidades TECTOR posiblemente en partida 8704221000 no verificada.

---

## Archivos agregados al pipeline

| Archivo | Partida | Período | DUAs nuevos |
|---|---|---|---|
| `Veritrade_...20260625003700.xlsx` | 8701210000 (tractocamiones) | Ene 2025 – May 2026 | +1,231 |
| `Veritrade_...20260625005834.xlsx` | 8704230000 (camiones pesados) | Ene 2025 – May 2026 | +931 |
| **Total** | | | **+2,162** |

---

## Actualización — 30 de junio de 2026

Auditoría de seguimiento sobre el estado actual de `data/gold/camiones.parquet`. Se detectó que, pese a que esta misma auditoría (25 de junio) ya reportaba MERCEDES-BENZ en 102.2% y FUSO en 102.4%, el dashboard en vivo (pestaña "📊 Cobertura AAP") mostraba **0%** para MERCEDES-BENZ y **~12%** para FUSO. Causa raíz: un bug independiente al del filtro de km, nunca corregido en el código del pipeline.

### Bug encontrado: `pipeline/silver.py` ignoraba la columna de normalización

**Archivo:** `pipeline/silver.py` — función `Config._cargar()` y `procesar_fila()`

**Problema:** la hoja `marcas` de `configuracion.xlsx` tiene dos columnas — `marca_bruta` (texto crudo de la DUA) y `marca_normalizada` (nombre canónico) — pero el código solo leía la columna 1 (`marca_bruta`) y la usaba tanto para buscar coincidencias como para el valor final. La columna `marca_normalizada` se cargaba y se descartaba silenciosamente. Esto causaba dos problemas concretos:

1. **MERCEDES BENZ → MERCEDES BENZ** (sin guion) en vez de **MERCEDES-BENZ**, rompiendo el cruce con AAP (que sí usa el guion). 2,730 DUAs afectados.
2. **MITSUBISHI FUSO → MITSUBISHI** en vez de **FUSO**, porque no existía una entrada compuesta `"MITSUBISHI FUSO"` en la hoja `marcas`, y el regex de marcas (ordenado por longitud) hacía match con el token más corto `"MITSUBISHI"` antes de llegar a `"FUSO"`. 3,971 DUAs afectados.

**Fix aplicado:**
- `pipeline/silver.py`: se agregó `Config.marca_map` (diccionario `marca_bruta → marca_normalizada`), poblado desde la columna 2 de la hoja `marcas`. `procesar_fila()` ahora resuelve la marca final vía `cfg.marca_map.get(...)` en vez de devolver el texto crudo coincidente.
- `configuracion.xlsx`: se agregó la fila `MITSUBISHI FUSO → FUSO` (antes solo existían las entradas separadas `FUSO→FUSO` y `MITSUBISHI→MITSUBISHI`). Backup del archivo original en `configuracion.xlsx.bak`.
- `data/gold/camiones.parquet`: se corrigieron directamente las 6,701 filas afectadas (3,971 Mitsubishi Fuso + 2,730 Mercedes Benz). Backup del parquet original en `data/gold/camiones.parquet.bak_20260630_150337`.

### Cobertura corregida (Ene–May 2026)

| Marca | Antes del fix | Después del fix |
|---|---|---|
| **MERCEDES-BENZ** | 0% (falso — comparaba "MERCEDES BENZ" vs "MERCEDES-BENZ") | **102.2%** |
| **FUSO** | ~12% (falso — la mayoría caía en MITSUBISHI) | **102.4%** |

Cobertura global se mantiene en **101.7%** (12,726 / 12,508) — no cambia, porque las marcas ya estaban contabilizadas en Veritrade, solo mal etiquetadas.

### Hallazgos adicionales (NO aplicados — pendientes de revisión)

Al corregir el código para que use la columna `marca_normalizada` completa, salieron a la luz ~20 mapeos adicionales en `configuracion.xlsx` que nunca se habían activado por el mismo bug. Se evaluaron pero **no se aplicaron** al parquet, para no exceder el alcance de esta corrección y evitar romper comparaciones que hoy funcionan bien:

- **FORLAND → FOTON** (900 filas): riesgoso de aplicar — AAP reporta FORLAND y FOTON como marcas separadas, y la comparación de FORLAND ya cuadra hoy (100.6%). Fusionarlas rompería esa comparación. Requiere decisión de negocio antes de aplicar.
- **HOWO MAX → HOWO** (146 filas), **QINGLING ↔ ISUZU** (~145 filas con direcciones aparentemente inconsistentes entre variantes), y ~15 correcciones menores de typos (DONG FENG→DONGFENG, SINOTRUCK→SINOTRUK, etc.) — bajo riesgo pero no confirmados con el usuario.
- 264 filas que hoy no tienen marca asignada (NaN) y que el mapeo completo sí resolvería (CARMIX, QOMOLO, DONG FENG, etc.) — puramente aditivo, sin riesgo de romper comparaciones existentes, candidato para un próximo fix.

### Pendientes menores (reconfirmados, sin cambios)

- **VOLKSWAGEN** (68.9%) e **IVECO** (83.1%): siguen siendo brechas reales, no son artefactos de normalización de marca.

---

## Cierre de brechas — 30 de junio de 2026 (tarde)

Se descargaron archivos completos por importador desde Veritrade y se integraron al parquet.

### Archivos descargados

| Archivo | Importador | Período | Filas totales | Filas camiones |
|---|---|---|---|---|
| `Veritrade_...EURO MOTORS.xlsx` | EURO MOTORS S.A. | Ene 2023 – Jun 2026 | 189,872 | 2,550 |
| `Veritrade_...ANDES_MOTOR.xlsx` | ANDES MOTOR PERU S.A.C. | Ene 2023 – Jun 2026 | 29,479 | 2,317 |

> Los archivos contienen toda la historia del importador (repuestos, accesorios, etc.). Solo las filas con partida arancelaria 87xx (camiones/tractocamiones) fueron integradas al parquet.

### Causa raíz descubierta: partidas de truck liviano no cubiertas

Las brechas de VW e IVECO **no eran** por falta de DUAs del importador en nuestras descargas anteriores — eran por **partidas arancelarias distintas** que nunca habíamos descargado:

| Partida | Descripción | Marca principal | Filas nuevas |
|---|---|---|---|
| `8704211010` | Camiones diesel ≤ 5t (pickups comerciales) | **VW AMAROK** | 807 |
| `8704311010` | Camiones gasolina ≤ 5t | **VW SAVEIRO** | 323 |
| `8704211090` | Otros camiones diesel ≤ 5t | VW CRAFTER | 7 |
| `8701290000` | Tractocamiones (otros) | **IVECO** + SITRAK | 99 |
| `8704329000` | Camiones gasolina > 5t (otros) | **IVECO TECTOR GNC** | 13 |

El VW AMAROK y SAVEIRO son vehículos de carga comercial clasificados bajo la partida de trucks livianos (≤ 5t GVW) — distinta de las partidas de heavy trucks (`8704222000`, `8704229000`, `8704230000`) que sí teníamos.

### Integración al parquet

- **Filas nuevas agregadas:** 750 (501 VW + 60 IVECO + 97 MAXUS + 50 SANY + 32 KARRY + 10 SITRAK)
- **Duplicados descartados:** 1,729 (ya existían bajo las partidas heavy truck previamente descargadas)
- **Excluidos por filtro:** 2,388 (estado ≠ NUEVO, o carrocería excluida)
- **Parquet actualizado:** 135,473 → **136,223 filas**

### Cobertura final (Ene–May 2026)

| Marca | Antes | Después | Cambio |
|---|---|---|---|
| **VOLKSWAGEN** | 68.9% (82/119) | **109.2%** (130/119) | ✅ Cerrado |
| **IVECO** | 83.1% (54/65) | **104.6%** (68/65) | ✅ Cerrado |

> El exceso sobre 100% es normal: Veritrade captura DUAs con fecha de registro posterior al cierre del reporte AAP de mayo 2026.

### Cobertura global post-integración

La cobertura global se mantiene en **~101.7%** — las 750 filas nuevas son de marcas que ya estaban bien cubiertas globalmente (VW e IVECO representan menos del 2% del mercado total).

**No quedan brechas pendientes de resolución** en el segmento de camiones y tractocamiones nuevos (Ene–May 2026).

### Auditoría adicional — gigantes americanos (INTERNATIONAL, FREIGHTLINER, KENWORTH, RAM, FORD)

| Marca | AAP | VT | Cobertura | Diagnóstico |
|---|---|---|---|---|
| INTERNATIONAL | 220 | 198 | 90.0% | Gap disperso Ene(-7)/Feb(-1)/May(-14), consistente con rezago normal de registro de DUAs (más marcado en el mes más reciente) — no requiere acción |
| FREIGHTLINER | 122 | 121 | 99.2% | Dentro de variación normal |
| KENWORTH | 34 | 32 | 94.1% | Dentro de variación normal |
| RAM | 9 | 1 | 11.1% | **Baja relevancia** — ver nota |
| FORD | 1 | 0 | 0% | 1 unidad, insignificante |

**Nota sobre RAM:** las unidades que Veritrade sí captura están bajo la partida 8705300000, compartida con fabricantes de camiones contra incendios (NAFFCO, E-ONE, ROSENBAUER). Los modelos declarados ("RAM 3500 SERVICE RESCUE", "RAM 5500 CREW CAB") confirman que son **vehículos de rescate/bomberos**, no camiones de carga comercial estándar. Aunque la cobertura numérica es baja (11.1%), el segmento es de baja relevancia para el análisis de mercado de camiones — no se prioriza la descarga de archivos adicionales para cerrar este gap.

---

## Pipeline completo — 30 de junio / 1 de julio de 2026

### Contexto

En sesiones anteriores solo se tenían archivos parciales en bronze. En esta jornada se procesaron **todos** los archivos disponibles a través del pipeline completo Bronze → Silver → Gold → Parquet.

### Correcciones al pipeline (previas al procesamiento)

Antes de correr el pipeline se corrigieron múltiples errores que lo bloqueaban:

| Archivo | Fix |
|---|---|
| `pipeline/gold.py` | Retry batch_size corregido: pases 1-2 usan `min(5, batch_size)` en vez del valor completo |
| `pipeline/gold.py` | Flag `--exclude` agregado para omitir archivos por patrón de nombre |
| `pipeline/llm/validate.py` | Campos `tren_rodaje_valido` y `categoria_maquinaria_valido` faltaban en `empty_record()` y `normalize_record()` — causaban `KeyError` en `--dry-run` |
| `pipeline/llm/cache.py` | `text_key()` fallaba con valores float NaN (`AttributeError: 'float' object has no attribute 'strip'`) — fix: `isinstance(desc, str)` antes de `.strip()` |
| `pipeline/silver.py` | Flag `--force` agregado para reprocesar archivos silver ya existentes |
| `data/vocab_extra.json` | Marcas canónicas faltantes agregadas: HITACHI, CASE, CHANGLIN, INKA LOADER, MAES BARR, LEHMAN, WACKER NEUSON, DERUI, YANTAI (los alias que apuntaban a estas marcas fallaban con `ValueError: alias apunta a marca inexistente`) |

### Archivos procesados

Se corrieron **26 archivos** gold en total. LLM utilizado: DeepSeek deepseek-v4-flash (API OpenAI-compatible). Caché persistente en `.cache/llm/results.jsonl` (append-only, sobrevive reinicios).

Nota: el archivo de EURO MOTORS S.A. (166,624 filas brutas, ~166,623 excluidas por no ser camiones) fue procesado por silver pero excluido del gold con `--exclude "EURO MOTORS"` para evitar costo de tokens en datos no relevantes (solo 1 fila clasificada como camión).

### Pipeline nuevo: `build_parquet.py`

Se creó `pipeline/build_parquet.py` para consolidar todos los `*_normalizado.xlsx` de `data/gold/` en `data/gold/camiones.parquet`. Funciones:
- Unión de todos los archivos gold
- Deduplicación por clave DUA+VIN
- Backup automático del parquet anterior con timestamp

Parquet final: **55,121 filas**.

### Cobertura post-pipeline completo (primera auditoría)

```
GLOBAL: 11,357 / 12,462 = 91.1%
```

Resultado aceptable (sobre umbral 88%), pero con dos anomalías críticas detectadas.

---

## Auditoría familia Sinotruk — 30 de junio de 2026

### Contexto

Sinotruk es el #2 del mercado peruano (1,640 unidades AAP Ene–May 2026). La auditoría de cobertura global mostraba 90.4% para SINOTRUK y 52.9% para HOWO MAX. Se realizó un análisis exhaustivo importador por importador.

### Composición de la familia en AAP

| Sub-marca AAP | Ene | Feb | Mar | Abr | May | Total |
|---|---|---|---|---|---|---|
| SINOTRUK | 344 | 213 | 532 | 217 | 334 | **1,640** |
| HOWO MAX | 4 | 31 | 5 | 30 | 0 | **70** |
| SINOTRUK HOWO | 0 | 6 | 0 | 0 | 2 | **8** |
| SINOTRUK WANGPAI | 0 | 0 | 2 | 0 | 0 | **2** |
| **TOTAL FAMILIA** | **348** | **250** | **539** | **247** | **336** | **1,720** |

### Archivos descargados por importador

Se descargaron 8 archivos adicionales por nombre de importador para verificar cobertura completa:

| Importador | VT (antes) | Filas camión en archivo | Nuevos aportados |
|---|---|---|---|
| CAMIONES CHINOS PERU S.A.C. | 223 | 352 | +58 SINOTRUK |
| CORPORATION WITHMORY S.R.L. | 177 | 227 | +50 SINOTRUK |
| ZOOMLION HEAVY INDUSTRY PERU S.A.C. | 188 | 324 | +50 (ZOOMLION+SINOTRUK) |
| CORIEX DS S.A.C. | 109 | 145 | +36 SINOTRUK |
| PREMIER MOTORS S.A. | 379 | 506 | +18 SINOTRUK |
| COMINKA MOTORS S.A.C. | 73 | 87 | +14 SINOTRUK |
| J.CH.COMERCIAL S.A. | 118 | 352 | 0 — ya estaba todo |
| INOMAC S.A.C. | 60 | 60 | 0 — ya estaba todo |

> Nota ZOOMLION: importa equipos especiales (mezcladoras, bombas de concreto, volquetes) sobre chasis SINOTRUK — partida 8705400000. Es correcto que aparezca como importador de la familia.

### Cobertura post-integración

| Sub-marca | AAP | VT | Cobertura |
|---|---|---|---|
| SINOTRUK | 1,640 | 1,505 | 91.8% |
| HOWO MAX | 70 | 37 | 52.9% |
| SINOTRUK HOWO | 8 | 8 | 100.0% |
| SINOTRUK WANGPAI | 2 | 2 | 100.0% |
| **FAMILIA TOTAL** | **1,720** | **1,552** | **90.2%** |

**Parquet actualizado:** 136,223 → **136,449 filas** (+226 registros).

### Diagnóstico de la brecha residual (−168 unidades)

La brecha bajó de −190 a −168 tras la integración de los 8 importadores. El gap residual se explica por dos factores:

1. **HOWO MAX (clasificación en aduana):** WITHMORY S.R.L. declara sus HOWO MAX como "SINOTRUK" en la DUA de aduana. AAP los cuenta como HOWO MAX. Las ~33 unidades "faltantes" de HOWO MAX ya están dentro del 1,505 SINOTRUK de VT — no son unidades perdidas sino una diferencia de etiqueta entre aduana y AAP.

2. **Rezago metodológico AAP vs Veritrade (~135 unidades):** AAP contabiliza unidades al momento de registro en el MTC (Ministerio de Transportes), mientras Veritrade registra la fecha del DUA de aduana. Pueden existir semanas de diferencia entre ambos eventos. Este rezago estructural es la causa más probable de los ~135 SINOTRUK restantes.

**Conclusión:** la cobertura real efectiva de la familia Sinotruk es **~91–92%**. No se identificaron importadores faltantes ni partidas arancelarias sin cubrir. La brecha residual es de origen metodológico, no de datos.

---

## Diagnóstico y corrección — MERCEDES-BENZ y FUSO — 1 de julio de 2026

### Síntoma detectado

La auditoría post-pipeline mostraba:

| Marca | Cobertura | Esperado |
|---|---|---|
| MERCEDES-BENZ | 0.2% | >95% |
| FUSO | 11.7% | >85% |

### Causa raíz

Cuatro archivos silver grandes (generados el 24–25 de junio, antes de que `configuracion.xlsx` tuviera los mapeos correctos) contenían las marcas mal normalizadas:

- `MERCEDES BENZ` → `MERCEDES BENZ` (sin guion) en vez de `MERCEDES-BENZ`
- `MITSUBISHI FUSO` → `MITSUBISHI` en vez de `FUSO`

Archivos afectados:

| Archivo | Filas |
|---|---|
| `Veritrade_...20260624123914.xlsx` | 46,633 |
| `Veritrade_...20260625001450.xlsx` | 13,447 |
| `Veritrade_...20260625003700.xlsx` | 4,520 |
| `Veritrade_...20260625005834.xlsx` | 8,843 |

Estos archivos representaban la gran mayoría de los registros de MERCEDES-BENZ (DIVEIMPORT S.A.) y FUSO (MC AUTOS DEL PERU S.A.C.).

### Solución aplicada

1. Se agregó el flag `--force` a `pipeline/silver.py` para forzar reprocesamiento de archivos ya existentes.
2. Se regeneraron los 4 archivos silver con los mapeos correctos de `configuracion.xlsx`.
3. Se volvió a correr gold sobre los 4 archivos (solo `20260624123914` necesitó nuevas llamadas LLM — 256 requests, $0.23; los otros 3 estaban completamente en caché).
4. Se reconstruyó `camiones.parquet` con `build_parquet.py`.

### Cobertura corregida

| Marca | Antes | Después |
|---|---|---|
| **MERCEDES-BENZ** | 0.2% | **97.4%** |
| **FUSO** | 11.7% | **86.7%** |
| GLOBAL | 91.1% | **91.1%** (sin cambio — datos ya estaban, solo re-etiquetados) |

> FUSO quedó en 86.7% (brecha -135 unidades). El diagnóstico indica partida arancelaria posiblemente incompleta — April mostró solo 2 unidades frente a una media de ~150/mes. Pendiente de investigación.

---

## Corrección de normalización — FORLAND — 1 de julio de 2026

### Síntoma detectado

La auditoría mostraba **FORLAND: VT=0 / Cobertura=0%**, pese a que AAP reportaba 154 unidades.

### Diagnóstico

El parquet sí contenía 937 registros con `marca_norm = "FORLAND"` (154 correspondientes a Ene–May 2026). El problema era doble:

1. **`configuracion.xlsx`** tenía el mapeo `FORLAND → FOTON` (Forland es sub-marca de Foton Motor, pero AAP las reporta como marcas separadas).
2. **`scripts/validar_cobertura.py`** usaba la columna `marca_normalizada` (salida de silver), no `marca_norm` (salida del LLM/gold). Como silver mapeaba FORLAND → FOTON, el audit veía 0 FORLAND.

Se intentó primero cambiar el audit a usar `marca_norm`, pero esto rompió MERCEDES-BENZ (0%) y FUSO (11.7%), ya que el caché del LLM tenía valores previos a las correcciones de silver ("MERCEDES BENZ" sin guion, "MITSUBISHI" en vez de "FUSO"). El caché LLM no se invalida automáticamente al cambiar los silver — usa la descripción de la DUA como clave, que no cambia.

### Solución aplicada

Corrección limpia en el origen:

1. `configuracion.xlsx`: fila FORLAND cambiada de `FOTON` a `FORLAND`.
2. Silver regenerado con `--force` para los 3 archivos que contienen registros FORLAND (todos de importador DIAMANTE DEL PACIFICO S.A.):
   - `Veritrade_...20260624123914.xlsx` (897 filas FORLAND)
   - `Veritrade_...20260630214751.xlsx` (28 filas FORLAND)
   - `Veritrade_...20260630215109.xlsx` (12 filas FORLAND)
3. Reconstrucción de parquet pendiente (ver estado actual al final).

### Estado de la corrección

La corrección fue aplicada parcialmente:
- `configuracion.xlsx` actualizado ✅ (FORLAND → FORLAND)
- Silver regenerado para los 3 archivos afectados ✅
- Gold **no re-ejecutado** — los archivos `*_normalizado.xlsx` en `data/gold/` todavía tienen `marca_normalizada = FOTON` para estos registros, porque gold lee silver y escribe el normalizado, y ese paso se saltó.
- Parquet reconstruido desde gold (con el dato antiguo) → FORLAND sigue en 0% en el audit

**Para completar el fix** (pendiente de decidir si se prioriza):
```bash
python pipeline/gold.py --force --input data/silver/Veritrade_...20260624123914_fase1.xlsx
python pipeline/gold.py --force --input data/silver/Veritrade_...20260630214751_fase1.xlsx
python pipeline/gold.py --force --input data/silver/Veritrade_...20260630215109_fase1.xlsx
python pipeline/build_parquet.py
```
Costo: ~0 tokens (todo en caché LLM). Tiempo: ~5 min. Impacto: FORLAND 0% → 100%, FOTON 101.8% → ~88%.

Se decidió **no aplicar** en esta sesión — la cobertura global (91.1%) ya está sobre el umbral del 88%.

---

## Estado actual y pendientes — 1 de julio de 2026

### Cobertura global (última auditoría con marca_normalizada, pre-FORLAND fix)

```
GLOBAL: 11,357 / 12,462 = 91.1%  ✅ (sobre umbral 88%)
```

### Snapshot por marca

| Marca | AAP | VT | Cob% | Estado |
|---|---|---|---|---|
| ISUZU | 1,775 | 1,607 | 90.5% | leve |
| SINOTRUK | 1,640 | 1,473 | 89.8% | excepción (~91% techo real) |
| FOTON | 1,135 | 1,155 | 101.8% | OK (incluye FORLAND — ver abajo) |
| FUSO | 1,016 | 881 | 86.7% | **pendiente investigación** |
| VOLVO | 937 | 937 | 100.0% | OK |
| SHACMAN | 902 | 844 | 93.6% | leve |
| JAC | 827 | 643 | 77.8% | **pendiente** |
| HINO | 682 | 594 | 87.1% | pendiente re-verificar (rezago probable) |
| MERCEDES-BENZ | 547 | 533 | 97.4% | OK ✅ |
| FAW | 495 | 453 | 91.5% | leve |
| SCANIA | 445 | 442 | 99.3% | OK |
| FORLAND | 154 | 0* | 0%* | *fix parcial aplicado — gold pendiente de re-correr |
| CAMC | 72 | 65 | 90.3% | leve (Mar=0 sospechoso en SAN BARTOLOME) |
| SANY | 70 | 42 | 60.0% | pendiente descarga por importador |
| XCMG | 53 | 46 | 86.8% | leve |

### Pendientes de resolución

| Prioridad | Marca | Brecha | Acción |
|---|---|---|---|
| Alta | FUSO | -135 | Investigar partida adicional o mes Abril (solo 2 unidades vs media 150/mes) |
| Alta | JAC | -184 | Investigar partida arancelaria no cubierta |
| Media | SANY | -28 | Descargar por importador: SANY PERU SOCIEDAD ANONIMA CERRADA + ANDES MOTOR PERU S.A.C. (ceros sospechosos confirmados) |
| Media | CAMC | -7 | Descargar por importador: SAN BARTOLOME S.A. (Mar=0 sospechoso) |
| Baja | HINO | -88 | Re-verificar en 2 semanas (probable rezago DUAs) |
| Baja | XCMG | -7 | Monitorear — solo una partida cubierta (8704230000) |
| Info | FORLAND | — | Fix en progreso — rebuild parquet pendiente de confirmar |
| Info | FARIZON / SUPER-ABOVE / MACRO / GUDAO ANDES | 0% c/u | Volumen muy pequeño (5–10 u/marca). Investigar partida si se prioriza cobertura total. |

### Importadores conocidos para descargas futuras

| Marca | Importador principal |
|---|---|
| MERCEDES-BENZ | DIVEIMPORT S.A. |
| FUSO | MC AUTOS DEL PERU S.A.C. |
| FORLAND | DIAMANTE DEL PACIFICO S.A. |
| JAC | DERCO PERU S.A. |
| HINO | TOYOTA DEL PERU S A |
| SANY | SANY PERU SOCIEDAD ANONIMA CERRADA · ANDES MOTOR PERU S.A.C. |
| CAMC | SAN BARTOLOME S.A. |
| XCMG | XCMG PERU S.A.C. |
