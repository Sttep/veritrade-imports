# Roster de sub-agentes de veritrade-imports

Estos son los agentes definidos en `.claude/agents/` para este repo. Todos menos
`diseno-visual` son de **solo lectura** (`Read, Grep, Glob, Bash`): investigan y
reportan, nunca tocan código ni datos sin que la persona confirme explícitamente cada
cambio propuesto. `diseno-visual` es el único con `Edit`/`Write`, y solo para CSS/HTML
inline del dashboard — con el mismo gate de confirmación por cambio puntual.

Se dividen en dos tracks independientes: **Datos** (pipeline de ingestión/calidad) y
**Dashboard** (el Streamlit que consume esos datos). No se superponen entre sí — cada
agente tiene una frase explícita en su prompt de "esto no es lo mío, eso lo hace X" para
evitar trabajo duplicado.

## Track Datos

| Agente | Qué hace | Cuándo usarlo |
|---|---|---|
| **gatekeeper-datos** | Revisa archivos `.xlsx` nuevos en `data/cuarentena/` **antes** de que entren al pipeline (silver→gold→parquet). Clasifica riesgo (bajo/medio/alto) con motivo concreto — nunca aprueba ni mueve nada por su cuenta. | Antes de procesar una descarga mensual nueva de Veritrade, o para el chequeo rutinario de "¿qué importador falta este mes?" sin archivos nuevos de por medio. |
| **auditor-datos** | Audita la calidad de lo que ya está en `data/gold/*.parquet` y la consistencia de `configuracion.xlsx`/`data/vocab_extra.json`. Corre los 6 scripts `validar_*`/`detectar_*`/`auditar_*` existentes más un checklist manual de cruces que esos scripts no cubren. | Después de que datos nuevos entraron al pipeline, o cuando piden auditar catálogos/incoherencias en general. |

**Cómo encajan juntos**: `gatekeeper-datos` es el filtro de entrada (pre-ingestión, por
archivo); `auditor-datos` es el chequeo de salida (post-ingestión, sobre el dataset
consolidado). Un archivo puede pasar el gatekeeper limpio y aun así el auditor encontrar
un problema aguas abajo (ej. una marca que normalizó distinto de lo esperado) — no son
redundantes, cubren dos momentos distintos del mismo pipeline.

## Track Dashboard

| Agente | Qué hace | Cuándo usarlo |
|---|---|---|
| **rompe-dashboard** | QA adversarial técnico: fuzzing de combinaciones de filtros (`AppTest` headless) + clicks reales de mouse (Playwright) buscando crashes y cálculos incorrectos. | Antes de dar por cerrada una ronda de cambios, o cuando piden buscar bugs/crashes específicamente. |
| **consultor-bi** | Evalúa si el dashboard funciona como herramienta de **exploración** (drill-down, cross-filtering, insights automáticos, jerarquía de información) o es un informe estático con más clicks. | Junto con `jefe-exigente`, como gate de cierre de una ronda de cambios, o cuando piden una opinión de consultoría BI. |
| **ux-no-tecnico** | Diagnostica fricción de uso para alguien sin background técnico ni de datos (jerga sin explicar, widgets ambiguos, densidad de información). Solo **encuentra** el problema, no propone solución. | Para evaluar si el dashboard es entendible por un usuario no experto. |
| **ux-propone-mejoras** | Toma los hallazgos de `ux-no-tecnico` y **propone** cómo resolverlos: wireframes en texto/ASCII, copy alternativo, reordenamiento de widgets. No toca código. | Después de correr `ux-no-tecnico`, o cuando piden ideas concretas de rediseño. |
| **diseno-visual** | Toma las propuestas de layout de `ux-propone-mejoras` (o pide directamente pulir/unificar el sistema visual existente) y las traduce a specs de diseño concretas: paleta, tipografía, espaciado, clases CSS. Es el único que puede **aplicar** el cambio al código, siempre con confirmación puntual por propuesta. | Para pulir/unificar colores y tipografía inconsistentes, o para implementar una propuesta de rediseño ya acordada. |
| **jefe-exigente** | Gate final antes de mostrarle el dashboard a gerencia: credibilidad ejecutiva en dos ejes — ¿los números suenan verdaderos para alguien que conoce el mercado de memoria? ¿el acabado se ve de nivel gerencial? | Como última revisión antes de dar por cerrada una ronda de cambios, o para una crítica dura pre-demo. |

### Cómo encajan juntos (secuencia típica de una ronda de cambios al dashboard)

```
1. rompe-dashboard        →  ¿algo crashea o calcula mal? (baseline técnico, se puede
                              correr en cualquier momento, incluso solo/repetido)

2. ux-no-tecnico           →  ¿dónde se pierde un usuario no técnico?
        ↓ (hallazgos)
3. ux-propone-mejoras      →  ¿cómo se resuelve esa fricción? (wireframes/copy en texto)
        ↓ (propuestas de layout)
4. diseno-visual           →  ¿cómo se ve exactamente? (specs de color/tipografía/CSS,
                              y opcionalmente lo implementa con confirmación)

5. consultor-bi            →  ¿esto ya funciona como BI real? (puede correr en paralelo
                              a 2-4, es un eje independiente de interactividad/insights)

6. jefe-exigente           →  gate de cierre: ¿se lo muestro a mi jefe tal cual?
                              (correrlo al final, después de aplicar los fixes de 1-5,
                              no antes — si lo corrés primero vas a repetir hallazgos que
                              los agentes de arriba ya iban a encontrar más barato)
```

`consultor-bi` y `jefe-exigente` están pensados para correr **juntos como gate de
cierre** (así lo dice explícitamente el prompt de `consultor-bi`) — uno mira si es BI de
verdad, el otro si es creíble para el negocio; un dashboard puede pasar uno y fallar el
otro.

Precedente real de esta sesión: `jefe-exigente` encontró 5 bloqueantes (fórmula de
proyección, comparación Sinotruk vs mercado, tarjeta "Competencia" auto-comparándose,
eje de gráfico sin traducir, tablas sin formato) → se corrigieron directamente → se
corrió `rompe-dashboard` con clicks reales para verificar que no se rompió nada → recién
ahí se agregó `diseno-visual` al roster para la siguiente ronda de pulido visual.
