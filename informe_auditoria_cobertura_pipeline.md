# Informe de Auditoría de Cobertura del Pipeline — Marca/Modelo/Categoría
**Fecha de generación:** 2026-07-20
**Dataset:** `data/gold/camiones.parquet` (61,160 filas)
**Script:** `scripts/auditoria_cobertura_pipeline.py`

Pregunta que este informe busca responder: **¿dónde se pierde cobertura de marca/modelo en el pipeline, y es un problema específico de tractocamiones o algo más general?**

No es el mismo informe que `informe_auditoria_cobertura.md` (ese compara volumen Veritrade vs AAP por marca). Este mide cobertura de vocabulario dentro del propio pipeline.

---

## 1. Hallazgo central: la métrica de cobertura de Gold estaba contaminada

`marca_in_vocab`/`modelo_flag` en `camiones.parquet` **no son señal confiable de cobertura**. `pipeline/gold.py` (líneas ~135-147) los hardcodea a `True`/`"reglas_alta"` cuando `confianza=="alta"` en Silver, sin validar nada contra el vocabulario real. Solo 69 de 61,160 filas (0.11%) pasan de verdad por el LLM/validación.

Al revalidar `marca_norm`/`modelo_match` contra el vocabulario real de `configuracion.xlsx` (hojas `marcas`/`modelos`, vía `pipeline.silver.Config`):

| campo | flag viejo (gold) | vocabulario real (antes del fix) |
|---|---|---|
| marca | 61,160 (100%) | 61,133 (99.96%) |
| modelo | 61,160 (100%) | 53,138 (86.9%) |

El flag viejo decía "100% de modelos conocidos". La realidad: **13.1% de los modelos no calzaban con la hoja `modelos`.**

---

## 2. Fix aplicado: `Config._cargar()` no normalizaba la clave de marca al cargar `modelos`

**Causa raíz encontrada:** la hoja `marcas` normaliza `"MERCEDES BENZ"`/`"DAIMLER"` → `"MERCEDES-BENZ"` (con guion). La hoja `modelos` tiene su columna `marca` con el valor `"MERCEDES BENZ"` (sin guion, texto raw). El código armaba `cfg.modelos` usando ese texto raw como clave, sin pasarlo por `marca_map` — así que `cfg.modelos["MERCEDES-BENZ"]` nunca existía, aunque 68 modelos de Mercedes-Benz sí estaban cargados bajo la clave `"MERCEDES BENZ"`. El diccionario no estaba vacío: era invisible para cualquier lookup con la marca ya normalizada.

**Validación de si era representativo o excepcional** (auditando las 77 marcas con al menos una fila con modelo extraído):

| estado | marcas | filas afectadas |
|---|---|---|
| clave exacta OK | 59 | 57,118 |
| mismatch de normalización | 3 | 3,702 |
| sin entrada en `modelos` en absoluto | 15 | 312 |

Del bucket de mismatch, **3,699 de 3,702 filas (99.9%) eran Mercedes-Benz**. Los otros dos casos (`JIN WANG`→`JINWANG`, 1 fila; `"SIN MARCA,"`, 2 filas placeholder) son marginales. **No es un problema sistémico de normalización entre las hojas `marcas` y `modelos`** — es un incidente aislado en una marca de alto volumen.

**Fix** (`pipeline/silver.py::Config._cargar()`, bloque de carga de `modelos`):
```python
m_raw = str(row.get("marca","")).upper().strip()
m = self.marca_map.get(m_raw, m_raw)   # normaliza via el alias de la hoja 'marcas'
```
Reusa el alias que la hoja `marcas` ya conocía — no requirió tocar `configuracion.xlsx`. Verificado: `cfg.modelos["MERCEDES-BENZ"]` y `cfg.modelos["JINWANG"]` ahora resuelven correctamente; `1 passed` en `uv run --extra dev pytest -q` (smoke test), sin regresiones.

