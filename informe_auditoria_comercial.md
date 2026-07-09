# Informe de Auditoría de Datos y Calidad Comercial — Camiones
**Fecha de generación:** 2026-07-08 18:06
**Dataset:** `data/gold/camiones.parquet` (61,160 filas)

Pregunta que este informe busca responder: **¿puedo confiar en los indicadores comerciales (participación de mercado, rankings, tendencias por carrocería) que salen de este archivo?**

---
## 1. Totales de Control (Integridad Absoluta)

**Origen real de los datos: bronze de Veritrade (no hay un extracto SUNAT independiente contra el cual comparar) — el control es bronze → silver → gold → consolidado final, dentro de nuestro propio pipeline.**

                               Etapa  Registros  CIF Total USD  Peso Bruto Total KG
     Bronze (crudo, incl. excluidos)     341433   6.468272e+09         2.237091e+09
        Válidas post-silver (a gold)      94153   5.647908e+09         2.166723e+09
Consolidado final (camiones.parquet)      61160   3.808181e+09         1.359575e+09

**Unidades finales: 61,160** (1 fila = 1 unidad, deduplicado por DUA+VIN/chasis).

Reducción bronze → final: **82.1%** (excluidas por partida no-camión, vans, duplicados, exclusiones de negocio como pickups — ver `scripts/auditar_embudo_importador.py` para el detalle por importador/razón.)

**[ALERTA] 3,861 filas (6.31%)** tienen `peso_bruto_desc` vacío pero `kg_bruto_col` presente. El dashboard (`pages/2_Camiones.py::MAPEO_COLS`) usa `kg_bruto_col` como fallback para calcular `segmento_peso` ('Categoría Withmory') — pero `kg_bruto_col` es en realidad **peso neto**, no bruto (confirmado 2026-07-08, ver `informe_calidad_datos.md`). Estas filas probablemente están en un segmento de peso más bajo del que les corresponde. No corregido en el dashboard todavía — el pipeline (`categoria_atu`) ya no usa este fallback desde hoy.

**[ALERTA] Bug confirmado en `pages/2_Camiones.py::clasificar_segmento()`:** cuando `pb` llega como `NaN` (no `None`, no string vacío — un float `NaN` real, que es exactamente cómo llegan los 3,861 valores faltantes desde el parquet), `float(pb)` NO lanza excepción y `NaN <= 0` da `False` en Python, así que la fila cae sin querer en el último `return "PESADO"` de la función — **el segmento más pesado**, no "SIN DATO". Confirmado y reproducido el 2026-07-08. Este informe usa una copia corregida de la función (ver comentario en el código fuente); el dashboard en producción sigue con el bug.


---

## 2. Cobertura Comercial por Atributo (Completitud)

                                                   Atributo  Cobertura %
                                                      Marca        100.0
                                                     Modelo        100.0
                                                 Carrocería        100.0
                           Categoría (bucket de carrocería)        100.0
Categoría Withmory (segmento de peso, solo peso_bruto_desc)         93.7

**[ALERTA] Categoría Withmory está en 93.7%, por debajo del umbral de 95%.** Un vacío de este tamaño distorsiona los rankings de participación de mercado basados en categoría withmory.


---

## 3. Participación de "No Clasificado" (Riesgo de Sesgo)

### Categoría (bucket de carrocería)

    Categoría  Unidades
CHASIS CABINA     33969
 TRACTOCAMIÓN     12297
     VOLQUETE      8316
        OTROS      4359
  HORMIGONERA      1846
     CISTERNA       322
         GRÚA        51

*Nota: "OTROS" mezcla carrocerías genuinamente distintas (ej. cisternas atípicas) con filas donde `carroceria_normalizada` estaba vacío — no es un "no clasificado" puro. Vacíos reales dentro de OTROS: 22.*


### Categoría Withmory (segmento de peso)

Categoría Withmory  Unidades
             LDT 2     16121
            PESADO     15724
       SEMI PESADO     10431
             MDT 3      7842
             MDT 1      5109
          SIN DATO      3866
             MDT 2      1367
             LDT 1       700

6.3% sin clasificar en Categoría Withmory — dentro de rango aceptable pero vale la pena revisar (ver sección 4).


---

## 4. Top 100 Descripciones sin Clasificar (Guía de Acción del Parser)

