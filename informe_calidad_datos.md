# Auditoría de Calidad de Datos — Veritrade Imports
**Fecha:** 7 de julio de 2026
**Datasets:** camiones (60,811 filas), maquinaria (20,610 filas)

---

## Resumen ejecutivo

- **Camiones**: 60,811 filas, 51,772 hallazgos marcados en total
- **Maquinaria**: 20,610 filas, 242 hallazgos marcados en total

---

## Camiones — 60,811 filas


### Duplicados exactos (DUA + VIN/Chasis)
- Filas evaluadas: 60,811 (de 60,811 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### VIN duplicado entre distintos DUA
- Filas evaluadas: 60,810 (de 60,811 totales)
- Filas con hallazgo: 33 (0.05%)
- Ejemplos (máx. 5):
  - DUA 008219 | 1 · VIN/Chasis 93KXG30DXRE934738
  - DUA 009536 | 1 · VIN/Chasis 93KXG30DXRE934738
  - DUA 000487 | 1 · VIN/Chasis 93ZE12JMZV8960838
  - DUA 003200 | 1 · VIN/Chasis 93ZE12JMZV8960838
  - DUA 015221 | 1 · VIN/Chasis 9BM958154RB323467


### Formato de VIN (ISO 3779)
- Filas evaluadas: 60,810 (de 60,811 totales)
- Filas con hallazgo: 20 (0.03%)
- Ejemplos (máx. 5):
  - DUA 328910 | 1 · VIN/Chasis JHHUCP1F8RK051605,MOT:N04CWK18518,CHA:JHHUCP1F8RK051605, PUERTAS 02
  - DUA 382024 | 1 · VIN/Chasis JHHUCP1F6RK052235,MOT:N04CWK19056,CHA:JHHUCP1F6RK052235, PUERTAS 2
  - DUA 331010 | 1 · VIN/Chasis JHHUCP1F7RK051594,MOT:N04CWK18508,CHA:JHHUCP1F7RK051594, PUERTAS 2
  - DUA 502205 | 1 · VIN/Chasis JHHUCP1F3SK058175,MOT:N04CWK23615,CHA:JHHUCP1F3SK058175, PUERTAS N.2
  - DUA 103803 | 1 · VIN/Chasis LWLYUAEK1SL003581, EX:


### Coherencia peso neto vs. peso bruto
- Filas evaluadas: 56,911 (de 60,811 totales)
- Filas con hallazgo: 1 (0.00%)
- Ejemplos (máx. 5):
  - DUA 234619 | 1 · VIN/Chasis LZZ5ELND4TN890064 · peso_neto_desc=15720.0


### Rango de año modelo
- Filas evaluadas: 32,308 (de 60,811 totales)
- Rango válido: [1990, 2027]
- Filas con hallazgo: 1 (0.00%)
- Ejemplos (máx. 5):
  - DUA 010931 | 1 · VIN/Chasis JLBFEB91GRKU17006 · anio_modelo=24.0


### Rango de año DUA (derivado de fecha_dua)
- Filas evaluadas: 60,811 (de 60,811 totales)
- Rango válido: [1990, 2027]
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### Rango de cilindrada (cc)
- Filas evaluadas: 60,759 (de 60,811 totales)
- Rango válido: [500, 20000]
- Filas con hallazgo: 97 (0.16%)
- Ejemplos (máx. 5):
  - DUA 278238 | 1 · VIN/Chasis TYBFDKPJHSZ250063 · cilindrada_cc=450.0
  - DUA 450911 | 1 · VIN/Chasis LGDKMCD15PSH23911 · cilindrada_cc=1.0
  - DUA 450911 | 2 · VIN/Chasis LGDKMCD15PSH23912 · cilindrada_cc=1.0
  - DUA 174509 | 1 · VIN/Chasis LGDD16DD1P41K0049 · cilindrada_cc=1.0
  - DUA 174509 | 2 · VIN/Chasis LGDD16DD1P41K0050 · cilindrada_cc=1.0


### Rango de número de cilindros
- Filas evaluadas: 60,637 (de 60,811 totales)
- Rango válido: [1, 16]
- Filas con hallazgo: 50 (0.08%)
- Ejemplos (máx. 5):
  - DUA 001524 | 1 · VIN/Chasis LWLNKAMG7NL048292 · num_cilindros=2991.0
  - DUA 001527 | 1 · VIN/Chasis LWLNKAMG5NL048291 · num_cilindros=2991.0
  - DUA 004215 | 1 · VIN/Chasis LWLNKAMG9NL048293 · num_cilindros=2991.0
  - DUA 000045 | 1 · VIN/Chasis LWU3DM2C9PKM00358 · num_cilindros=2771.0
  - DUA 002558 | 1 · VIN/Chasis LWU2PM2CXNKM04581 · num_cilindros=2771.0


### Rango de número de ejes
- Filas evaluadas: 60,805 (de 60,811 totales)
- Rango válido: [2, 6]
- Filas con hallazgo: 166 (0.27%)
- Ejemplos (máx. 5):
  - DUA 009155 | 1 · VIN/Chasis KMFVA17SPPC362351 · ejes=3375.0
  - DUA 001169 | 1 · VIN/Chasis KMFVA17SPPC362370 · ejes=3375.0
  - DUA 001171 | 1 · VIN/Chasis KMFVA17SPPC362369 · ejes=3375.0
  - DUA 001172 | 1 · VIN/Chasis KMFVA17SPPC362368 · ejes=3375.0
  - DUA 001173 | 1 · VIN/Chasis KMFVA17SPPC362366 · ejes=3375.0


### Rango de largo (mm)
- Filas evaluadas: 60,681 (de 60,811 totales)
- Rango válido: [2000, 20000]
- Filas con hallazgo: 9 (0.01%)
- Ejemplos (máx. 5):
  - DUA 450911 | 1 · VIN/Chasis LGDKMCD15PSH23911 · largo_mm=400.0
  - DUA 450911 | 2 · VIN/Chasis LGDKMCD15PSH23912 · largo_mm=400.0
  - DUA 174509 | 1 · VIN/Chasis LGDD16DD1P41K0049 · largo_mm=400.0
  - DUA 174509 | 2 · VIN/Chasis LGDD16DD1P41K0050 · largo_mm=400.0
  - DUA 128253 | 1 · VIN/Chasis LZGJR4Z69SX005161 · largo_mm=9.0


### Rango de ancho (mm)
- Filas evaluadas: 60,676 (de 60,811 totales)
- Rango válido: [1200, 3200]
- Filas con hallazgo: 50 (0.08%)
- Ejemplos (máx. 5):
  - DUA 450911 | 1 · VIN/Chasis LGDKMCD15PSH23911 · ancho_mm=150.0
  - DUA 450911 | 2 · VIN/Chasis LGDKMCD15PSH23912 · ancho_mm=150.0
  - DUA 174509 | 1 · VIN/Chasis LGDD16DD1P41K0049 · ancho_mm=150.0
  - DUA 174509 | 2 · VIN/Chasis LGDD16DD1P41K0050 · ancho_mm=150.0
  - DUA 003021 | 1 · VIN/Chasis KMTHM014TSD006042 · ancho_mm=3450.0


### Rango de alto (mm)
- Filas evaluadas: 60,637 (de 60,811 totales)
- Rango válido: [1000, 4800]
- Filas con hallazgo: 553 (0.91%)
- Ejemplos (máx. 5):
  - DUA 450911 | 1 · VIN/Chasis LGDKMCD15PSH23911 · alto_mm=150.0
  - DUA 450911 | 2 · VIN/Chasis LGDKMCD15PSH23912 · alto_mm=150.0
  - DUA 174509 | 1 · VIN/Chasis LGDD16DD1P41K0049 · alto_mm=150.0
  - DUA 174509 | 2 · VIN/Chasis LGDD16DD1P41K0050 · alto_mm=150.0
  - DUA 026662 | 1 · VIN/Chasis LFNKRXSM8PAD81541 · alto_mm=3.0


### Descripción sin parsear (texto presente, campos core vacíos)
- Filas evaluadas: 60,811 (de 60,811 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### kg_bruto (columna dura) vs. peso_bruto (extraído de texto)
- Filas evaluadas: 56,954 (de 60,811 totales)
- - Distribución del ratio (peso_bruto_desc/kg_bruto_col): mediana=3.04 · p25=2.68 · p75=3.41 (patrón sistémico esperado ~3x, no todas las filas fuera de banda son error)
- Filas con hallazgo: 86 (0.15%)
- Ejemplos (máx. 5):
  - DUA 470121 | 1 · VIN/Chasis LWU3PM2C9TKM00216 · ratio=9.292682926829269
  - DUA 187727 | 1 · VIN/Chasis LEFAFCG20VHN01248 · ratio=6.6
  - DUA 187727 | 2 · VIN/Chasis LEFAECG23VHN01277 · ratio=7.333333333333333
  - DUA 240394 | 20 · VIN/Chasis MEC0464PCVP081081 · ratio=10.726256983240223
  - DUA 186238 | 10 · VIN/Chasis MEC0574PBRP064725 · ratio=8.156462585034014


### Marca normalizada fuera del vocabulario controlado
- Filas evaluadas: 60,811 (de 60,811 totales)
- Top marcas afectadas: ISUZU(8837), FOTON(5857), SINOTRUK(5072), HINO(3863), MERCEDES-BENZ(3697), FUSO(3568), SCANIA(3554), SHACMAN(3522), JAC(2625), FAW(1375)
- Filas con hallazgo: 50,705 (83.38%)
- Ejemplos (máx. 5):
  - DUA 000103 | 1 · VIN/Chasis LEFAECG28PHN02797
  - DUA 002550 | 1 · VIN/Chasis LEFAECG23PHN03629
  - DUA 005912 | 1 · VIN/Chasis JHHUCP1F1PK048039
  - DUA 005899 | 1 · VIN/Chasis JHHYCP0F6PK027433
  - DUA 005900 | 1 · VIN/Chasis JHHYCP0F4PK027432


### Mojibake de encoding en columnas de texto
- Filas evaluadas: 60,811 (de 60,811 totales)
- Columnas con hallazgo: importador(1)
- Filas con hallazgo: 1 (0.00%)
- Ejemplos (máx. 5):
  - DUA 496248 | 1 · VIN/Chasis LWLGWKFU8PL002964


### CIF menor que FOB
- Filas evaluadas: 60,811 (de 60,811 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


## Resumen Camiones

| Check | Evaluadas | Hallazgos | % |
|---|---|---|---|
| Duplicados exactos (DUA + VIN/Chasis) | 60,811 | 0 | 0.00% |
| VIN duplicado entre distintos DUA | 60,810 | 33 | 0.05% |
| Formato de VIN (ISO 3779) | 60,810 | 20 | 0.03% |
| Coherencia peso neto vs. peso bruto | 56,911 | 1 | 0.00% |
| Rango de año modelo | 32,308 | 1 | 0.00% |
| Rango de año DUA (derivado de fecha_dua) | 60,811 | 0 | 0.00% |
| Rango de cilindrada (cc) | 60,759 | 97 | 0.16% |
| Rango de número de cilindros | 60,637 | 50 | 0.08% |
| Rango de número de ejes | 60,805 | 166 | 0.27% |
| Rango de largo (mm) | 60,681 | 9 | 0.01% |
| Rango de ancho (mm) | 60,676 | 50 | 0.08% |
| Rango de alto (mm) | 60,637 | 553 | 0.91% |
| Descripción sin parsear (texto presente, campos core vacíos) | 60,811 | 0 | 0.00% |
| kg_bruto (columna dura) vs. peso_bruto (extraído de texto) | 56,954 | 86 | 0.15% |
| Marca normalizada fuera del vocabulario controlado | 60,811 | 50,705 | 83.38% |
| Mojibake de encoding en columnas de texto | 60,811 | 1 | 0.00% |
| CIF menor que FOB | 60,811 | 0 | 0.00% |


## Maquinaria — 20,610 filas


### Duplicados exactos (DUA + VIN/Chasis)
- Filas evaluadas: 20,610 (de 20,610 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### VIN duplicado entre distintos DUA
- Filas evaluadas: 9,880 (de 20,610 totales)
- Filas con hallazgo: 24 (0.24%)
- Ejemplos (máx. 5):
  - DUA 370652 | 1 · VIN/Chasis CAT00330LKEL40081
  - DUA 370702 | 1 · VIN/Chasis CAT00330LKEL40081
  - DUA 296284 | 1 · VIN/Chasis CAT00333PTJT10055
  - DUA 296164 | 1 · VIN/Chasis CAT00333PTJT10055
  - DUA 019438 | 1 · VIN/Chasis CAT00340CWFK30134


### Formato de VIN (ISO 3779)
- Filas evaluadas: 9,880 (de 20,610 totales)
- Filas con hallazgo: 81 (0.82%)
- Ejemplos (máx. 5):
  - DUA 000240 | 1 · VIN/Chasis KMTOD074ASC083058
  - DUA 000248 | 1 · VIN/Chasis KMTOD114KSA086028
  - DUA 000249 | 1 · VIN/Chasis KMTOD114PSA086027
  - DUA 000250 | 1 · VIN/Chasis KMTOD074ESC083064
  - DUA 000251 | 1 · VIN/Chasis KMTOD074CSC083065


### Coherencia peso neto vs. peso bruto
- Filas evaluadas: 20,610 (de 20,610 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### Rango de año modelo
- Filas evaluadas: 10,146 (de 20,610 totales)
- Rango válido: [1990, 2027]
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### Rango de año DUA (derivado de fecha_dua)
- Filas evaluadas: 20,610 (de 20,610 totales)
- Rango válido: [1990, 2027]
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### Rango de cilindrada (cc)
- — No aplica (columna no disponible en este dataset) —


### Rango de número de cilindros
- — No aplica (columna no disponible en este dataset) —


### Rango de número de ejes
- — No aplica (columna no disponible en este dataset) —


### Rango de largo (mm)
- — No aplica (columna no disponible en este dataset) —


### Rango de ancho (mm)
- — No aplica (columna no disponible en este dataset) —


### Rango de alto (mm)
- — No aplica (columna no disponible en este dataset) —


### Descripción sin parsear (texto presente, campos core vacíos)
- Filas evaluadas: 20,610 (de 20,610 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### kg_bruto (columna dura) vs. peso_bruto (extraído de texto)
- — No aplica (columna no disponible en este dataset) —


### Marca normalizada fuera del vocabulario controlado
- Filas evaluadas: 20,610 (de 20,610 totales)
- Top marcas afectadas: FREDICH(8), BONELLY(8), ROCKWELL AUTOMATION(6), MONTEFIORI(3), IFM ELECTRONICS(3), TANNER(3), FLEXOFOLD(2), NUOMAN(2), HUANSHENG(2), SINO(2)
- Filas con hallazgo: 133 (0.65%)
- Ejemplos (máx. 5):
  - DUA 246532 | 1 · VIN/Chasis s/d
  - DUA 190467 | 1 · VIN/Chasis s/d
  - DUA 088717 | 1 · VIN/Chasis s/d
  - DUA 088717 | 2 · VIN/Chasis s/d
  - DUA 238022 | 1 · VIN/Chasis s/d


### Mojibake de encoding en columnas de texto
- Filas evaluadas: 20,610 (de 20,610 totales)
- Columnas con hallazgo: _descripcion(4)
- Filas con hallazgo: 4 (0.02%)
- Ejemplos (máx. 5):
  - DUA 476319 | 1 · VIN/Chasis s/d
  - DUA 476319 | 2 · VIN/Chasis s/d
  - DUA 476319 | 3 · VIN/Chasis s/d
  - DUA 476319 | 4 · VIN/Chasis s/d


### CIF menor que FOB
- Filas evaluadas: 20,610 (de 20,610 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


## Resumen Maquinaria

| Check | Evaluadas | Hallazgos | % |
|---|---|---|---|
| Duplicados exactos (DUA + VIN/Chasis) | 20,610 | 0 | 0.00% |
| VIN duplicado entre distintos DUA | 9,880 | 24 | 0.24% |
| Formato de VIN (ISO 3779) | 9,880 | 81 | 0.82% |
| Coherencia peso neto vs. peso bruto | 20,610 | 0 | 0.00% |
| Rango de año modelo | 10,146 | 0 | 0.00% |
| Rango de año DUA (derivado de fecha_dua) | 20,610 | 0 | 0.00% |
| Rango de cilindrada (cc) | 0 | 0 | 0.00% |
| Rango de número de cilindros | 0 | 0 | 0.00% |
| Rango de número de ejes | 0 | 0 | 0.00% |
| Rango de largo (mm) | 0 | 0 | 0.00% |
| Rango de ancho (mm) | 0 | 0 | 0.00% |
| Rango de alto (mm) | 0 | 0 | 0.00% |
| Descripción sin parsear (texto presente, campos core vacíos) | 20,610 | 0 | 0.00% |
| kg_bruto (columna dura) vs. peso_bruto (extraído de texto) | 0 | 0 | 0.00% |
| Marca normalizada fuera del vocabulario controlado | 20,610 | 133 | 0.65% |
| Mojibake de encoding en columnas de texto | 20,610 | 4 | 0.02% |
| CIF menor que FOB | 20,610 | 0 | 0.00% |


---

## Notas de código (fuera de alcance de este script)

Hallazgos incidentales detectados en el pipeline durante el diseño de este análisis. No se
corrigen aquí — quedan documentados para una futura sesión de trabajo:

- **`pipeline/gold.py` lee `confianza_clasificacion`, pero `pipeline/silver.py` escribe
  `confianza`** (nombres distintos) → el atajo de "alta confianza" (que evita mandar la fila
  al LLM) nunca se activa en producción; todas las filas pasan por el LLM aunque silver ya las
  considerara confiables.
- **`pipeline/build_parquet.py` elige `vin` o `chasis` como clave de dedup a nivel de columna
  completa**, no fila por fila (`next(c for c in ("vin","chasis") if c in out.columns)`) — si
  una fila puntual tiene `vin` nulo pero `chasis` con dato, igual se usa la columna `vin` para
  esa fila (porque la columna existe), pudiendo generar una clave de dedup incompleta.
- **`pipeline/gold.py` referencia `r.get("marca")`** en la rama de alta confianza, pero silver
  nunca escribe una columna llamada `marca` (usa `marca_declarada`/`marca_normalizada`) —
  código muerto hoy debido al bug anterior, pero quedaría roto si ese bug se corrige sin
  también arreglar esto.
- **`kg_bruto_col` (columna dura `kg_bruto` del Excel de Veritrade) no es peso bruto — es
  esencialmente una copia de `peso_neto_desc`.** Medido: 62.5% de las filas coinciden dentro de
  ±2% con `peso_neto_desc` (36.5% exacto), mediana del ratio `kg_bruto_col/peso_neto_desc` = 1.00.
  Por eso `kg_bruto_col` difiere ~3x de `peso_bruto_desc` (código `PB:`) — no son dos fuentes de
  peso bruto que discrepan, una de las dos simplemente no es peso bruto. Esto importa porque
  `pipeline/silver.py:578` usa `kg_bruto_col` como *fallback* de `peso_para_atu` cuando falta
  `peso_bruto_desc` — pasa en 3,857 filas (6.3%), donde `categoria_atu` (N1: 2,394 / N2: 1,463) se
  calculó con lo que en realidad es el peso neto, probablemente subclasificando esas filas a una
  categoría ATU más liviana de la que corresponde.

---

## Ejecución — 8 de julio de 2026 16:41

- **Camiones**: 61,044 filas, 1,168 hallazgos marcados en total
- **Maquinaria**: 20,610 filas, 242 hallazgos marcados en total

## Camiones — 61,044 filas


### Duplicados exactos (DUA + VIN/Chasis)
- Filas evaluadas: 61,044 (de 61,044 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### VIN duplicado entre distintos DUA
- Filas evaluadas: 60,703 (de 61,044 totales)
- Filas con hallazgo: 33 (0.05%)
- Ejemplos (máx. 5):
  - DUA 008219 | 1 · VIN/Chasis 93KXG30DXRE934738
  - DUA 009536 | 1 · VIN/Chasis 93KXG30DXRE934738
  - DUA 000487 | 1 · VIN/Chasis 93ZE12JMZV8960838
  - DUA 003200 | 1 · VIN/Chasis 93ZE12JMZV8960838
  - DUA 015221 | 1 · VIN/Chasis 9BM958154RB323467


### Formato de VIN (ISO 3779)
- Filas evaluadas: 60,703 (de 61,044 totales)
- Filas con hallazgo: 20 (0.03%)
- Ejemplos (máx. 5):
  - DUA 328910 | 1 · VIN/Chasis JHHUCP1F8RK051605,MOT:N04CWK18518,CHA:JHHUCP1F8RK051605, PUERTAS 02
  - DUA 382024 | 1 · VIN/Chasis JHHUCP1F6RK052235,MOT:N04CWK19056,CHA:JHHUCP1F6RK052235, PUERTAS 2
  - DUA 331010 | 1 · VIN/Chasis JHHUCP1F7RK051594,MOT:N04CWK18508,CHA:JHHUCP1F7RK051594, PUERTAS 2
  - DUA 502205 | 1 · VIN/Chasis JHHUCP1F3SK058175,MOT:N04CWK23615,CHA:JHHUCP1F3SK058175, PUERTAS N.2
  - DUA 103803 | 1 · VIN/Chasis LWLYUAEK1SL003581, EX:


### Coherencia peso neto vs. peso bruto
- Filas evaluadas: 57,113 (de 61,044 totales)
- Filas con hallazgo: 2 (0.00%)
- Ejemplos (máx. 5):
  - DUA 001876 | 1 · VIN/Chasis s/d · peso_neto_desc=7800.0
  - DUA 234619 | 1 · VIN/Chasis LZZ5ELND4TN890064 · peso_neto_desc=15720.0


### Rango de año modelo
- Filas evaluadas: 32,384 (de 61,044 totales)
- Rango válido: [1990, 2027]
- Filas con hallazgo: 1 (0.00%)
- Ejemplos (máx. 5):
  - DUA 010931 | 1 · VIN/Chasis JLBFEB91GRKU17006 · anio_modelo=24.0


### Rango de año DUA (derivado de fecha_dua)
- Filas evaluadas: 61,044 (de 61,044 totales)
- Rango válido: [1990, 2027]
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### Rango de cilindrada (cc)
- Filas evaluadas: 60,965 (de 61,044 totales)
- Rango válido: [500, 20000]
- Filas con hallazgo: 110 (0.18%)
- Ejemplos (máx. 5):
  - DUA 278238 | 1 · VIN/Chasis TYBFDKPJHSZ250063 · cilindrada_cc=450.0
  - DUA 278238 | 2 · VIN/Chasis TYBFDKPJHSZ250064 · cilindrada_cc=450.0
  - DUA 278238 | 3 · VIN/Chasis TYBFDKPJHSZ250065 · cilindrada_cc=450.0
  - DUA 278238 | 4 · VIN/Chasis TYBFDKPJHSZ250066 · cilindrada_cc=450.0
  - DUA 135529 | 1 · VIN/Chasis . · cilindrada_cc=0.0


### Rango de número de cilindros
- Filas evaluadas: 60,870 (de 61,044 totales)
- Rango válido: [1, 16]
- Filas con hallazgo: 77 (0.13%)
- Ejemplos (máx. 5):
  - DUA 001524 | 1 · VIN/Chasis LWLNKAMG7NL048292 · num_cilindros=2991.0
  - DUA 001527 | 1 · VIN/Chasis LWLNKAMG5NL048291 · num_cilindros=2991.0
  - DUA 004215 | 1 · VIN/Chasis LWLNKAMG9NL048293 · num_cilindros=2991.0
  - DUA 000045 | 1 · VIN/Chasis LWU3DM2C9PKM00358 · num_cilindros=2771.0
  - DUA 002558 | 1 · VIN/Chasis LWU2PM2CXNKM04581 · num_cilindros=2771.0


### Rango de número de ejes
- Filas evaluadas: 61,033 (de 61,044 totales)
- Rango válido: [2, 6]
- Filas con hallazgo: 166 (0.27%)
- Ejemplos (máx. 5):
  - DUA 009155 | 1 · VIN/Chasis KMFVA17SPPC362351 · ejes=3375.0
  - DUA 001169 | 1 · VIN/Chasis KMFVA17SPPC362370 · ejes=3375.0
  - DUA 001171 | 1 · VIN/Chasis KMFVA17SPPC362369 · ejes=3375.0
  - DUA 001172 | 1 · VIN/Chasis KMFVA17SPPC362368 · ejes=3375.0
  - DUA 001173 | 1 · VIN/Chasis KMFVA17SPPC362366 · ejes=3375.0


### Rango de largo (mm)
- Filas evaluadas: 60,743 (de 61,044 totales)
- Rango válido: [2000, 20000]
- Filas con hallazgo: 11 (0.02%)
- Ejemplos (máx. 5):
  - DUA 450911 | 1 · VIN/Chasis LGDKMCD15PSH23911 · largo_mm=400.0
  - DUA 450911 | 2 · VIN/Chasis LGDKMCD15PSH23912 · largo_mm=400.0
  - DUA 174509 | 1 · VIN/Chasis LGDD16DD1P41K0049 · largo_mm=400.0
  - DUA 174509 | 2 · VIN/Chasis LGDD16DD1P41K0050 · largo_mm=400.0
  - DUA 128253 | 1 · VIN/Chasis LZGJR4Z69SX005161 · largo_mm=9.0


### Rango de ancho (mm)
- Filas evaluadas: 60,738 (de 61,044 totales)
- Rango válido: [1200, 3200]
- Filas con hallazgo: 55 (0.09%)
- Ejemplos (máx. 5):
  - DUA 450911 | 1 · VIN/Chasis LGDKMCD15PSH23911 · ancho_mm=150.0
  - DUA 450911 | 2 · VIN/Chasis LGDKMCD15PSH23912 · ancho_mm=150.0
  - DUA 174509 | 1 · VIN/Chasis LGDD16DD1P41K0049 · ancho_mm=150.0
  - DUA 174509 | 2 · VIN/Chasis LGDD16DD1P41K0050 · ancho_mm=150.0
  - DUA 003021 | 1 · VIN/Chasis KMTHM014TSD006042 · ancho_mm=3450.0


### Rango de alto (mm)
- Filas evaluadas: 60,699 (de 61,044 totales)
- Rango válido: [1000, 4800]
- Filas con hallazgo: 556 (0.92%)
- Ejemplos (máx. 5):
  - DUA 450911 | 1 · VIN/Chasis LGDKMCD15PSH23911 · alto_mm=150.0
  - DUA 450911 | 2 · VIN/Chasis LGDKMCD15PSH23912 · alto_mm=150.0
  - DUA 174509 | 1 · VIN/Chasis LGDD16DD1P41K0049 · alto_mm=150.0
  - DUA 174509 | 2 · VIN/Chasis LGDD16DD1P41K0050 · alto_mm=150.0
  - DUA 026662 | 1 · VIN/Chasis LFNKRXSM8PAD81541 · alto_mm=3.0


### Descripción sin parsear (texto presente, campos core vacíos)
- Filas evaluadas: 61,044 (de 61,044 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### kg_bruto (columna dura) vs. peso_bruto (extraído de texto)
- Filas evaluadas: 57,183 (de 61,044 totales)
- - Distribución del ratio (peso_bruto_desc/kg_bruto_col): mediana=3.04 · p25=2.68 · p75=3.41 (patrón sistémico esperado ~3x, no todas las filas fuera de banda son error)
- Filas con hallazgo: 92 (0.16%)
- Ejemplos (máx. 5):
  - DUA 470121 | 1 · VIN/Chasis LWU3PM2C9TKM00216 · ratio=9.292682926829269
  - DUA 187727 | 1 · VIN/Chasis LEFAFCG20VHN01248 · ratio=6.6
  - DUA 187727 | 2 · VIN/Chasis LEFAECG23VHN01277 · ratio=7.333333333333333
  - DUA 240394 | 20 · VIN/Chasis MEC0464PCVP081081 · ratio=10.726256983240223
  - DUA 001876 | 1 · VIN/Chasis s/d · ratio=0.002307692307692308


### Marca normalizada fuera del vocabulario controlado
- Filas evaluadas: 61,044 (de 61,044 totales)
- Top marcas afectadas: 
- Filas con hallazgo: 44 (0.07%)
- Ejemplos (máx. 5):
  - DUA 308893 | 1 · VIN/Chasis L90SL25P7SF052614
  - DUA 308893 | 2 · VIN/Chasis L90SL25P7SF052615
  - DUA 308893 | 3 · VIN/Chasis L90SL25P7SF052616
  - DUA 308893 | 4 · VIN/Chasis L90SL25P7SF052617
  - DUA 554731 | 25 · VIN/Chasis LHSDHZZ38S1003483


### Mojibake de encoding en columnas de texto
- Filas evaluadas: 61,044 (de 61,044 totales)
- Columnas con hallazgo: importador(1)
- Filas con hallazgo: 1 (0.00%)
- Ejemplos (máx. 5):
  - DUA 496248 | 1 · VIN/Chasis LWLGWKFU8PL002964


### CIF menor que FOB
- Filas evaluadas: 61,044 (de 61,044 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


## Resumen Camiones

| Check | Evaluadas | Hallazgos | % |
|---|---|---|---|
| Duplicados exactos (DUA + VIN/Chasis) | 61,044 | 0 | 0.00% |
| VIN duplicado entre distintos DUA | 60,703 | 33 | 0.05% |
| Formato de VIN (ISO 3779) | 60,703 | 20 | 0.03% |
| Coherencia peso neto vs. peso bruto | 57,113 | 2 | 0.00% |
| Rango de año modelo | 32,384 | 1 | 0.00% |
| Rango de año DUA (derivado de fecha_dua) | 61,044 | 0 | 0.00% |
| Rango de cilindrada (cc) | 60,965 | 110 | 0.18% |
| Rango de número de cilindros | 60,870 | 77 | 0.13% |
| Rango de número de ejes | 61,033 | 166 | 0.27% |
| Rango de largo (mm) | 60,743 | 11 | 0.02% |
| Rango de ancho (mm) | 60,738 | 55 | 0.09% |
| Rango de alto (mm) | 60,699 | 556 | 0.92% |
| Descripción sin parsear (texto presente, campos core vacíos) | 61,044 | 0 | 0.00% |
| kg_bruto (columna dura) vs. peso_bruto (extraído de texto) | 57,183 | 92 | 0.16% |
| Marca normalizada fuera del vocabulario controlado | 61,044 | 44 | 0.07% |
| Mojibake de encoding en columnas de texto | 61,044 | 1 | 0.00% |
| CIF menor que FOB | 61,044 | 0 | 0.00% |


## Maquinaria — 20,610 filas


### Duplicados exactos (DUA + VIN/Chasis)
- Filas evaluadas: 20,610 (de 20,610 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### VIN duplicado entre distintos DUA
- Filas evaluadas: 9,880 (de 20,610 totales)
- Filas con hallazgo: 24 (0.24%)
- Ejemplos (máx. 5):
  - DUA 370652 | 1 · VIN/Chasis CAT00330LKEL40081
  - DUA 370702 | 1 · VIN/Chasis CAT00330LKEL40081
  - DUA 296284 | 1 · VIN/Chasis CAT00333PTJT10055
  - DUA 296164 | 1 · VIN/Chasis CAT00333PTJT10055
  - DUA 019438 | 1 · VIN/Chasis CAT00340CWFK30134


### Formato de VIN (ISO 3779)
- Filas evaluadas: 9,880 (de 20,610 totales)
- Filas con hallazgo: 81 (0.82%)
- Ejemplos (máx. 5):
  - DUA 000240 | 1 · VIN/Chasis KMTOD074ASC083058
  - DUA 000248 | 1 · VIN/Chasis KMTOD114KSA086028
  - DUA 000249 | 1 · VIN/Chasis KMTOD114PSA086027
  - DUA 000250 | 1 · VIN/Chasis KMTOD074ESC083064
  - DUA 000251 | 1 · VIN/Chasis KMTOD074CSC083065


### Coherencia peso neto vs. peso bruto
- Filas evaluadas: 20,610 (de 20,610 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### Rango de año modelo
- Filas evaluadas: 10,146 (de 20,610 totales)
- Rango válido: [1990, 2027]
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### Rango de año DUA (derivado de fecha_dua)
- Filas evaluadas: 20,610 (de 20,610 totales)
- Rango válido: [1990, 2027]
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### Rango de cilindrada (cc)
- — No aplica (columna no disponible en este dataset) —


### Rango de número de cilindros
- — No aplica (columna no disponible en este dataset) —


### Rango de número de ejes
- — No aplica (columna no disponible en este dataset) —


### Rango de largo (mm)
- — No aplica (columna no disponible en este dataset) —


### Rango de ancho (mm)
- — No aplica (columna no disponible en este dataset) —


### Rango de alto (mm)
- — No aplica (columna no disponible en este dataset) —


### Descripción sin parsear (texto presente, campos core vacíos)
- Filas evaluadas: 20,610 (de 20,610 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### kg_bruto (columna dura) vs. peso_bruto (extraído de texto)
- — No aplica (columna no disponible en este dataset) —


### Marca normalizada fuera del vocabulario controlado
- Filas evaluadas: 20,610 (de 20,610 totales)
- Top marcas afectadas: FREDICH(8), BONELLY(8), ROCKWELL AUTOMATION(6), MONTEFIORI(3), IFM ELECTRONICS(3), TANNER(3), FLEXOFOLD(2), NUOMAN(2), HUANSHENG(2), SINO(2)
- Filas con hallazgo: 133 (0.65%)
- Ejemplos (máx. 5):
  - DUA 246532 | 1 · VIN/Chasis s/d
  - DUA 190467 | 1 · VIN/Chasis s/d
  - DUA 088717 | 1 · VIN/Chasis s/d
  - DUA 088717 | 2 · VIN/Chasis s/d
  - DUA 238022 | 1 · VIN/Chasis s/d


### Mojibake de encoding en columnas de texto
- Filas evaluadas: 20,610 (de 20,610 totales)
- Columnas con hallazgo: _descripcion(4)
- Filas con hallazgo: 4 (0.02%)
- Ejemplos (máx. 5):
  - DUA 476319 | 1 · VIN/Chasis s/d
  - DUA 476319 | 2 · VIN/Chasis s/d
  - DUA 476319 | 3 · VIN/Chasis s/d
  - DUA 476319 | 4 · VIN/Chasis s/d


### CIF menor que FOB
- Filas evaluadas: 20,610 (de 20,610 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


## Resumen Maquinaria

| Check | Evaluadas | Hallazgos | % |
|---|---|---|---|
| Duplicados exactos (DUA + VIN/Chasis) | 20,610 | 0 | 0.00% |
| VIN duplicado entre distintos DUA | 9,880 | 24 | 0.24% |
| Formato de VIN (ISO 3779) | 9,880 | 81 | 0.82% |
| Coherencia peso neto vs. peso bruto | 20,610 | 0 | 0.00% |
| Rango de año modelo | 10,146 | 0 | 0.00% |
| Rango de año DUA (derivado de fecha_dua) | 20,610 | 0 | 0.00% |
| Rango de cilindrada (cc) | 0 | 0 | 0.00% |
| Rango de número de cilindros | 0 | 0 | 0.00% |
| Rango de número de ejes | 0 | 0 | 0.00% |
| Rango de largo (mm) | 0 | 0 | 0.00% |
| Rango de ancho (mm) | 0 | 0 | 0.00% |
| Rango de alto (mm) | 0 | 0 | 0.00% |
| Descripción sin parsear (texto presente, campos core vacíos) | 20,610 | 0 | 0.00% |
| kg_bruto (columna dura) vs. peso_bruto (extraído de texto) | 0 | 0 | 0.00% |
| Marca normalizada fuera del vocabulario controlado | 20,610 | 133 | 0.65% |
| Mojibake de encoding en columnas de texto | 20,610 | 4 | 0.02% |
| CIF menor que FOB | 20,610 | 0 | 0.00% |


## Notas de código (fuera de alcance de este script)

Hallazgos incidentales detectados en el pipeline durante el diseño de este análisis. No se
corrigen aquí — quedan documentados para una futura sesión de trabajo:

- **`pipeline/gold.py` lee `confianza_clasificacion`, pero `pipeline/silver.py` escribe
  `confianza`** (nombres distintos) → el atajo de "alta confianza" (que evita mandar la fila
  al LLM) nunca se activa en producción; todas las filas pasan por el LLM aunque silver ya las
  considerara confiables.
- **`pipeline/build_parquet.py` elige `vin` o `chasis` como clave de dedup a nivel de columna
  completa**, no fila por fila (`next(c for c in ("vin","chasis") if c in out.columns)`) — si
  una fila puntual tiene `vin` nulo pero `chasis` con dato, igual se usa la columna `vin` para
  esa fila (porque la columna existe), pudiendo generar una clave de dedup incompleta.
- **`pipeline/gold.py` referencia `r.get("marca")`** en la rama de alta confianza, pero silver
  nunca escribe una columna llamada `marca` (usa `marca_declarada`/`marca_normalizada`) —
  código muerto hoy debido al bug anterior, pero quedaría roto si ese bug se corrige sin
  también arreglar esto.
- **`kg_bruto_col` (columna dura `kg_bruto` del Excel de Veritrade) no es peso bruto — es
  esencialmente una copia de `peso_neto_desc`.** Medido: 62.5% de las filas coinciden dentro de
  ±2% con `peso_neto_desc` (36.5% exacto), mediana del ratio `kg_bruto_col/peso_neto_desc` = 1.00.
  Por eso `kg_bruto_col` difiere ~3x de `peso_bruto_desc` (código `PB:`) — no son dos fuentes de
  peso bruto que discrepan, una de las dos simplemente no es peso bruto. Esto importa porque
  `pipeline/silver.py:578` usa `kg_bruto_col` como *fallback* de `peso_para_atu` cuando falta
  `peso_bruto_desc` — pasa en 3,857 filas (6.3%), donde `categoria_atu` (N1: 2,394 / N2: 1,463) se
  calculó con lo que en realidad es el peso neto, probablemente subclasificando esas filas a una
  categoría ATU más liviana de la que corresponde.

---

## Ejecución — 9 de julio de 2026 00:51

- **Camiones**: 61,160 filas, 1,200 hallazgos marcados en total
- **Maquinaria**: 20,610 filas, 242 hallazgos marcados en total

## Camiones — 61,160 filas


### Duplicados exactos (DUA + VIN/Chasis)
- Filas evaluadas: 61,160 (de 61,160 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### VIN duplicado entre distintos DUA
- Filas evaluadas: 60,819 (de 61,160 totales)
- Filas con hallazgo: 35 (0.06%)
- Ejemplos (máx. 5):
  - DUA 008219 | 1 · VIN/Chasis 93KXG30DXRE934738
  - DUA 009536 | 1 · VIN/Chasis 93KXG30DXRE934738
  - DUA 000487 | 1 · VIN/Chasis 93ZE12JMZV8960838
  - DUA 003200 | 1 · VIN/Chasis 93ZE12JMZV8960838
  - DUA 015221 | 1 · VIN/Chasis 9BM958154RB323467


### Formato de VIN (ISO 3779)
- Filas evaluadas: 60,819 (de 61,160 totales)
- Filas con hallazgo: 20 (0.03%)
- Ejemplos (máx. 5):
  - DUA 328910 | 1 · VIN/Chasis JHHUCP1F8RK051605,MOT:N04CWK18518,CHA:JHHUCP1F8RK051605, PUERTAS 02
  - DUA 382024 | 1 · VIN/Chasis JHHUCP1F6RK052235,MOT:N04CWK19056,CHA:JHHUCP1F6RK052235, PUERTAS 2
  - DUA 331010 | 1 · VIN/Chasis JHHUCP1F7RK051594,MOT:N04CWK18508,CHA:JHHUCP1F7RK051594, PUERTAS 2
  - DUA 502205 | 1 · VIN/Chasis JHHUCP1F3SK058175,MOT:N04CWK23615,CHA:JHHUCP1F3SK058175, PUERTAS N.2
  - DUA 103803 | 1 · VIN/Chasis LWLYUAEK1SL003581, EX:


### Coherencia peso neto vs. peso bruto
- Filas evaluadas: 57,229 (de 61,160 totales)
- Filas con hallazgo: 2 (0.00%)
- Ejemplos (máx. 5):
  - DUA 001876 | 1 · VIN/Chasis s/d · peso_neto_desc=7800.0
  - DUA 234619 | 1 · VIN/Chasis LZZ5ELND4TN890064 · peso_neto_desc=15720.0


### Rango de año modelo
- Filas evaluadas: 46,262 (de 61,160 totales)
- Rango válido: [1990, 2027]
- Filas con hallazgo: 1 (0.00%)
- Ejemplos (máx. 5):
  - DUA 010931 | 1 · VIN/Chasis JLBFEB91GRKU17006 · anio_modelo=24.0


### Rango de año DUA (derivado de fecha_dua)
- Filas evaluadas: 61,160 (de 61,160 totales)
- Rango válido: [1990, 2027]
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### Rango de cilindrada (cc)
- Filas evaluadas: 61,081 (de 61,160 totales)
- Rango válido: [500, 20000]
- Filas con hallazgo: 140 (0.23%)
- Ejemplos (máx. 5):
  - DUA 278238 | 1 · VIN/Chasis TYBFDKPJHSZ250063 · cilindrada_cc=450.0
  - DUA 278238 | 2 · VIN/Chasis TYBFDKPJHSZ250064 · cilindrada_cc=450.0
  - DUA 278238 | 3 · VIN/Chasis TYBFDKPJHSZ250065 · cilindrada_cc=450.0
  - DUA 278238 | 4 · VIN/Chasis TYBFDKPJHSZ250066 · cilindrada_cc=450.0
  - DUA 135529 | 1 · VIN/Chasis . · cilindrada_cc=0.0


### Rango de número de cilindros
- Filas evaluadas: 60,986 (de 61,160 totales)
- Rango válido: [1, 16]
- Filas con hallazgo: 77 (0.13%)
- Ejemplos (máx. 5):
  - DUA 001524 | 1 · VIN/Chasis LWLNKAMG7NL048292 · num_cilindros=2991.0
  - DUA 001527 | 1 · VIN/Chasis LWLNKAMG5NL048291 · num_cilindros=2991.0
  - DUA 004215 | 1 · VIN/Chasis LWLNKAMG9NL048293 · num_cilindros=2991.0
  - DUA 000045 | 1 · VIN/Chasis LWU3DM2C9PKM00358 · num_cilindros=2771.0
  - DUA 002558 | 1 · VIN/Chasis LWU2PM2CXNKM04581 · num_cilindros=2771.0


### Rango de número de ejes
- Filas evaluadas: 61,149 (de 61,160 totales)
- Rango válido: [2, 6]
- Filas con hallazgo: 166 (0.27%)
- Ejemplos (máx. 5):
  - DUA 009155 | 1 · VIN/Chasis KMFVA17SPPC362351 · ejes=3375.0
  - DUA 001169 | 1 · VIN/Chasis KMFVA17SPPC362370 · ejes=3375.0
  - DUA 001171 | 1 · VIN/Chasis KMFVA17SPPC362369 · ejes=3375.0
  - DUA 001172 | 1 · VIN/Chasis KMFVA17SPPC362368 · ejes=3375.0
  - DUA 001173 | 1 · VIN/Chasis KMFVA17SPPC362366 · ejes=3375.0


### Rango de largo (mm)
- Filas evaluadas: 60,859 (de 61,160 totales)
- Rango válido: [2000, 20000]
- Filas con hallazgo: 11 (0.02%)
- Ejemplos (máx. 5):
  - DUA 450911 | 1 · VIN/Chasis LGDKMCD15PSH23911 · largo_mm=400.0
  - DUA 450911 | 2 · VIN/Chasis LGDKMCD15PSH23912 · largo_mm=400.0
  - DUA 174509 | 1 · VIN/Chasis LGDD16DD1P41K0049 · largo_mm=400.0
  - DUA 174509 | 2 · VIN/Chasis LGDD16DD1P41K0050 · largo_mm=400.0
  - DUA 128253 | 1 · VIN/Chasis LZGJR4Z69SX005161 · largo_mm=9.0


### Rango de ancho (mm)
- Filas evaluadas: 60,854 (de 61,160 totales)
- Rango válido: [1200, 3200]
- Filas con hallazgo: 55 (0.09%)
- Ejemplos (máx. 5):
  - DUA 450911 | 1 · VIN/Chasis LGDKMCD15PSH23911 · ancho_mm=150.0
  - DUA 450911 | 2 · VIN/Chasis LGDKMCD15PSH23912 · ancho_mm=150.0
  - DUA 174509 | 1 · VIN/Chasis LGDD16DD1P41K0049 · ancho_mm=150.0
  - DUA 174509 | 2 · VIN/Chasis LGDD16DD1P41K0050 · ancho_mm=150.0
  - DUA 003021 | 1 · VIN/Chasis KMTHM014TSD006042 · ancho_mm=3450.0


### Rango de alto (mm)
- Filas evaluadas: 60,815 (de 61,160 totales)
- Rango válido: [1000, 4800]
- Filas con hallazgo: 556 (0.91%)
- Ejemplos (máx. 5):
  - DUA 450911 | 1 · VIN/Chasis LGDKMCD15PSH23911 · alto_mm=150.0
  - DUA 450911 | 2 · VIN/Chasis LGDKMCD15PSH23912 · alto_mm=150.0
  - DUA 174509 | 1 · VIN/Chasis LGDD16DD1P41K0049 · alto_mm=150.0
  - DUA 174509 | 2 · VIN/Chasis LGDD16DD1P41K0050 · alto_mm=150.0
  - DUA 026662 | 1 · VIN/Chasis LFNKRXSM8PAD81541 · alto_mm=3.0


### Descripción sin parsear (texto presente, campos core vacíos)
- Filas evaluadas: 61,160 (de 61,160 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### kg_bruto (columna dura) vs. peso_bruto (extraído de texto)
- Filas evaluadas: 57,299 (de 61,160 totales)
- - Distribución del ratio (peso_bruto_desc/kg_bruto_col): mediana=3.04 · p25=2.68 · p75=3.41 (patrón sistémico esperado ~3x, no todas las filas fuera de banda son error)
- Filas con hallazgo: 92 (0.16%)
- Ejemplos (máx. 5):
  - DUA 470121 | 1 · VIN/Chasis LWU3PM2C9TKM00216 · ratio=9.292682926829269
  - DUA 187727 | 1 · VIN/Chasis LEFAFCG20VHN01248 · ratio=6.6
  - DUA 187727 | 2 · VIN/Chasis LEFAECG23VHN01277 · ratio=7.333333333333333
  - DUA 240394 | 20 · VIN/Chasis MEC0464PCVP081081 · ratio=10.726256983240223
  - DUA 001876 | 1 · VIN/Chasis s/d · ratio=0.002307692307692308


### Marca normalizada fuera del vocabulario controlado
- Filas evaluadas: 61,160 (de 61,160 totales)
- Top marcas afectadas: 
- Filas con hallazgo: 44 (0.07%)
- Ejemplos (máx. 5):
  - DUA 308893 | 1 · VIN/Chasis L90SL25P7SF052614
  - DUA 308893 | 2 · VIN/Chasis L90SL25P7SF052615
  - DUA 308893 | 3 · VIN/Chasis L90SL25P7SF052616
  - DUA 308893 | 4 · VIN/Chasis L90SL25P7SF052617
  - DUA 554731 | 25 · VIN/Chasis LHSDHZZ38S1003483


### Mojibake de encoding en columnas de texto
- Filas evaluadas: 61,160 (de 61,160 totales)
- Columnas con hallazgo: importador(1)
- Filas con hallazgo: 1 (0.00%)
- Ejemplos (máx. 5):
  - DUA 496248 | 1 · VIN/Chasis LWLGWKFU8PL002964


### CIF menor que FOB
- Filas evaluadas: 61,160 (de 61,160 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


## Resumen Camiones

| Check | Evaluadas | Hallazgos | % |
|---|---|---|---|
| Duplicados exactos (DUA + VIN/Chasis) | 61,160 | 0 | 0.00% |
| VIN duplicado entre distintos DUA | 60,819 | 35 | 0.06% |
| Formato de VIN (ISO 3779) | 60,819 | 20 | 0.03% |
| Coherencia peso neto vs. peso bruto | 57,229 | 2 | 0.00% |
| Rango de año modelo | 46,262 | 1 | 0.00% |
| Rango de año DUA (derivado de fecha_dua) | 61,160 | 0 | 0.00% |
| Rango de cilindrada (cc) | 61,081 | 140 | 0.23% |
| Rango de número de cilindros | 60,986 | 77 | 0.13% |
| Rango de número de ejes | 61,149 | 166 | 0.27% |
| Rango de largo (mm) | 60,859 | 11 | 0.02% |
| Rango de ancho (mm) | 60,854 | 55 | 0.09% |
| Rango de alto (mm) | 60,815 | 556 | 0.91% |
| Descripción sin parsear (texto presente, campos core vacíos) | 61,160 | 0 | 0.00% |
| kg_bruto (columna dura) vs. peso_bruto (extraído de texto) | 57,299 | 92 | 0.16% |
| Marca normalizada fuera del vocabulario controlado | 61,160 | 44 | 0.07% |
| Mojibake de encoding en columnas de texto | 61,160 | 1 | 0.00% |
| CIF menor que FOB | 61,160 | 0 | 0.00% |


## Maquinaria — 20,610 filas


### Duplicados exactos (DUA + VIN/Chasis)
- Filas evaluadas: 20,610 (de 20,610 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### VIN duplicado entre distintos DUA
- Filas evaluadas: 9,880 (de 20,610 totales)
- Filas con hallazgo: 24 (0.24%)
- Ejemplos (máx. 5):
  - DUA 370652 | 1 · VIN/Chasis CAT00330LKEL40081
  - DUA 370702 | 1 · VIN/Chasis CAT00330LKEL40081
  - DUA 296284 | 1 · VIN/Chasis CAT00333PTJT10055
  - DUA 296164 | 1 · VIN/Chasis CAT00333PTJT10055
  - DUA 019438 | 1 · VIN/Chasis CAT00340CWFK30134


### Formato de VIN (ISO 3779)
- Filas evaluadas: 9,880 (de 20,610 totales)
- Filas con hallazgo: 81 (0.82%)
- Ejemplos (máx. 5):
  - DUA 000240 | 1 · VIN/Chasis KMTOD074ASC083058
  - DUA 000248 | 1 · VIN/Chasis KMTOD114KSA086028
  - DUA 000249 | 1 · VIN/Chasis KMTOD114PSA086027
  - DUA 000250 | 1 · VIN/Chasis KMTOD074ESC083064
  - DUA 000251 | 1 · VIN/Chasis KMTOD074CSC083065


### Coherencia peso neto vs. peso bruto
- Filas evaluadas: 20,610 (de 20,610 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### Rango de año modelo
- Filas evaluadas: 10,146 (de 20,610 totales)
- Rango válido: [1990, 2027]
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### Rango de año DUA (derivado de fecha_dua)
- Filas evaluadas: 20,610 (de 20,610 totales)
- Rango válido: [1990, 2027]
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### Rango de cilindrada (cc)
- — No aplica (columna no disponible en este dataset) —


### Rango de número de cilindros
- — No aplica (columna no disponible en este dataset) —


### Rango de número de ejes
- — No aplica (columna no disponible en este dataset) —


### Rango de largo (mm)
- — No aplica (columna no disponible en este dataset) —


### Rango de ancho (mm)
- — No aplica (columna no disponible en este dataset) —


### Rango de alto (mm)
- — No aplica (columna no disponible en este dataset) —


### Descripción sin parsear (texto presente, campos core vacíos)
- Filas evaluadas: 20,610 (de 20,610 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### kg_bruto (columna dura) vs. peso_bruto (extraído de texto)
- — No aplica (columna no disponible en este dataset) —


### Marca normalizada fuera del vocabulario controlado
- Filas evaluadas: 20,610 (de 20,610 totales)
- Top marcas afectadas: FREDICH(8), BONELLY(8), ROCKWELL AUTOMATION(6), MONTEFIORI(3), IFM ELECTRONICS(3), TANNER(3), FLEXOFOLD(2), NUOMAN(2), HUANSHENG(2), SINO(2)
- Filas con hallazgo: 133 (0.65%)
- Ejemplos (máx. 5):
  - DUA 246532 | 1 · VIN/Chasis s/d
  - DUA 190467 | 1 · VIN/Chasis s/d
  - DUA 088717 | 1 · VIN/Chasis s/d
  - DUA 088717 | 2 · VIN/Chasis s/d
  - DUA 238022 | 1 · VIN/Chasis s/d


### Mojibake de encoding en columnas de texto
- Filas evaluadas: 20,610 (de 20,610 totales)
- Columnas con hallazgo: _descripcion(4)
- Filas con hallazgo: 4 (0.02%)
- Ejemplos (máx. 5):
  - DUA 476319 | 1 · VIN/Chasis s/d
  - DUA 476319 | 2 · VIN/Chasis s/d
  - DUA 476319 | 3 · VIN/Chasis s/d
  - DUA 476319 | 4 · VIN/Chasis s/d


### CIF menor que FOB
- Filas evaluadas: 20,610 (de 20,610 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


## Resumen Maquinaria

| Check | Evaluadas | Hallazgos | % |
|---|---|---|---|
| Duplicados exactos (DUA + VIN/Chasis) | 20,610 | 0 | 0.00% |
| VIN duplicado entre distintos DUA | 9,880 | 24 | 0.24% |
| Formato de VIN (ISO 3779) | 9,880 | 81 | 0.82% |
| Coherencia peso neto vs. peso bruto | 20,610 | 0 | 0.00% |
| Rango de año modelo | 10,146 | 0 | 0.00% |
| Rango de año DUA (derivado de fecha_dua) | 20,610 | 0 | 0.00% |
| Rango de cilindrada (cc) | 0 | 0 | 0.00% |
| Rango de número de cilindros | 0 | 0 | 0.00% |
| Rango de número de ejes | 0 | 0 | 0.00% |
| Rango de largo (mm) | 0 | 0 | 0.00% |
| Rango de ancho (mm) | 0 | 0 | 0.00% |
| Rango de alto (mm) | 0 | 0 | 0.00% |
| Descripción sin parsear (texto presente, campos core vacíos) | 20,610 | 0 | 0.00% |
| kg_bruto (columna dura) vs. peso_bruto (extraído de texto) | 0 | 0 | 0.00% |
| Marca normalizada fuera del vocabulario controlado | 20,610 | 133 | 0.65% |
| Mojibake de encoding en columnas de texto | 20,610 | 4 | 0.02% |
| CIF menor que FOB | 20,610 | 0 | 0.00% |


## Notas de código (fuera de alcance de este script)

Hallazgos incidentales detectados en el pipeline durante el diseño de este análisis. No se
corrigen aquí — quedan documentados para una futura sesión de trabajo:

- **`pipeline/gold.py` lee `confianza_clasificacion`, pero `pipeline/silver.py` escribe
  `confianza`** (nombres distintos) → el atajo de "alta confianza" (que evita mandar la fila
  al LLM) nunca se activa en producción; todas las filas pasan por el LLM aunque silver ya las
  considerara confiables.
- **`pipeline/build_parquet.py` elige `vin` o `chasis` como clave de dedup a nivel de columna
  completa**, no fila por fila (`next(c for c in ("vin","chasis") if c in out.columns)`) — si
  una fila puntual tiene `vin` nulo pero `chasis` con dato, igual se usa la columna `vin` para
  esa fila (porque la columna existe), pudiendo generar una clave de dedup incompleta.
- **`pipeline/gold.py` referencia `r.get("marca")`** en la rama de alta confianza, pero silver
  nunca escribe una columna llamada `marca` (usa `marca_declarada`/`marca_normalizada`) —
  código muerto hoy debido al bug anterior, pero quedaría roto si ese bug se corrige sin
  también arreglar esto.
- **`kg_bruto_col` (columna dura `kg_bruto` del Excel de Veritrade) no es peso bruto — es
  esencialmente una copia de `peso_neto_desc`.** Medido: 62.5% de las filas coinciden dentro de
  ±2% con `peso_neto_desc` (36.5% exacto), mediana del ratio `kg_bruto_col/peso_neto_desc` = 1.00.
  Por eso `kg_bruto_col` difiere ~3x de `peso_bruto_desc` (código `PB:`) — no son dos fuentes de
  peso bruto que discrepan, una de las dos simplemente no es peso bruto. Esto importa porque
  `pipeline/silver.py:578` usa `kg_bruto_col` como *fallback* de `peso_para_atu` cuando falta
  `peso_bruto_desc` — pasa en 3,857 filas (6.3%), donde `categoria_atu` (N1: 2,394 / N2: 1,463) se
  calculó con lo que en realidad es el peso neto, probablemente subclasificando esas filas a una
  categoría ATU más liviana de la que corresponde.

---

## Ejecución — 9 de julio de 2026 01:08

- **Camiones**: 61,160 filas, 1,711 hallazgos marcados en total
- **Maquinaria**: 20,610 filas, 242 hallazgos marcados en total

## Camiones — 61,160 filas


### Duplicados exactos (DUA + VIN/Chasis)
- Filas evaluadas: 61,160 (de 61,160 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### VIN duplicado entre distintos DUA
- Filas evaluadas: 60,819 (de 61,160 totales)
- Filas con hallazgo: 35 (0.06%)
- Ejemplos (máx. 5):
  - DUA 008219 | 1 · VIN/Chasis 93KXG30DXRE934738
  - DUA 009536 | 1 · VIN/Chasis 93KXG30DXRE934738
  - DUA 000487 | 1 · VIN/Chasis 93ZE12JMZV8960838
  - DUA 003200 | 1 · VIN/Chasis 93ZE12JMZV8960838
  - DUA 015221 | 1 · VIN/Chasis 9BM958154RB323467


### Formato de VIN (ISO 3779)
- Filas evaluadas: 60,819 (de 61,160 totales)
- Filas con hallazgo: 20 (0.03%)
- Ejemplos (máx. 5):
  - DUA 328910 | 1 · VIN/Chasis JHHUCP1F8RK051605,MOT:N04CWK18518,CHA:JHHUCP1F8RK051605, PUERTAS 02
  - DUA 382024 | 1 · VIN/Chasis JHHUCP1F6RK052235,MOT:N04CWK19056,CHA:JHHUCP1F6RK052235, PUERTAS 2
  - DUA 331010 | 1 · VIN/Chasis JHHUCP1F7RK051594,MOT:N04CWK18508,CHA:JHHUCP1F7RK051594, PUERTAS 2
  - DUA 502205 | 1 · VIN/Chasis JHHUCP1F3SK058175,MOT:N04CWK23615,CHA:JHHUCP1F3SK058175, PUERTAS N.2
  - DUA 103803 | 1 · VIN/Chasis LWLYUAEK1SL003581, EX:


### Coherencia peso neto vs. peso bruto
- Filas evaluadas: 57,229 (de 61,160 totales)
- Filas con hallazgo: 2 (0.00%)
- Ejemplos (máx. 5):
  - DUA 001876 | 1 · VIN/Chasis s/d · peso_neto_desc=7800.0
  - DUA 234619 | 1 · VIN/Chasis LZZ5ELND4TN890064 · peso_neto_desc=15720.0


### Rango de año modelo
- Filas evaluadas: 46,262 (de 61,160 totales)
- Rango válido: [1990, 2027]
- Filas con hallazgo: 1 (0.00%)
- Ejemplos (máx. 5):
  - DUA 010931 | 1 · VIN/Chasis JLBFEB91GRKU17006 · anio_modelo=24.0


### Rango de año DUA (derivado de fecha_dua)
- Filas evaluadas: 61,160 (de 61,160 totales)
- Rango válido: [1990, 2027]
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### Rango de cilindrada (cc)
- Filas evaluadas: 61,081 (de 61,160 totales)
- Rango válido: [500, 20000]
- Filas con hallazgo: 140 (0.23%)
- Ejemplos (máx. 5):
  - DUA 278238 | 1 · VIN/Chasis TYBFDKPJHSZ250063 · cilindrada_cc=450.0
  - DUA 278238 | 2 · VIN/Chasis TYBFDKPJHSZ250064 · cilindrada_cc=450.0
  - DUA 278238 | 3 · VIN/Chasis TYBFDKPJHSZ250065 · cilindrada_cc=450.0
  - DUA 278238 | 4 · VIN/Chasis TYBFDKPJHSZ250066 · cilindrada_cc=450.0
  - DUA 135529 | 1 · VIN/Chasis . · cilindrada_cc=0.0


### Rango de número de cilindros
- Filas evaluadas: 60,986 (de 61,160 totales)
- Rango válido: [1, 16]
- Filas con hallazgo: 77 (0.13%)
- Ejemplos (máx. 5):
  - DUA 001524 | 1 · VIN/Chasis LWLNKAMG7NL048292 · num_cilindros=2991.0
  - DUA 001527 | 1 · VIN/Chasis LWLNKAMG5NL048291 · num_cilindros=2991.0
  - DUA 004215 | 1 · VIN/Chasis LWLNKAMG9NL048293 · num_cilindros=2991.0
  - DUA 000045 | 1 · VIN/Chasis LWU3DM2C9PKM00358 · num_cilindros=2771.0
  - DUA 002558 | 1 · VIN/Chasis LWU2PM2CXNKM04581 · num_cilindros=2771.0


### Rango de número de ejes
- Filas evaluadas: 61,149 (de 61,160 totales)
- Rango válido: [2, 6]
- Filas con hallazgo: 166 (0.27%)
- Ejemplos (máx. 5):
  - DUA 009155 | 1 · VIN/Chasis KMFVA17SPPC362351 · ejes=3375.0
  - DUA 001169 | 1 · VIN/Chasis KMFVA17SPPC362370 · ejes=3375.0
  - DUA 001171 | 1 · VIN/Chasis KMFVA17SPPC362369 · ejes=3375.0
  - DUA 001172 | 1 · VIN/Chasis KMFVA17SPPC362368 · ejes=3375.0
  - DUA 001173 | 1 · VIN/Chasis KMFVA17SPPC362366 · ejes=3375.0


### Rango de largo (mm)
- Filas evaluadas: 60,859 (de 61,160 totales)
- Rango válido: [2000, 20000]
- Filas con hallazgo: 11 (0.02%)
- Ejemplos (máx. 5):
  - DUA 450911 | 1 · VIN/Chasis LGDKMCD15PSH23911 · largo_mm=400.0
  - DUA 450911 | 2 · VIN/Chasis LGDKMCD15PSH23912 · largo_mm=400.0
  - DUA 174509 | 1 · VIN/Chasis LGDD16DD1P41K0049 · largo_mm=400.0
  - DUA 174509 | 2 · VIN/Chasis LGDD16DD1P41K0050 · largo_mm=400.0
  - DUA 128253 | 1 · VIN/Chasis LZGJR4Z69SX005161 · largo_mm=9.0


### Rango de ancho (mm)
- Filas evaluadas: 60,854 (de 61,160 totales)
- Rango válido: [1200, 3200]
- Filas con hallazgo: 55 (0.09%)
- Ejemplos (máx. 5):
  - DUA 450911 | 1 · VIN/Chasis LGDKMCD15PSH23911 · ancho_mm=150.0
  - DUA 450911 | 2 · VIN/Chasis LGDKMCD15PSH23912 · ancho_mm=150.0
  - DUA 174509 | 1 · VIN/Chasis LGDD16DD1P41K0049 · ancho_mm=150.0
  - DUA 174509 | 2 · VIN/Chasis LGDD16DD1P41K0050 · ancho_mm=150.0
  - DUA 003021 | 1 · VIN/Chasis KMTHM014TSD006042 · ancho_mm=3450.0


### Rango de alto (mm)
- Filas evaluadas: 60,815 (de 61,160 totales)
- Rango válido: [1000, 4800]
- Filas con hallazgo: 556 (0.91%)
- Ejemplos (máx. 5):
  - DUA 450911 | 1 · VIN/Chasis LGDKMCD15PSH23911 · alto_mm=150.0
  - DUA 450911 | 2 · VIN/Chasis LGDKMCD15PSH23912 · alto_mm=150.0
  - DUA 174509 | 1 · VIN/Chasis LGDD16DD1P41K0049 · alto_mm=150.0
  - DUA 174509 | 2 · VIN/Chasis LGDD16DD1P41K0050 · alto_mm=150.0
  - DUA 026662 | 1 · VIN/Chasis LFNKRXSM8PAD81541 · alto_mm=3.0


### Descripción sin parsear (texto presente, campos core vacíos)
- Filas evaluadas: 61,160 (de 61,160 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### kg_bruto (columna dura) vs. peso_bruto (extraído de texto)
- Filas evaluadas: 57,299 (de 61,160 totales)
- - Distribución del ratio (peso_bruto_desc/kg_bruto_col): mediana=3.04 · p25=2.68 · p75=3.41 (patrón sistémico esperado ~3x, no todas las filas fuera de banda son error)
- Filas con hallazgo: 92 (0.16%)
- Ejemplos (máx. 5):
  - DUA 470121 | 1 · VIN/Chasis LWU3PM2C9TKM00216 · ratio=9.292682926829269
  - DUA 187727 | 1 · VIN/Chasis LEFAFCG20VHN01248 · ratio=6.6
  - DUA 187727 | 2 · VIN/Chasis LEFAECG23VHN01277 · ratio=7.333333333333333
  - DUA 240394 | 20 · VIN/Chasis MEC0464PCVP081081 · ratio=10.726256983240223
  - DUA 001876 | 1 · VIN/Chasis s/d · ratio=0.002307692307692308


### Marca normalizada fuera del vocabulario controlado
- Filas evaluadas: 61,160 (de 61,160 totales)
- Top marcas afectadas: 
- Filas con hallazgo: 44 (0.07%)
- Ejemplos (máx. 5):
  - DUA 308893 | 1 · VIN/Chasis L90SL25P7SF052614
  - DUA 308893 | 2 · VIN/Chasis L90SL25P7SF052615
  - DUA 308893 | 3 · VIN/Chasis L90SL25P7SF052616
  - DUA 308893 | 4 · VIN/Chasis L90SL25P7SF052617
  - DUA 554731 | 25 · VIN/Chasis LHSDHZZ38S1003483


### Mojibake de encoding en columnas de texto
- Filas evaluadas: 61,160 (de 61,160 totales)
- Columnas con hallazgo: importador(1)
- Filas con hallazgo: 1 (0.00%)
- Ejemplos (máx. 5):
  - DUA 496248 | 1 · VIN/Chasis LWLGWKFU8PL002964


### CIF menor que FOB
- Filas evaluadas: 61,160 (de 61,160 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### Carrocería fuera del catálogo conocido (configuracion.xlsx)
- Filas evaluadas: 61,138 (de 61,160 totales)
- Top valores no catalogados: VALORES(24), OTROS USOS ESPECIALES(11), CAMIÓN MINERO DE CUERPO ANC(10), DE PESO TOTAL CON CARGA MÁ(4), SANITARIO(3), GUNITADORA(3), FACTORIA(2), ESPARCIDOR DE ASFALTO(2), - SUPERIOR A 6,2 T, PERO I(1), BOMBONA(1)
- Filas con hallazgo: 68 (0.11%)
- Ejemplos (máx. 5):
  - DUA 096265 | 1 · VIN/Chasis 9535H5TB5RR060983
  - DUA 322485 | 1 · VIN/Chasis 9535H5TBXSR009579
  - DUA 263242 | 1 · VIN/Chasis LWLNKJMG5SL044771
  - DUA 306485 | 1 · VIN/Chasis 9535H5TB1SR031714
  - DUA 306486 | 1 · VIN/Chasis 9535H5TB4SR031965


### Formato inconsistente de anio_modelo (string 'YYYY' vs 'YYYY.0')
- Filas evaluadas: 46,262 (de 61,160 totales)
- Numéricamente inofensivo (pd.to_numeric interpreta ambos formatos igual) -- riesgo solo para filtros por string exacto.
- Filas con hallazgo: 443 (0.96%)
- Ejemplos (máx. 5):
  - DUA 232432 | 1 · VIN/Chasis LZZ1CL3D6TD553227
  - DUA 232432 | 2 · VIN/Chasis LZZ1CL3D7TD554032
  - DUA 232432 | 3 · VIN/Chasis LZZ1CL3D0TD554034
  - DUA 232432 | 4 · VIN/Chasis LZZ1CL3D2TD554035
  - DUA 232432 | 5 · VIN/Chasis LZZ1CL3D4TD554036


## Resumen Camiones

| Check | Evaluadas | Hallazgos | % |
|---|---|---|---|
| Duplicados exactos (DUA + VIN/Chasis) | 61,160 | 0 | 0.00% |
| VIN duplicado entre distintos DUA | 60,819 | 35 | 0.06% |
| Formato de VIN (ISO 3779) | 60,819 | 20 | 0.03% |
| Coherencia peso neto vs. peso bruto | 57,229 | 2 | 0.00% |
| Rango de año modelo | 46,262 | 1 | 0.00% |
| Rango de año DUA (derivado de fecha_dua) | 61,160 | 0 | 0.00% |
| Rango de cilindrada (cc) | 61,081 | 140 | 0.23% |
| Rango de número de cilindros | 60,986 | 77 | 0.13% |
| Rango de número de ejes | 61,149 | 166 | 0.27% |
| Rango de largo (mm) | 60,859 | 11 | 0.02% |
| Rango de ancho (mm) | 60,854 | 55 | 0.09% |
| Rango de alto (mm) | 60,815 | 556 | 0.91% |
| Descripción sin parsear (texto presente, campos core vacíos) | 61,160 | 0 | 0.00% |
| kg_bruto (columna dura) vs. peso_bruto (extraído de texto) | 57,299 | 92 | 0.16% |
| Marca normalizada fuera del vocabulario controlado | 61,160 | 44 | 0.07% |
| Mojibake de encoding en columnas de texto | 61,160 | 1 | 0.00% |
| CIF menor que FOB | 61,160 | 0 | 0.00% |
| Carrocería fuera del catálogo conocido (configuracion.xlsx) | 61,138 | 68 | 0.11% |
| Formato inconsistente de anio_modelo (string 'YYYY' vs 'YYYY.0') | 46,262 | 443 | 0.96% |


## Maquinaria — 20,610 filas


### Duplicados exactos (DUA + VIN/Chasis)
- Filas evaluadas: 20,610 (de 20,610 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### VIN duplicado entre distintos DUA
- Filas evaluadas: 9,880 (de 20,610 totales)
- Filas con hallazgo: 24 (0.24%)
- Ejemplos (máx. 5):
  - DUA 370652 | 1 · VIN/Chasis CAT00330LKEL40081
  - DUA 370702 | 1 · VIN/Chasis CAT00330LKEL40081
  - DUA 296284 | 1 · VIN/Chasis CAT00333PTJT10055
  - DUA 296164 | 1 · VIN/Chasis CAT00333PTJT10055
  - DUA 019438 | 1 · VIN/Chasis CAT00340CWFK30134


### Formato de VIN (ISO 3779)
- Filas evaluadas: 9,880 (de 20,610 totales)
- Filas con hallazgo: 81 (0.82%)
- Ejemplos (máx. 5):
  - DUA 000240 | 1 · VIN/Chasis KMTOD074ASC083058
  - DUA 000248 | 1 · VIN/Chasis KMTOD114KSA086028
  - DUA 000249 | 1 · VIN/Chasis KMTOD114PSA086027
  - DUA 000250 | 1 · VIN/Chasis KMTOD074ESC083064
  - DUA 000251 | 1 · VIN/Chasis KMTOD074CSC083065


### Coherencia peso neto vs. peso bruto
- Filas evaluadas: 20,610 (de 20,610 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### Rango de año modelo
- Filas evaluadas: 10,146 (de 20,610 totales)
- Rango válido: [1990, 2027]
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### Rango de año DUA (derivado de fecha_dua)
- Filas evaluadas: 20,610 (de 20,610 totales)
- Rango válido: [1990, 2027]
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### Rango de cilindrada (cc)
- — No aplica (columna no disponible en este dataset) —


### Rango de número de cilindros
- — No aplica (columna no disponible en este dataset) —


### Rango de número de ejes
- — No aplica (columna no disponible en este dataset) —


### Rango de largo (mm)
- — No aplica (columna no disponible en este dataset) —


### Rango de ancho (mm)
- — No aplica (columna no disponible en este dataset) —


### Rango de alto (mm)
- — No aplica (columna no disponible en este dataset) —


### Descripción sin parsear (texto presente, campos core vacíos)
- Filas evaluadas: 20,610 (de 20,610 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### kg_bruto (columna dura) vs. peso_bruto (extraído de texto)
- — No aplica (columna no disponible en este dataset) —


### Marca normalizada fuera del vocabulario controlado
- Filas evaluadas: 20,610 (de 20,610 totales)
- Top marcas afectadas: FREDICH(8), BONELLY(8), ROCKWELL AUTOMATION(6), MONTEFIORI(3), IFM ELECTRONICS(3), TANNER(3), FLEXOFOLD(2), NUOMAN(2), HUANSHENG(2), SINO(2)
- Filas con hallazgo: 133 (0.65%)
- Ejemplos (máx. 5):
  - DUA 246532 | 1 · VIN/Chasis s/d
  - DUA 190467 | 1 · VIN/Chasis s/d
  - DUA 088717 | 1 · VIN/Chasis s/d
  - DUA 088717 | 2 · VIN/Chasis s/d
  - DUA 238022 | 1 · VIN/Chasis s/d


### Mojibake de encoding en columnas de texto
- Filas evaluadas: 20,610 (de 20,610 totales)
- Columnas con hallazgo: _descripcion(4)
- Filas con hallazgo: 4 (0.02%)
- Ejemplos (máx. 5):
  - DUA 476319 | 1 · VIN/Chasis s/d
  - DUA 476319 | 2 · VIN/Chasis s/d
  - DUA 476319 | 3 · VIN/Chasis s/d
  - DUA 476319 | 4 · VIN/Chasis s/d


### CIF menor que FOB
- Filas evaluadas: 20,610 (de 20,610 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### Carrocería fuera del catálogo conocido (configuracion.xlsx)
- — No aplica (columna no disponible en este dataset) —


### Formato inconsistente de anio_modelo (string 'YYYY' vs 'YYYY.0')
- Filas evaluadas: 10,146 (de 20,610 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


## Resumen Maquinaria

| Check | Evaluadas | Hallazgos | % |
|---|---|---|---|
| Duplicados exactos (DUA + VIN/Chasis) | 20,610 | 0 | 0.00% |
| VIN duplicado entre distintos DUA | 9,880 | 24 | 0.24% |
| Formato de VIN (ISO 3779) | 9,880 | 81 | 0.82% |
| Coherencia peso neto vs. peso bruto | 20,610 | 0 | 0.00% |
| Rango de año modelo | 10,146 | 0 | 0.00% |
| Rango de año DUA (derivado de fecha_dua) | 20,610 | 0 | 0.00% |
| Rango de cilindrada (cc) | 0 | 0 | 0.00% |
| Rango de número de cilindros | 0 | 0 | 0.00% |
| Rango de número de ejes | 0 | 0 | 0.00% |
| Rango de largo (mm) | 0 | 0 | 0.00% |
| Rango de ancho (mm) | 0 | 0 | 0.00% |
| Rango de alto (mm) | 0 | 0 | 0.00% |
| Descripción sin parsear (texto presente, campos core vacíos) | 20,610 | 0 | 0.00% |
| kg_bruto (columna dura) vs. peso_bruto (extraído de texto) | 0 | 0 | 0.00% |
| Marca normalizada fuera del vocabulario controlado | 20,610 | 133 | 0.65% |
| Mojibake de encoding en columnas de texto | 20,610 | 4 | 0.02% |
| CIF menor que FOB | 20,610 | 0 | 0.00% |
| Carrocería fuera del catálogo conocido (configuracion.xlsx) | 0 | 0 | 0.00% |
| Formato inconsistente de anio_modelo (string 'YYYY' vs 'YYYY.0') | 10,146 | 0 | 0.00% |


## Notas de código (fuera de alcance de este script)

Los 4 hallazgos incidentales que este bloque documentaba (mismatch `confianza`/
`confianza_clasificacion` entre silver/gold, dedup por columna completa en vez de fila por fila
en `build_parquet.py`, referencia muerta a `r.get("marca")` en `gold.py`, y `kg_bruto_col` como
fallback de `peso_para_atu`) fueron **verificados como ya corregidos en el código actual**
(re-auditoría 2026-07-09 -- ver `git blame`/commits de julio 2026 para cuándo se corrigió cada
uno). Este bloque queda vacío a propósito -- si una futura auditoría encuentra un hallazgo de
código nuevo fuera de alcance de este script, documentarlo aquí siguiendo el mismo formato.

---

## Ejecución — 9 de julio de 2026 03:07

- **Camiones**: 61,160 filas, 1,643 hallazgos marcados en total
- **Maquinaria**: 20,610 filas, 242 hallazgos marcados en total

## Camiones — 61,160 filas


### Duplicados exactos (DUA + VIN/Chasis)
- Filas evaluadas: 61,160 (de 61,160 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### VIN duplicado entre distintos DUA
- Filas evaluadas: 60,819 (de 61,160 totales)
- Filas con hallazgo: 35 (0.06%)
- Ejemplos (máx. 5):
  - DUA 008219 | 1 · VIN/Chasis 93KXG30DXRE934738
  - DUA 009536 | 1 · VIN/Chasis 93KXG30DXRE934738
  - DUA 000487 | 1 · VIN/Chasis 93ZE12JMZV8960838
  - DUA 003200 | 1 · VIN/Chasis 93ZE12JMZV8960838
  - DUA 015221 | 1 · VIN/Chasis 9BM958154RB323467


### Formato de VIN (ISO 3779)
- Filas evaluadas: 60,819 (de 61,160 totales)
- Filas con hallazgo: 20 (0.03%)
- Ejemplos (máx. 5):
  - DUA 328910 | 1 · VIN/Chasis JHHUCP1F8RK051605,MOT:N04CWK18518,CHA:JHHUCP1F8RK051605, PUERTAS 02
  - DUA 382024 | 1 · VIN/Chasis JHHUCP1F6RK052235,MOT:N04CWK19056,CHA:JHHUCP1F6RK052235, PUERTAS 2
  - DUA 331010 | 1 · VIN/Chasis JHHUCP1F7RK051594,MOT:N04CWK18508,CHA:JHHUCP1F7RK051594, PUERTAS 2
  - DUA 502205 | 1 · VIN/Chasis JHHUCP1F3SK058175,MOT:N04CWK23615,CHA:JHHUCP1F3SK058175, PUERTAS N.2
  - DUA 103803 | 1 · VIN/Chasis LWLYUAEK1SL003581, EX:


### Coherencia peso neto vs. peso bruto
- Filas evaluadas: 57,229 (de 61,160 totales)
- Filas con hallazgo: 2 (0.00%)
- Ejemplos (máx. 5):
  - DUA 001876 | 1 · VIN/Chasis s/d · peso_neto_desc=7800.0
  - DUA 234619 | 1 · VIN/Chasis LZZ5ELND4TN890064 · peso_neto_desc=15720.0


### Rango de año modelo
- Filas evaluadas: 46,262 (de 61,160 totales)
- Rango válido: [1990, 2027]
- Filas con hallazgo: 1 (0.00%)
- Ejemplos (máx. 5):
  - DUA 010931 | 1 · VIN/Chasis JLBFEB91GRKU17006 · anio_modelo=24.0


### Rango de año DUA (derivado de fecha_dua)
- Filas evaluadas: 61,160 (de 61,160 totales)
- Rango válido: [1990, 2027]
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### Rango de cilindrada (cc)
- Filas evaluadas: 61,081 (de 61,160 totales)
- Rango válido: [500, 20000]
- Filas con hallazgo: 140 (0.23%)
- Ejemplos (máx. 5):
  - DUA 278238 | 1 · VIN/Chasis TYBFDKPJHSZ250063 · cilindrada_cc=450.0
  - DUA 278238 | 2 · VIN/Chasis TYBFDKPJHSZ250064 · cilindrada_cc=450.0
  - DUA 278238 | 3 · VIN/Chasis TYBFDKPJHSZ250065 · cilindrada_cc=450.0
  - DUA 278238 | 4 · VIN/Chasis TYBFDKPJHSZ250066 · cilindrada_cc=450.0
  - DUA 135529 | 1 · VIN/Chasis . · cilindrada_cc=0.0


### Rango de número de cilindros
- Filas evaluadas: 60,986 (de 61,160 totales)
- Rango válido: [1, 16]
- Filas con hallazgo: 77 (0.13%)
- Ejemplos (máx. 5):
  - DUA 001524 | 1 · VIN/Chasis LWLNKAMG7NL048292 · num_cilindros=2991.0
  - DUA 001527 | 1 · VIN/Chasis LWLNKAMG5NL048291 · num_cilindros=2991.0
  - DUA 004215 | 1 · VIN/Chasis LWLNKAMG9NL048293 · num_cilindros=2991.0
  - DUA 000045 | 1 · VIN/Chasis LWU3DM2C9PKM00358 · num_cilindros=2771.0
  - DUA 002558 | 1 · VIN/Chasis LWU2PM2CXNKM04581 · num_cilindros=2771.0


### Rango de número de ejes
- Filas evaluadas: 61,149 (de 61,160 totales)
- Rango válido: [2, 6]
- Filas con hallazgo: 166 (0.27%)
- Ejemplos (máx. 5):
  - DUA 009155 | 1 · VIN/Chasis KMFVA17SPPC362351 · ejes=3375.0
  - DUA 001169 | 1 · VIN/Chasis KMFVA17SPPC362370 · ejes=3375.0
  - DUA 001171 | 1 · VIN/Chasis KMFVA17SPPC362369 · ejes=3375.0
  - DUA 001172 | 1 · VIN/Chasis KMFVA17SPPC362368 · ejes=3375.0
  - DUA 001173 | 1 · VIN/Chasis KMFVA17SPPC362366 · ejes=3375.0


### Rango de largo (mm)
- Filas evaluadas: 60,859 (de 61,160 totales)
- Rango válido: [2000, 20000]
- Filas con hallazgo: 11 (0.02%)
- Ejemplos (máx. 5):
  - DUA 450911 | 1 · VIN/Chasis LGDKMCD15PSH23911 · largo_mm=400.0
  - DUA 450911 | 2 · VIN/Chasis LGDKMCD15PSH23912 · largo_mm=400.0
  - DUA 174509 | 1 · VIN/Chasis LGDD16DD1P41K0049 · largo_mm=400.0
  - DUA 174509 | 2 · VIN/Chasis LGDD16DD1P41K0050 · largo_mm=400.0
  - DUA 128253 | 1 · VIN/Chasis LZGJR4Z69SX005161 · largo_mm=9.0


### Rango de ancho (mm)
- Filas evaluadas: 60,854 (de 61,160 totales)
- Rango válido: [1200, 3200]
- Filas con hallazgo: 55 (0.09%)
- Ejemplos (máx. 5):
  - DUA 450911 | 1 · VIN/Chasis LGDKMCD15PSH23911 · ancho_mm=150.0
  - DUA 450911 | 2 · VIN/Chasis LGDKMCD15PSH23912 · ancho_mm=150.0
  - DUA 174509 | 1 · VIN/Chasis LGDD16DD1P41K0049 · ancho_mm=150.0
  - DUA 174509 | 2 · VIN/Chasis LGDD16DD1P41K0050 · ancho_mm=150.0
  - DUA 003021 | 1 · VIN/Chasis KMTHM014TSD006042 · ancho_mm=3450.0


### Rango de alto (mm)
- Filas evaluadas: 60,815 (de 61,160 totales)
- Rango válido: [1000, 4800]
- Filas con hallazgo: 556 (0.91%)
- Ejemplos (máx. 5):
  - DUA 450911 | 1 · VIN/Chasis LGDKMCD15PSH23911 · alto_mm=150.0
  - DUA 450911 | 2 · VIN/Chasis LGDKMCD15PSH23912 · alto_mm=150.0
  - DUA 174509 | 1 · VIN/Chasis LGDD16DD1P41K0049 · alto_mm=150.0
  - DUA 174509 | 2 · VIN/Chasis LGDD16DD1P41K0050 · alto_mm=150.0
  - DUA 026662 | 1 · VIN/Chasis LFNKRXSM8PAD81541 · alto_mm=3.0


### Descripción sin parsear (texto presente, campos core vacíos)
- Filas evaluadas: 61,160 (de 61,160 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### kg_bruto (columna dura) vs. peso_bruto (extraído de texto)
- Filas evaluadas: 57,299 (de 61,160 totales)
- - Distribución del ratio (peso_bruto_desc/kg_bruto_col): mediana=3.04 · p25=2.68 · p75=3.41 (patrón sistémico esperado ~3x, no todas las filas fuera de banda son error)
- Filas con hallazgo: 92 (0.16%)
- Ejemplos (máx. 5):
  - DUA 470121 | 1 · VIN/Chasis LWU3PM2C9TKM00216 · ratio=9.292682926829269
  - DUA 187727 | 1 · VIN/Chasis LEFAFCG20VHN01248 · ratio=6.6
  - DUA 187727 | 2 · VIN/Chasis LEFAECG23VHN01277 · ratio=7.333333333333333
  - DUA 240394 | 20 · VIN/Chasis MEC0464PCVP081081 · ratio=10.726256983240223
  - DUA 001876 | 1 · VIN/Chasis s/d · ratio=0.002307692307692308


### Marca normalizada fuera del vocabulario controlado
- Filas evaluadas: 61,160 (de 61,160 totales)
- Top marcas afectadas: 
- Filas con hallazgo: 44 (0.07%)
- Ejemplos (máx. 5):
  - DUA 308893 | 1 · VIN/Chasis L90SL25P7SF052614
  - DUA 308893 | 2 · VIN/Chasis L90SL25P7SF052615
  - DUA 308893 | 3 · VIN/Chasis L90SL25P7SF052616
  - DUA 308893 | 4 · VIN/Chasis L90SL25P7SF052617
  - DUA 554731 | 25 · VIN/Chasis LHSDHZZ38S1003483


### Mojibake de encoding en columnas de texto
- Filas evaluadas: 61,160 (de 61,160 totales)
- Columnas con hallazgo: importador(1)
- Filas con hallazgo: 1 (0.00%)
- Ejemplos (máx. 5):
  - DUA 496248 | 1 · VIN/Chasis LWLGWKFU8PL002964


### CIF menor que FOB
- Filas evaluadas: 61,160 (de 61,160 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### Carrocería fuera del catálogo conocido (configuracion.xlsx)
- Filas evaluadas: 61,138 (de 61,160 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### Formato inconsistente de anio_modelo (string 'YYYY' vs 'YYYY.0')
- Filas evaluadas: 46,262 (de 61,160 totales)
- Numéricamente inofensivo (pd.to_numeric interpreta ambos formatos igual) -- riesgo solo para filtros por string exacto.
- Filas con hallazgo: 443 (0.96%)
- Ejemplos (máx. 5):
  - DUA 232432 | 1 · VIN/Chasis LZZ1CL3D6TD553227
  - DUA 232432 | 2 · VIN/Chasis LZZ1CL3D7TD554032
  - DUA 232432 | 3 · VIN/Chasis LZZ1CL3D0TD554034
  - DUA 232432 | 4 · VIN/Chasis LZZ1CL3D2TD554035
  - DUA 232432 | 5 · VIN/Chasis LZZ1CL3D4TD554036


## Resumen Camiones

| Check | Evaluadas | Hallazgos | % |
|---|---|---|---|
| Duplicados exactos (DUA + VIN/Chasis) | 61,160 | 0 | 0.00% |
| VIN duplicado entre distintos DUA | 60,819 | 35 | 0.06% |
| Formato de VIN (ISO 3779) | 60,819 | 20 | 0.03% |
| Coherencia peso neto vs. peso bruto | 57,229 | 2 | 0.00% |
| Rango de año modelo | 46,262 | 1 | 0.00% |
| Rango de año DUA (derivado de fecha_dua) | 61,160 | 0 | 0.00% |
| Rango de cilindrada (cc) | 61,081 | 140 | 0.23% |
| Rango de número de cilindros | 60,986 | 77 | 0.13% |
| Rango de número de ejes | 61,149 | 166 | 0.27% |
| Rango de largo (mm) | 60,859 | 11 | 0.02% |
| Rango de ancho (mm) | 60,854 | 55 | 0.09% |
| Rango de alto (mm) | 60,815 | 556 | 0.91% |
| Descripción sin parsear (texto presente, campos core vacíos) | 61,160 | 0 | 0.00% |
| kg_bruto (columna dura) vs. peso_bruto (extraído de texto) | 57,299 | 92 | 0.16% |
| Marca normalizada fuera del vocabulario controlado | 61,160 | 44 | 0.07% |
| Mojibake de encoding en columnas de texto | 61,160 | 1 | 0.00% |
| CIF menor que FOB | 61,160 | 0 | 0.00% |
| Carrocería fuera del catálogo conocido (configuracion.xlsx) | 61,138 | 0 | 0.00% |
| Formato inconsistente de anio_modelo (string 'YYYY' vs 'YYYY.0') | 46,262 | 443 | 0.96% |


## Maquinaria — 20,610 filas


### Duplicados exactos (DUA + VIN/Chasis)
- Filas evaluadas: 20,610 (de 20,610 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### VIN duplicado entre distintos DUA
- Filas evaluadas: 9,880 (de 20,610 totales)
- Filas con hallazgo: 24 (0.24%)
- Ejemplos (máx. 5):
  - DUA 370652 | 1 · VIN/Chasis CAT00330LKEL40081
  - DUA 370702 | 1 · VIN/Chasis CAT00330LKEL40081
  - DUA 296284 | 1 · VIN/Chasis CAT00333PTJT10055
  - DUA 296164 | 1 · VIN/Chasis CAT00333PTJT10055
  - DUA 019438 | 1 · VIN/Chasis CAT00340CWFK30134


### Formato de VIN (ISO 3779)
- Filas evaluadas: 9,880 (de 20,610 totales)
- Filas con hallazgo: 81 (0.82%)
- Ejemplos (máx. 5):
  - DUA 000240 | 1 · VIN/Chasis KMTOD074ASC083058
  - DUA 000248 | 1 · VIN/Chasis KMTOD114KSA086028
  - DUA 000249 | 1 · VIN/Chasis KMTOD114PSA086027
  - DUA 000250 | 1 · VIN/Chasis KMTOD074ESC083064
  - DUA 000251 | 1 · VIN/Chasis KMTOD074CSC083065


### Coherencia peso neto vs. peso bruto
- Filas evaluadas: 20,610 (de 20,610 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### Rango de año modelo
- Filas evaluadas: 10,146 (de 20,610 totales)
- Rango válido: [1990, 2027]
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### Rango de año DUA (derivado de fecha_dua)
- Filas evaluadas: 20,610 (de 20,610 totales)
- Rango válido: [1990, 2027]
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### Rango de cilindrada (cc)
- — No aplica (columna no disponible en este dataset) —


### Rango de número de cilindros
- — No aplica (columna no disponible en este dataset) —


### Rango de número de ejes
- — No aplica (columna no disponible en este dataset) —


### Rango de largo (mm)
- — No aplica (columna no disponible en este dataset) —


### Rango de ancho (mm)
- — No aplica (columna no disponible en este dataset) —


### Rango de alto (mm)
- — No aplica (columna no disponible en este dataset) —


### Descripción sin parsear (texto presente, campos core vacíos)
- Filas evaluadas: 20,610 (de 20,610 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### kg_bruto (columna dura) vs. peso_bruto (extraído de texto)
- — No aplica (columna no disponible en este dataset) —


### Marca normalizada fuera del vocabulario controlado
- Filas evaluadas: 20,610 (de 20,610 totales)
- Top marcas afectadas: FREDICH(8), BONELLY(8), ROCKWELL AUTOMATION(6), MONTEFIORI(3), IFM ELECTRONICS(3), TANNER(3), FLEXOFOLD(2), NUOMAN(2), HUANSHENG(2), SINO(2)
- Filas con hallazgo: 133 (0.65%)
- Ejemplos (máx. 5):
  - DUA 246532 | 1 · VIN/Chasis s/d
  - DUA 190467 | 1 · VIN/Chasis s/d
  - DUA 088717 | 1 · VIN/Chasis s/d
  - DUA 088717 | 2 · VIN/Chasis s/d
  - DUA 238022 | 1 · VIN/Chasis s/d


### Mojibake de encoding en columnas de texto
- Filas evaluadas: 20,610 (de 20,610 totales)
- Columnas con hallazgo: _descripcion(4)
- Filas con hallazgo: 4 (0.02%)
- Ejemplos (máx. 5):
  - DUA 476319 | 1 · VIN/Chasis s/d
  - DUA 476319 | 2 · VIN/Chasis s/d
  - DUA 476319 | 3 · VIN/Chasis s/d
  - DUA 476319 | 4 · VIN/Chasis s/d


### CIF menor que FOB
- Filas evaluadas: 20,610 (de 20,610 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### Carrocería fuera del catálogo conocido (configuracion.xlsx)
- — No aplica (columna no disponible en este dataset) —


### Formato inconsistente de anio_modelo (string 'YYYY' vs 'YYYY.0')
- Filas evaluadas: 10,146 (de 20,610 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


## Resumen Maquinaria

| Check | Evaluadas | Hallazgos | % |
|---|---|---|---|
| Duplicados exactos (DUA + VIN/Chasis) | 20,610 | 0 | 0.00% |
| VIN duplicado entre distintos DUA | 9,880 | 24 | 0.24% |
| Formato de VIN (ISO 3779) | 9,880 | 81 | 0.82% |
| Coherencia peso neto vs. peso bruto | 20,610 | 0 | 0.00% |
| Rango de año modelo | 10,146 | 0 | 0.00% |
| Rango de año DUA (derivado de fecha_dua) | 20,610 | 0 | 0.00% |
| Rango de cilindrada (cc) | 0 | 0 | 0.00% |
| Rango de número de cilindros | 0 | 0 | 0.00% |
| Rango de número de ejes | 0 | 0 | 0.00% |
| Rango de largo (mm) | 0 | 0 | 0.00% |
| Rango de ancho (mm) | 0 | 0 | 0.00% |
| Rango de alto (mm) | 0 | 0 | 0.00% |
| Descripción sin parsear (texto presente, campos core vacíos) | 20,610 | 0 | 0.00% |
| kg_bruto (columna dura) vs. peso_bruto (extraído de texto) | 0 | 0 | 0.00% |
| Marca normalizada fuera del vocabulario controlado | 20,610 | 133 | 0.65% |
| Mojibake de encoding en columnas de texto | 20,610 | 4 | 0.02% |
| CIF menor que FOB | 20,610 | 0 | 0.00% |
| Carrocería fuera del catálogo conocido (configuracion.xlsx) | 0 | 0 | 0.00% |
| Formato inconsistente de anio_modelo (string 'YYYY' vs 'YYYY.0') | 10,146 | 0 | 0.00% |


## Notas de código (fuera de alcance de este script)

Los 4 hallazgos incidentales que este bloque documentaba (mismatch `confianza`/
`confianza_clasificacion` entre silver/gold, dedup por columna completa en vez de fila por fila
en `build_parquet.py`, referencia muerta a `r.get("marca")` en `gold.py`, y `kg_bruto_col` como
fallback de `peso_para_atu`) fueron **verificados como ya corregidos en el código actual**
(re-auditoría 2026-07-09 -- ver `git blame`/commits de julio 2026 para cuándo se corrigió cada
uno). Este bloque queda vacío a propósito -- si una futura auditoría encuentra un hallazgo de
código nuevo fuera de alcance de este script, documentarlo aquí siguiendo el mismo formato.

---

## Ejecución — 9 de julio de 2026 03:29

- **Camiones**: 61,160 filas, 1,639 hallazgos marcados en total
- **Maquinaria**: 20,610 filas, 242 hallazgos marcados en total

## Camiones — 61,160 filas


### Duplicados exactos (DUA + VIN/Chasis)
- Filas evaluadas: 61,160 (de 61,160 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### VIN duplicado entre distintos DUA
- Filas evaluadas: 60,819 (de 61,160 totales)
- Filas con hallazgo: 35 (0.06%)
- Ejemplos (máx. 5):
  - DUA 008219 | 1 · VIN/Chasis 93KXG30DXRE934738
  - DUA 009536 | 1 · VIN/Chasis 93KXG30DXRE934738
  - DUA 000487 | 1 · VIN/Chasis 93ZE12JMZV8960838
  - DUA 003200 | 1 · VIN/Chasis 93ZE12JMZV8960838
  - DUA 015221 | 1 · VIN/Chasis 9BM958154RB323467


### Formato de VIN (ISO 3779)
- Filas evaluadas: 60,819 (de 61,160 totales)
- Filas con hallazgo: 20 (0.03%)
- Ejemplos (máx. 5):
  - DUA 328910 | 1 · VIN/Chasis JHHUCP1F8RK051605,MOT:N04CWK18518,CHA:JHHUCP1F8RK051605, PUERTAS 02
  - DUA 382024 | 1 · VIN/Chasis JHHUCP1F6RK052235,MOT:N04CWK19056,CHA:JHHUCP1F6RK052235, PUERTAS 2
  - DUA 331010 | 1 · VIN/Chasis JHHUCP1F7RK051594,MOT:N04CWK18508,CHA:JHHUCP1F7RK051594, PUERTAS 2
  - DUA 502205 | 1 · VIN/Chasis JHHUCP1F3SK058175,MOT:N04CWK23615,CHA:JHHUCP1F3SK058175, PUERTAS N.2
  - DUA 103803 | 1 · VIN/Chasis LWLYUAEK1SL003581, EX:


### Coherencia peso neto vs. peso bruto
- Filas evaluadas: 57,229 (de 61,160 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### Rango de año modelo
- Filas evaluadas: 46,262 (de 61,160 totales)
- Rango válido: [1990, 2027]
- Filas con hallazgo: 1 (0.00%)
- Ejemplos (máx. 5):
  - DUA 010931 | 1 · VIN/Chasis JLBFEB91GRKU17006 · anio_modelo=24.0


### Rango de año DUA (derivado de fecha_dua)
- Filas evaluadas: 61,160 (de 61,160 totales)
- Rango válido: [1990, 2027]
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### Rango de cilindrada (cc)
- Filas evaluadas: 61,081 (de 61,160 totales)
- Rango válido: [500, 20000]
- Filas con hallazgo: 140 (0.23%)
- Ejemplos (máx. 5):
  - DUA 278238 | 1 · VIN/Chasis TYBFDKPJHSZ250063 · cilindrada_cc=450.0
  - DUA 278238 | 2 · VIN/Chasis TYBFDKPJHSZ250064 · cilindrada_cc=450.0
  - DUA 278238 | 3 · VIN/Chasis TYBFDKPJHSZ250065 · cilindrada_cc=450.0
  - DUA 278238 | 4 · VIN/Chasis TYBFDKPJHSZ250066 · cilindrada_cc=450.0
  - DUA 135529 | 1 · VIN/Chasis . · cilindrada_cc=0.0


### Rango de número de cilindros
- Filas evaluadas: 60,986 (de 61,160 totales)
- Rango válido: [1, 16]
- Filas con hallazgo: 77 (0.13%)
- Ejemplos (máx. 5):
  - DUA 001524 | 1 · VIN/Chasis LWLNKAMG7NL048292 · num_cilindros=2991.0
  - DUA 001527 | 1 · VIN/Chasis LWLNKAMG5NL048291 · num_cilindros=2991.0
  - DUA 004215 | 1 · VIN/Chasis LWLNKAMG9NL048293 · num_cilindros=2991.0
  - DUA 000045 | 1 · VIN/Chasis LWU3DM2C9PKM00358 · num_cilindros=2771.0
  - DUA 002558 | 1 · VIN/Chasis LWU2PM2CXNKM04581 · num_cilindros=2771.0


### Rango de número de ejes
- Filas evaluadas: 61,149 (de 61,160 totales)
- Rango válido: [2, 6]
- Filas con hallazgo: 166 (0.27%)
- Ejemplos (máx. 5):
  - DUA 009155 | 1 · VIN/Chasis KMFVA17SPPC362351 · ejes=3375.0
  - DUA 001169 | 1 · VIN/Chasis KMFVA17SPPC362370 · ejes=3375.0
  - DUA 001171 | 1 · VIN/Chasis KMFVA17SPPC362369 · ejes=3375.0
  - DUA 001172 | 1 · VIN/Chasis KMFVA17SPPC362368 · ejes=3375.0
  - DUA 001173 | 1 · VIN/Chasis KMFVA17SPPC362366 · ejes=3375.0


### Rango de largo (mm)
- Filas evaluadas: 60,859 (de 61,160 totales)
- Rango válido: [2000, 20000]
- Filas con hallazgo: 11 (0.02%)
- Ejemplos (máx. 5):
  - DUA 450911 | 1 · VIN/Chasis LGDKMCD15PSH23911 · largo_mm=400.0
  - DUA 450911 | 2 · VIN/Chasis LGDKMCD15PSH23912 · largo_mm=400.0
  - DUA 174509 | 1 · VIN/Chasis LGDD16DD1P41K0049 · largo_mm=400.0
  - DUA 174509 | 2 · VIN/Chasis LGDD16DD1P41K0050 · largo_mm=400.0
  - DUA 128253 | 1 · VIN/Chasis LZGJR4Z69SX005161 · largo_mm=9.0


### Rango de ancho (mm)
- Filas evaluadas: 60,854 (de 61,160 totales)
- Rango válido: [1200, 3200]
- Filas con hallazgo: 55 (0.09%)
- Ejemplos (máx. 5):
  - DUA 450911 | 1 · VIN/Chasis LGDKMCD15PSH23911 · ancho_mm=150.0
  - DUA 450911 | 2 · VIN/Chasis LGDKMCD15PSH23912 · ancho_mm=150.0
  - DUA 174509 | 1 · VIN/Chasis LGDD16DD1P41K0049 · ancho_mm=150.0
  - DUA 174509 | 2 · VIN/Chasis LGDD16DD1P41K0050 · ancho_mm=150.0
  - DUA 003021 | 1 · VIN/Chasis KMTHM014TSD006042 · ancho_mm=3450.0


### Rango de alto (mm)
- Filas evaluadas: 60,815 (de 61,160 totales)
- Rango válido: [1000, 4800]
- Filas con hallazgo: 556 (0.91%)
- Ejemplos (máx. 5):
  - DUA 450911 | 1 · VIN/Chasis LGDKMCD15PSH23911 · alto_mm=150.0
  - DUA 450911 | 2 · VIN/Chasis LGDKMCD15PSH23912 · alto_mm=150.0
  - DUA 174509 | 1 · VIN/Chasis LGDD16DD1P41K0049 · alto_mm=150.0
  - DUA 174509 | 2 · VIN/Chasis LGDD16DD1P41K0050 · alto_mm=150.0
  - DUA 026662 | 1 · VIN/Chasis LFNKRXSM8PAD81541 · alto_mm=3.0


### Descripción sin parsear (texto presente, campos core vacíos)
- Filas evaluadas: 61,160 (de 61,160 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### kg_bruto (columna dura) vs. peso_bruto (extraído de texto)
- Filas evaluadas: 57,299 (de 61,160 totales)
- - Distribución del ratio (peso_bruto_desc/kg_bruto_col): mediana=3.04 · p25=2.68 · p75=3.41 (patrón sistémico esperado ~3x, no todas las filas fuera de banda son error)
- Filas con hallazgo: 90 (0.16%)
- Ejemplos (máx. 5):
  - DUA 470121 | 1 · VIN/Chasis LWU3PM2C9TKM00216 · ratio=9.292682926829269
  - DUA 187727 | 1 · VIN/Chasis LEFAFCG20VHN01248 · ratio=6.6
  - DUA 187727 | 2 · VIN/Chasis LEFAECG23VHN01277 · ratio=7.333333333333333
  - DUA 240394 | 20 · VIN/Chasis MEC0464PCVP081081 · ratio=10.726256983240223
  - DUA 135529 | 1 · VIN/Chasis . · ratio=0.0


### Marca normalizada fuera del vocabulario controlado
- Filas evaluadas: 61,160 (de 61,160 totales)
- Top marcas afectadas: 
- Filas con hallazgo: 44 (0.07%)
- Ejemplos (máx. 5):
  - DUA 308893 | 1 · VIN/Chasis L90SL25P7SF052614
  - DUA 308893 | 2 · VIN/Chasis L90SL25P7SF052615
  - DUA 308893 | 3 · VIN/Chasis L90SL25P7SF052616
  - DUA 308893 | 4 · VIN/Chasis L90SL25P7SF052617
  - DUA 554731 | 25 · VIN/Chasis LHSDHZZ38S1003483


### Mojibake de encoding en columnas de texto
- Filas evaluadas: 61,160 (de 61,160 totales)
- Columnas con hallazgo: importador(1)
- Filas con hallazgo: 1 (0.00%)
- Ejemplos (máx. 5):
  - DUA 496248 | 1 · VIN/Chasis LWLGWKFU8PL002964


### CIF menor que FOB
- Filas evaluadas: 61,160 (de 61,160 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### Carrocería fuera del catálogo conocido (configuracion.xlsx)
- Filas evaluadas: 61,138 (de 61,160 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### Formato inconsistente de anio_modelo (string 'YYYY' vs 'YYYY.0')
- Filas evaluadas: 46,262 (de 61,160 totales)
- Numéricamente inofensivo (pd.to_numeric interpreta ambos formatos igual) -- riesgo solo para filtros por string exacto.
- Filas con hallazgo: 443 (0.96%)
- Ejemplos (máx. 5):
  - DUA 232432 | 1 · VIN/Chasis LZZ1CL3D6TD553227
  - DUA 232432 | 2 · VIN/Chasis LZZ1CL3D7TD554032
  - DUA 232432 | 3 · VIN/Chasis LZZ1CL3D0TD554034
  - DUA 232432 | 4 · VIN/Chasis LZZ1CL3D2TD554035
  - DUA 232432 | 5 · VIN/Chasis LZZ1CL3D4TD554036


## Resumen Camiones

| Check | Evaluadas | Hallazgos | % |
|---|---|---|---|
| Duplicados exactos (DUA + VIN/Chasis) | 61,160 | 0 | 0.00% |
| VIN duplicado entre distintos DUA | 60,819 | 35 | 0.06% |
| Formato de VIN (ISO 3779) | 60,819 | 20 | 0.03% |
| Coherencia peso neto vs. peso bruto | 57,229 | 0 | 0.00% |
| Rango de año modelo | 46,262 | 1 | 0.00% |
| Rango de año DUA (derivado de fecha_dua) | 61,160 | 0 | 0.00% |
| Rango de cilindrada (cc) | 61,081 | 140 | 0.23% |
| Rango de número de cilindros | 60,986 | 77 | 0.13% |
| Rango de número de ejes | 61,149 | 166 | 0.27% |
| Rango de largo (mm) | 60,859 | 11 | 0.02% |
| Rango de ancho (mm) | 60,854 | 55 | 0.09% |
| Rango de alto (mm) | 60,815 | 556 | 0.91% |
| Descripción sin parsear (texto presente, campos core vacíos) | 61,160 | 0 | 0.00% |
| kg_bruto (columna dura) vs. peso_bruto (extraído de texto) | 57,299 | 90 | 0.16% |
| Marca normalizada fuera del vocabulario controlado | 61,160 | 44 | 0.07% |
| Mojibake de encoding en columnas de texto | 61,160 | 1 | 0.00% |
| CIF menor que FOB | 61,160 | 0 | 0.00% |
| Carrocería fuera del catálogo conocido (configuracion.xlsx) | 61,138 | 0 | 0.00% |
| Formato inconsistente de anio_modelo (string 'YYYY' vs 'YYYY.0') | 46,262 | 443 | 0.96% |


## Maquinaria — 20,610 filas


### Duplicados exactos (DUA + VIN/Chasis)
- Filas evaluadas: 20,610 (de 20,610 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### VIN duplicado entre distintos DUA
- Filas evaluadas: 9,880 (de 20,610 totales)
- Filas con hallazgo: 24 (0.24%)
- Ejemplos (máx. 5):
  - DUA 370652 | 1 · VIN/Chasis CAT00330LKEL40081
  - DUA 370702 | 1 · VIN/Chasis CAT00330LKEL40081
  - DUA 296284 | 1 · VIN/Chasis CAT00333PTJT10055
  - DUA 296164 | 1 · VIN/Chasis CAT00333PTJT10055
  - DUA 019438 | 1 · VIN/Chasis CAT00340CWFK30134


### Formato de VIN (ISO 3779)
- Filas evaluadas: 9,880 (de 20,610 totales)
- Filas con hallazgo: 81 (0.82%)
- Ejemplos (máx. 5):
  - DUA 000240 | 1 · VIN/Chasis KMTOD074ASC083058
  - DUA 000248 | 1 · VIN/Chasis KMTOD114KSA086028
  - DUA 000249 | 1 · VIN/Chasis KMTOD114PSA086027
  - DUA 000250 | 1 · VIN/Chasis KMTOD074ESC083064
  - DUA 000251 | 1 · VIN/Chasis KMTOD074CSC083065


### Coherencia peso neto vs. peso bruto
- Filas evaluadas: 20,610 (de 20,610 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### Rango de año modelo
- Filas evaluadas: 10,146 (de 20,610 totales)
- Rango válido: [1990, 2027]
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### Rango de año DUA (derivado de fecha_dua)
- Filas evaluadas: 20,610 (de 20,610 totales)
- Rango válido: [1990, 2027]
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### Rango de cilindrada (cc)
- — No aplica (columna no disponible en este dataset) —


### Rango de número de cilindros
- — No aplica (columna no disponible en este dataset) —


### Rango de número de ejes
- — No aplica (columna no disponible en este dataset) —


### Rango de largo (mm)
- — No aplica (columna no disponible en este dataset) —


### Rango de ancho (mm)
- — No aplica (columna no disponible en este dataset) —


### Rango de alto (mm)
- — No aplica (columna no disponible en este dataset) —


### Descripción sin parsear (texto presente, campos core vacíos)
- Filas evaluadas: 20,610 (de 20,610 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### kg_bruto (columna dura) vs. peso_bruto (extraído de texto)
- — No aplica (columna no disponible en este dataset) —


### Marca normalizada fuera del vocabulario controlado
- Filas evaluadas: 20,610 (de 20,610 totales)
- Top marcas afectadas: FREDICH(8), BONELLY(8), ROCKWELL AUTOMATION(6), MONTEFIORI(3), IFM ELECTRONICS(3), TANNER(3), FLEXOFOLD(2), NUOMAN(2), HUANSHENG(2), SINO(2)
- Filas con hallazgo: 133 (0.65%)
- Ejemplos (máx. 5):
  - DUA 246532 | 1 · VIN/Chasis s/d
  - DUA 190467 | 1 · VIN/Chasis s/d
  - DUA 088717 | 1 · VIN/Chasis s/d
  - DUA 088717 | 2 · VIN/Chasis s/d
  - DUA 238022 | 1 · VIN/Chasis s/d


### Mojibake de encoding en columnas de texto
- Filas evaluadas: 20,610 (de 20,610 totales)
- Columnas con hallazgo: _descripcion(4)
- Filas con hallazgo: 4 (0.02%)
- Ejemplos (máx. 5):
  - DUA 476319 | 1 · VIN/Chasis s/d
  - DUA 476319 | 2 · VIN/Chasis s/d
  - DUA 476319 | 3 · VIN/Chasis s/d
  - DUA 476319 | 4 · VIN/Chasis s/d


### CIF menor que FOB
- Filas evaluadas: 20,610 (de 20,610 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


### Carrocería fuera del catálogo conocido (configuracion.xlsx)
- — No aplica (columna no disponible en este dataset) —


### Formato inconsistente de anio_modelo (string 'YYYY' vs 'YYYY.0')
- Filas evaluadas: 10,146 (de 20,610 totales)
- Filas con hallazgo: 0 (0.00%)
- Sin hallazgos


## Resumen Maquinaria

| Check | Evaluadas | Hallazgos | % |
|---|---|---|---|
| Duplicados exactos (DUA + VIN/Chasis) | 20,610 | 0 | 0.00% |
| VIN duplicado entre distintos DUA | 9,880 | 24 | 0.24% |
| Formato de VIN (ISO 3779) | 9,880 | 81 | 0.82% |
| Coherencia peso neto vs. peso bruto | 20,610 | 0 | 0.00% |
| Rango de año modelo | 10,146 | 0 | 0.00% |
| Rango de año DUA (derivado de fecha_dua) | 20,610 | 0 | 0.00% |
| Rango de cilindrada (cc) | 0 | 0 | 0.00% |
| Rango de número de cilindros | 0 | 0 | 0.00% |
| Rango de número de ejes | 0 | 0 | 0.00% |
| Rango de largo (mm) | 0 | 0 | 0.00% |
| Rango de ancho (mm) | 0 | 0 | 0.00% |
| Rango de alto (mm) | 0 | 0 | 0.00% |
| Descripción sin parsear (texto presente, campos core vacíos) | 20,610 | 0 | 0.00% |
| kg_bruto (columna dura) vs. peso_bruto (extraído de texto) | 0 | 0 | 0.00% |
| Marca normalizada fuera del vocabulario controlado | 20,610 | 133 | 0.65% |
| Mojibake de encoding en columnas de texto | 20,610 | 4 | 0.02% |
| CIF menor que FOB | 20,610 | 0 | 0.00% |
| Carrocería fuera del catálogo conocido (configuracion.xlsx) | 0 | 0 | 0.00% |
| Formato inconsistente de anio_modelo (string 'YYYY' vs 'YYYY.0') | 10,146 | 0 | 0.00% |


## Notas de código (fuera de alcance de este script)

Los 4 hallazgos incidentales que este bloque documentaba (mismatch `confianza`/
`confianza_clasificacion` entre silver/gold, dedup por columna completa en vez de fila por fila
en `build_parquet.py`, referencia muerta a `r.get("marca")` en `gold.py`, y `kg_bruto_col` como
fallback de `peso_para_atu`) fueron **verificados como ya corregidos en el código actual**
(re-auditoría 2026-07-09 -- ver `git blame`/commits de julio 2026 para cuándo se corrigió cada
uno). Este bloque queda vacío a propósito -- si una futura auditoría encuentra un hallazgo de
código nuevo fuera de alcance de este script, documentarlo aquí siguiendo el mismo formato.