**Nota de expectativa vs. resultado:** se esperaba recuperar los 3,699 registros de Mercedes-Benz completos; en la práctica se recuperaron ~1,508, porque el fix corrige el *acceso* a la clave, no la granularidad de los modelos (ver sección 4).

---

## 3. Recalculo — cobertura por categoría (antes → después del fix)

| categoría | total | % fuera de vocab (antes) | % fuera de vocab (después) |
|---|---|---|---|
| SIN CATEGORÍA (nulo) | 22 | 100.0% | 100.0% |
| GRÚA | 51 | 41.2% | 37.3% |
| CHASIS CABINA | 33,969 | 16.9% (5,733) | 14.4% (4,887) |
| HORMIGONERA | 1,844 | 14.6% | 14.6% |
| COMPACTADOR | 236 | 14.4% | 14.4% |
| OTROS | 4,101 | 13.5% | 13.0% |
| CISTERNA | 322 | 9.3% | 9.0% |
| **TRACTOCAMIÓN** | 12,297 | 7.8% (957) | **2.5% (308)** |
| VOLQUETE | 8,316 | 4.9% | 4.7% |
| MEZCLADORA | 2 | 0.0% | 0.0% |

**Hallazgo más relevante para la hipótesis original**: buena parte de lo que parecía "brecha de cobertura en tractocamiones" era en realidad el bug de Mercedes-Benz (sus Actros/Axor tractocamiones). Corregido el bug, TRACTOCAMIÓN pasa de cobertura mediocre (7.8% fuera de vocab) a la **mejor cobertura del dataset** (2.5%, empatada con MEZCLADORA). **La hipótesis de que había un problema específico de tractocamiones no se sostiene con estos datos** — CHASIS CABINA sigue siendo, por lejos, la categoría con más volumen de filas fuera de vocabulario en términos absolutos (4,887).

---

## 4. Recalculo — ranking de marcas y Pareto (antes → después)

| marca | filas fuera de vocab (antes) | filas fuera de vocab (después) |
|---|---|---|
| MERCEDES-BENZ | 3,699 (100% de la marca) | 2,191 (59.2% de la marca) |
| HINO | 2,130 | 2,130 (sin cambio) |
| SINOTRUK | 476 | 468 |
| FOTON | 296 | 296 |
| DONGFENG | — | 206 |

**Total fuera de vocabulario:** 8,022 → **6,483** filas (−1,539, no los ~3,699 que la estimación ingenua hacía esperar).

**Por qué la recuperación fue parcial**: de los 67 modelos únicos que el pipeline extrae para Mercedes-Benz, solo 17 coinciden exacto con el diccionario. Otros 33 matchean si se ignoran sufijos de variante (`/44`, `/48`, códigos de potencia) y espacios — el diccionario tiene el modelo base, el pipeline extrae la variante completa. Los 17 restantes están genuinamente ausentes del diccionario. Ese problema de granularidad **no se corrigió** (fuera de alcance de este fix).

**Nuevo Pareto**: ahora **5 marcas de 66 (7.6%)** concentran el 80%+ del gap restante: MERCEDES-BENZ (33.8%), HINO (66.7% acum.), SINOTRUK (73.9%), FOTON (78.5%), DONGFENG (81.7%). **Hino queda prácticamente empatado con el residuo de Mercedes-Benz** (2,130 vs 2,191 filas) como el objetivo de mayor retorno para una próxima ronda — pendiente de decisión, no ejecutado.

Detalle completo (todas las marcas, no solo el top 5) en `auditoria_cobertura_pipeline.xlsx`, hoja `03b_fuera_vocab_por_marca`.

---

## 5. Hallazgo independiente — duplicidad de vocabularios `Config` vs `Vocab` (NO resuelto, solo documentado)

Existe una **segunda implementación paralela** de "modelos por marca", separada de `pipeline.silver.Config.modelos` (el que se corrigió en este informe):