Total filas sin `peso_bruto_desc`: **3,866**

- Código `PB:` **ausente** de la descripción (dato no capturado en origen): 3,861 (99.9%)
- Código `PB:` **presente** pero no se pudo extraer un valor válido (posible bug del parser, o descripción truncada antes del valor): 5 (0.1%)

### Top marcas afectadas (dentro de las que no tienen PB: en absoluto)

marca_declarada  unidades_sin_PB_en_descripcion
           HINO                            3853
           KAMA                               2
           LTMG                               2
         NORMET                               2
         TOYOTA                               1
AUTOHORMIGONERA                               1

Resolver las 6 marcas de arriba cubre la mayoría de este bucket — si concentran >80% del total, confirma la heurística del 80/20 del enunciado original.


---

## 5. Ranking contra la Realidad (Validación Manual y Consistencia)

### Top 20 combinaciones Marca + Modelo

marca_norm     modelo_match  unidades
      FUSO           CANTER      2832
     ISUZU NPR75L-KL5VAYPEN      2745
     VOLVO        FMX 6X4 R      2001
     VOLVO         FH 6X4 T      1902
      HINO            DUTRO      1712
     VOLVO        FMX 8X4 R      1438
  SINOTRUK    ZZ3257V364HE1      1389
      HINO         STANDARD      1290
     ISUZU NPR75L-HL5VAYPEN      1200
     ISUZU              FRR      1104
     VOLVO         FM 6X4 T       973
     ISUZU NQR90L-MQ5VAYPEN       944
     FOTON   BJ4269SNFKB-A4       923
     ISUZU    FVR34UL-QDPES       826
   SHACMAN     SX325862354C       690
     ISUZU    FTR34UL-PDPEN       609
     ISUZU NPS75L-HJ5VAYPEN       602
    SCANIA        R500 A6X4       590
  SINOTRUK    ZZ3168G3415E1       568
   SHACMAN     SX331862306C       496

### Combinaciones Marca-Modelo fuera del catálogo conocido (configuracion.xlsx)

marca   modelo  unidades
 HINO STANDARD      1290

*No implica error — puede ser un modelo nuevo legítimo no agregado aún al catálogo. Revisar manualmente.*


### Protocolo de muestreo para validación manual

Con 95% de confianza y margen de error del 5% sobre 61,158 filas clasificadas, el tamaño de muestra necesario es **382 filas** (fórmula `n = Z²·p·(1-p)/e²` con corrección por población finita). Tomar esa cantidad de filas al azar y verificar a mano Marca-Modelo-Categoría-Categoría Withmory contra el DUA original en Veritrade.


---

## 6. Fragmentación de Marcas y Familias (Consolidación Comercial)

**SINOTRUK / SINOTRUK HOWO / SINOTRUK WANGPAI** — total combinado: 5,131 unidades
  - SINOTRUK: 5,105
  - SINOTRUK HOWO: 23
  - SINOTRUK WANGPAI: 3

**HOWO / SINOTRUK HOWO** — total combinado: 529 unidades
  - HOWO: 506
  - SINOTRUK HOWO: 23

**IVECO / IVECO ASTRA** — total combinado: 467 unidades
  - IVECO: 387
  - IVECO ASTRA: 80

**KAMA / KAMAZ** — total combinado: 102 unidades
  - KAMA: 100
  - KAMAZ: 2

**ASTRA / IVECO ASTRA** — total combinado: 95 unidades
  - ASTRA: 15
  - IVECO ASTRA: 80

**WANGPAI / SINOTRUK WANGPAI** — total combinado: 8 unidades
  - WANGPAI: 5
  - SINOTRUK WANGPAI: 3

**PEREYRA / CP PEREYRA** — total combinado: 10 unidades
  - PEREYRA: 4
  - CP PEREYRA: 6

*Estas variantes probablemente son la misma marca comercial escrita distinto — consolidarlas evita subestimar su participación de mercado en los rankings.*


---

## 7. Impacto Económico (Traducción Financiera de Errores)

                                               Categoría          USD     %
CIF Clasificado (Marca+Categoría+Cat.Withmory completos) 3.681217e+09  96.7
                            CIF No Clasificado / Erróneo 1.269646e+08   3.3
                                                   TOTAL 3.808181e+09 100.0

3.3% del CIF sin clasificar — bajo, no representa riesgo financiero material.