- **`pipeline.silver.Config.modelos`**: carga desde `configuracion.xlsx` hoja `modelos`, clave normalizada vía `marca_map`. Verificado que es el único consumidor en todo el repo es este mismo script de auditoría — **ningún código de `pipeline/silver.py` ni `pipeline/gold.py` lo consulta para tomar decisiones** durante el procesamiento real de filas.
- **`pipeline.llm.vocab.Vocab.modelos_por_marca`**: carga desde `data/diccionario_maquinaria.xlsx` (`DEFAULT_PATH`, `pipeline/llm/vocab.py:15`) con su propia normalización de clave (`norm_key()`, más agresiva: saca acentos, guiones, espacios, paréntesis). Este es el que consume `pipeline/llm/validate.py:98` en el único camino de validación real (el 0.11% de filas que llegan al LLM).

**`data/diccionario_maquinaria.xlsx` no existe en el repo** — es un nombre de archivo de una arquitectura anterior (referenciado solo en `docs/superpowers/specs/2026-05-30-...md`, previo al rediseño medallion de junio 2026). Se verificó empíricamente si esto deja el vocabulario real vacío:

```
uv run python -m pipeline.llm.vocab
marcas: 257
modelos: 2018
```

**No queda vacío** — `data/vocab_extra.json` (`_merge_extra()`, `vocab.py:168-196`) llena efectivamente el vocabulario completo (257 marcas, 2018 modelos) de forma independiente del archivo base faltante. El sistema funciona hoy solo porque `vocab_extra.json` compensa un archivo base que no existe.

**Riesgo a futuro, no urgente hoy** (impacto real limitado al 0.11% de filas que usan este camino): dos "diccionarios de modelos" con fuentes y reglas de normalización distintas, que pueden divergir sin que nada lo detecte. Queda registrado como hallazgo independiente para una futura consolidación — **no se intentó resolver en esta sesión**.

---

## 6. Conflictos entre fuentes de evidencia (ninguna es ground truth)

**Cambio de pregunta**: las secciones anteriores medían presencia en vocabulario. Esta mide si la categoría **asignada** (`carroceria_normalizada`) coincide con lo que otras fuentes independientes del mismo registro sugieren. Principio explícito: **ninguna fuente es ground truth hasta demostrarlo** — ni la partida arancelaria, ni el campo `CA:` declarado, ni la descripción comercial completa, ni el resultado del propio parser. Las fuentes tampoco son estadísticamente independientes entre sí (el parser deriva parcialmente del mismo texto de `CA:` que se usa como fuente aparte) — el objetivo es detectar **conflictos observables**, no medir independencia estadística.

### 6.1 Las 4 fuentes

1. **Partida arancelaria** → *sugiere* un tipo según la Nomenclatura Arancelaria (Sistema Armonizado, cap. 87): `8701.21/23/29`→TRACTO, `8704.10/60`→VOLQUETE, `8705.10`→GRUA, `8705.40`→HORMIGONERA, `8706.00`→CHASIS_CON_MOTOR, `8704.21/22/23/31/32` (el grueso de las filas)→`NO_DISCRIMINA` (se dividen por peso/motor, no por carrocería). **Este mapeo es en sí mismo una hipótesis auditable de esta sesión, no una verdad** — es una interpretación de la nomenclatura, no el diccionario del pipeline.
2. **`CA:` declarado** (texto crudo) → evidencia encontrada vía escaneo de keywords propio de esta auditoría (no reutiliza `normalizar_carroceria()`), puede devolver 0, 1 o varios tipos.
3. **Descripción comercial completa** → mismo escaneo, sobre todo el texto.
4. **Resultado del parser** (`carroceria_normalizada`) → una fuente más, no el objetivo a validar.

Por fila se calcula `n_evidencias_utilizables` (cuántas de las 4 aportaron algo) y, si hay ≥2, un `índice_consenso` (`k/n`) que **mide solo convergencia, no confianza**: un `4/4` no prueba que la fila esté bien clasificada (las 4 fuentes podrían compartir el mismo error de origen).

### 6.2 Resultado agregado (61,160 filas)

| estado | n_evidencias_utilizables | filas |
|---|---|---|
| compatibles | 2 | 31 |
| compatibles | 3 | 44,051 |
| compatibles | 4 | 12,759 |
| **conflictivas** | 2 | 22 |
| **conflictivas** | 4 | 201 |
| evidencia_insuficiente | 0 | 9 |
| evidencia_insuficiente | 1 | 4,087 |

**93% de las filas (56,841) son compatibles entre las fuentes disponibles.** Solo 223 filas (0.36%) muestran conflicto observable, y 4,096 no tienen suficiente evidencia independiente para evaluar (típicamente: partida `NO_DISCRIMINA` + `CA:`/descripción sin keyword reconocible — queda solo el parser, que no se compara contra nada).

**Qué pares de fuentes chocan más seguido** (dentro de las 223 filas `conflictivas`):

| par de fuentes | filas |
|---|---|
| partida vs descripción | 207 |
| partida vs parser | 207 |
| partida vs CA: | 201 |
| **descripción vs parser** | **10** |

El par más "interno al pipeline" (descripción completa vs. resultado del propio parser) es el menos frecuente — solo 10 filas. Ejemplo real: **`XCMG XGH150`** (9 filas del mismo DUA 042153) — la descripción completa menciona "VOLQUETE" pero el parser asignó `OTROS`. No se investigó si es un accesorio descrito en otro contexto o una miscategorización real — queda como conflicto observable a revisar.

### 6.3 Patrones por modelo — la vista de mayor retorno

En vez de mirar filas sueltas, se buscan **modelos cuya distribución de categoría (según el parser) está repartida entre 2+ categorías sin que ninguna domine** — son anomalías a nivel de patrón, no errores puntuales. 92 modelos tienen más de una categoría asignada; los más parejos (50/50):

| marca | modelo | filas | distribución (parser) |
|---|---|---|---|
| HINO | (C87)-DUTRO 4 TON | 4 | 50% SIN_CATEGORIA, 50% CHASIS CABINA |
| ISUZU | QL1250U4SDZY | 2 | 50% COMPACTADOR, 50% CISTERNA |
| ISUZU | QL1180EQFRCY | 2 | 50% CHASIS CABINA, 50% OTROS |
| SINOTRUK | ZZ1257V3847E1 | 4 | 50% HORMIGONERA, 50% MEZCLADORA |
| SHACMAN | SX5318JSQ6W456C | 4 | 50% GRÚA, 50% CHASIS CABINA |

Ninguno de estos casos se investigó a fondo — la tabla completa (92 modelos) está en la hoja `05_patrones_por_modelo` del Excel, ordenada de más a menos anómala, para decidir cuáles ameritan revisión.

### 6.4 Duplicados en la hoja `carrocerias` (conflicto de reglas confirmado)

| clave | valores en conflicto |
|---|---|
| `CHASIS CABINADO,` | CHASIS CABINA, OTROS |
| `BARANDA,` | BARANDA, OTROS |

Dos claves de la hoja `carrocerias` de `configuracion.xlsx` mapean a más de un valor distinto — la última fila leída gana (`Config._cargar()` itera el Excel en orden). `BARANDA,` es un hallazgo nuevo de esta sesión, no visto antes.

### 6.5 Explícitamente fuera de alcance

No se decidió cuál fuente tiene razón en ningún caso, no se propusieron cambios al parser ni al diccionario, y no se trató ninguna fuente (ni el conocimiento de negocio marca+modelo) como verdad absoluta.

---

## 7. Caracterización de incertidumbre del sistema (no más búsqueda de bugs)

**Cambio de objetivo respecto a la sección 6**: la búsqueda de errores puntuales llegó a rendimiento decreciente — de las 223 filas `conflictivas`, se auditaron a mano las 10 más "internas al pipeline" (descripción vs. parser): **9 eran un hallazgo real acotado** (XCMG "CAMIÓN MINERO" no cubierto por el diccionario de volquetes) y **1 era un artefacto del propio detector** (confunde "chasis cabinado" como plataforma de fabricación con carrocería final). En vez de seguir cazando errores puntuales, esta sección pregunta: **¿dónde toma decisiones el pipeline con alta, parcial o baja convergencia de evidencia — y por qué?** No se decide cuál señal tiene razón; se describen zonas de incertidumbre estructural.

### 7.1 Nivel de convergencia de evidencia (61,160 filas)

Reinterpreta `detectar_conflictos_entre_senales` como niveles de convergencia (no de acierto):

| nivel | filas | qué significa |
|---|---|---|
| `alta_convergencia` | 56,810 | ≥3 fuentes independientes concuerdan sin ninguna en desacuerdo |
| `convergencia_parcial` | 232 | solo 2 fuentes concuerdan, o mayoría converge con una minoría en desacuerdo |
| `baja_convergencia` | 22 | empate 1 contra 1, el mínimo de evidencia y ya en desacuerdo |
| `no_evaluable` | 4,096 | menos de 2 fuentes con evidencia — no es un desacuerdo, es ausencia de evidencia |

Un `4/4` no prueba que la fila esté bien clasificada (las 4 fuentes podrían compartir el mismo error de origen); un nivel bajo no prueba que esté mal.

### 7.2 Evidencia por categoría — dónde el pipeline decide con poca evidencia

| categoría | % no_evaluable | % alta_convergencia |
|---|---|---|
| **OTROS** | **99.6%** | 0.0% |
| SIN_CATEGORIA (nula) | 50.0% | 0.0% |
| TRACTOCAMIÓN | 0.0% | 99.8% |
| VOLQUETE | 0.0% | 99.9% |
| CHASIS CABINA | 0.0% | 99.4% |
| CISTERNA / COMPACTADOR / MEZCLADORA | 0.0% | 100.0% |

**Hipótesis confirmada con datos**: `OTROS` (el cajón de sastre) concentra casi toda su masa en `no_evaluable` — cuando el pipeline asigna OTROS, casi siempre es porque no hay evidencia disponible en ninguna fuente (partida no discrimina, ni CA: ni descripción traen keyword reconocible), no porque haya señales en conflicto. Es una zona de **ausencia de evidencia**, no de error.

### 7.3 Variabilidad estructural por modelo (extiende `05_patrones_por_modelo`)

Se agregó `indice_variabilidad` (entropía de Shannon normalizada, 0=uniforme, 1=repartido parejo) a la tabla de 92 modelos con 2+ categorías. Ejemplo: `HINO (C87)-DUTRO 4 TON` (50% SIN_CATEGORIA / 50% CHASIS CABINA) da `indice_variabilidad=1.000`. No decide si la variabilidad es genuina (plataforma multipropósito) o síntoma de algo más — solo la cuantifica para priorizar revisión.

### 7.4 Uso y generalidad de las reglas de `carrocerias`

Instrumentación de solo lectura (no toca `pipeline/silver.py`) que registra qué clave de `cfg.carroceria_map` decide cada fila:

| clave | → mapea a | usos | % match exacto | % substring | % superstring |
|---|---|---|---|---|---|
| CHASIS CABINA | CHASIS CABINA | 33,674 | 0% | 100% | 0% |
| REMOLCADOR | TRACTOCAMIÓN | 12,269 | 99.7% | 0.3% | 0% |
| VOLQUETE | VOLQUETE | 8,316 | 98.6% | 1.4% | 0% |
| BARANDA | OTROS | 3,237 | 100% | 0% | 0% |
| CHASIS MOTORIZADO, | CHASIS CABINA | 295 | 0% | 0% | **100%** |
| TRACTOR | TRACTOCAMIÓN | 25 | 0% | **100%** | 0% |

**38 de las ~56 claves de la hoja `carrocerias` nunca se usaron con los datos actuales** — candidatas a revisión de utilidad, sin afirmar que sobren.

**Revisión manual de ejemplos reales** (pedida explícitamente para descartar falsos matches antes de cerrar esta caracterización):
- **`CHASIS MOTORIZADO,`** (295 usos, 100% superstring — el texto crudo cabe *dentro* de la clave): el valor crudo real es siempre `"CHASIS MOTORIZADO"` (sin coma); matchea por superstring porque la clave del diccionario tiene una coma sobrante al final (artefacto de formato, no un error de clasificación — el resultado, CHASIS CABINA, es correcto).
- **`TRACTOR`** (25 usos): el valor crudo real es siempre `"TRACTOR TRUCK"`, que contiene la palabra "TRACTOR" — es un match por **substring** (no superstring; la tabla de una versión anterior de este informe lo consignó mal, corregido aquí tras reproducir el algoritmo paso a paso 3 veces). Resultado correcto: TRACTOCAMIÓN.

**No se encontró ningún falso match en los ejemplos revisados.** Ambos casos resuelven a una categoría sensata; el único hallazgo es de formato de la clave (la coma sobrante en `CHASIS MOTORIZADO,`), no un error de clasificación.

### 7.5 Zonas de información indirecta/insuficiente

Se cruzó si `carroceria` (CA: crudo, código explícito) está vacío contra el nivel de convergencia. **Resultado (no asumido, verificado)**: el fallback posicional (`_extraer_posicional`, cuando no hay código CA: explícito) prácticamente no se usa en los datos actuales — solo aparece en las 22 filas `SIN_CATEGORIA`; el resto de categorías tiene 100% de sus filas con código CA: explícito. La hipótesis de que el fallback posicional fuera una fuente relevante de evidencia débil **no se sostiene** — el parser casi siempre trabaja con el dato más directo disponible.

### 7.6 Explícitamente fuera de alcance

No se buscaron más conflictos puntuales, no se decidió cuál señal tiene razón, no se propusieron cambios al parser ni al diccionario. Detalle completo en las hojas `10_nivel_evidencia_por_fila`, `11_evidencia_por_categoria`, `13_uso_reglas_carroceria`, `14_zonas_informacion_insuficiente` del Excel.

---

## 8. Entregables de esta auditoría

1. ✅ Fix en `pipeline/silver.py::Config._cargar()` — reutiliza `marca_map` al cargar la hoja `modelos` (sección 2).
2. ✅ Métricas recalculadas post-fix y nueva priorización (secciones 3-4).
3. ✅ Duplicidad `Config` vs `Vocab` registrada como hallazgo independiente, sin resolver (sección 5).
4. ✅ Conflictos entre fuentes de evidencia detectados y cuantificados, sin decidir cuál tiene razón (sección 6).
5. ✅ Incertidumbre del sistema caracterizada: evidencia por categoría, variabilidad por modelo, uso de reglas, zonas de información insuficiente (sección 7).
6. ✅ Ejemplos reales de match `superstring`/`substring` revisados a mano (sección 7.4) — no se encontró ningún falso match; el único hallazgo es cosmético (coma sobrante en la clave `CHASIS MOTORIZADO,`).

**Con esto se da por cerrada la caracterización de incertidumbre de esta sesión, sin modificar el parser ni el diccionario.**

**Pendiente de decisión, no ejecutado en esta sesión:** completar modelos de Hino (2,130 filas, 13 modelos únicos) y/o Sinotruk (468 filas, 86 modelos únicos) en `configuracion.xlsx`; decidir la convención de granularidad de variante para Mercedes-Benz; consolidar `Config`/`Vocab` en un único vocabulario; revisar los 92 modelos de `05_patrones_por_modelo` y las 38 reglas de `carrocerias` nunca usadas; corregir (o no) las claves duplicadas de `carrocerias` y la coma sobrante en `CHASIS MOTORIZADO,`.
