# veritrade-imports

Pipeline para **estructurar y normalizar** el campo de texto libre *"Descripción Comercial"* de
exports de **Veritrade** (importaciones de vehículos, p. ej. partida `8704229000` — camiones
diésel, y maquinaria) y contrastar la cobertura resultante contra los reportes mensuales de la
**AAP** (Asociación Automotriz del Perú). El resultado alimenta un dashboard Streamlit de market
share.

Arquitectura medallion, dos fases dentro de silver→gold:

1. **Silver — parser determinístico** (gratis, sin red) — descompone la descripción
   (`CÓDIGO:valor`) en ~28 columnas tipadas.
2. **Gold — normalización con LLM** (DeepSeek) — mapea marca, modelo y atributos contra un
   **vocabulario controlado**, con flags de confianza para revisión.

> **Datos:** los `.xlsx` crudos vienen de **Veritrade** (proveedor de inteligencia comercial de
> aduanas) y son datos comerciales privados — por eso `data/bronze/` y `data/silver/` están en
> `.gitignore`; solo los parquet de `data/gold/` se versionan (Streamlit Cloud los sirve directo
> desde el repo).
> **Uso de IA:** la fase gold usa un modelo generativo (DeepSeek); las columnas normalizadas
> (`marca_norm`, `modelo_match`, `*_norm`) quedan marcadas con flags de confianza y deben
> validarse antes de usarse en decisiones.

## Estructura

```
data/
  bronze/            xlsx crudo de Veritrade (privado, gitignored)
  silver/            estructurado por pipeline/silver.py (privado, gitignored)
  gold/              parquet normalizado y deduplicado — único nivel versionado en git
  vocab_extra.json   extensión curada del vocabulario (marcas nuevas, alias, alias de modelo)
refs/                reportes mensuales de la AAP (xlsx) usados como referencia de cobertura
pipeline/
  run.py             orquestador: silver.py -> gold.py (o --silver-only / --gold-only)
  silver.py          Fase 1: parser determinístico de "Descripción Comercial"
  gold.py            Fase 2: normalización LLM (DeepSeek)
  aap.py             ETL de refs/*.xlsx -> data/gold/aap_camiones.parquet
  build_parquet.py   consolida gold/*_normalizado.xlsx -> data/gold/camiones.parquet (dedup DUA+VIN)
  llm/               vocab · schema · client (DeepSeek) · validate · cache · sampler · report
scripts/
  validar_cobertura.py   validación mensual de cobertura Veritrade vs AAP por marca
app.py, pages/       dashboard Streamlit (lee data/gold/*.parquet vía shared/loader.py)
metodologia_descarga_mensual.md   runbook de descarga mensual + checklist de cobertura
```

## Instalación

Este proyecto usa [uv](https://docs.astral.sh/uv/) para dependencias:

```bash
uv sync --extra dev
```

Para la fase gold, copia `.env.example` → `.env` y pon tu clave:

```bash
cp .env.example .env
# editar .env:  DEEPSEEK_API_KEY=sk-...
```

## Uso

### Pipeline completo (silver + gold)

```bash
uv run python pipeline/run.py                 # todo: bronze -> silver -> gold
uv run python pipeline/run.py --silver-only   # solo Fase 1 (determinístico, gratis)
uv run python pipeline/run.py --gold-only     # solo Fase 2 (LLM)
uv run python pipeline/run.py --input data/bronze/mi_export.xlsx   # un archivo puntual
```

`pipeline/silver.py` procesa **todos** los `data/bronze/*.xlsx` y escribe el estructurado en
`data/silver/`. `pipeline/gold.py` normaliza contra el vocabulario y escribe en `data/gold/`,
reanudable vía cache en `.cache/llm/` (descripciones repetidas no se re-consultan). Cada fila trae
`modelo_flag`:

| flag | significado |
|---|---|
| `ok` | match exacto contra el vocabulario |
| `alias` | mapeo curado/inferido — revisar |
| `low` | match difuso de baja confianza — revisar |
| `nomatch` | sin match (igual conserva el valor crudo) — revisar |

### Consolidar a parquet

```bash
uv run python pipeline/build_parquet.py                    # consolida gold/*_normalizado.xlsx
uv run python pipeline/build_parquet.py --exclude patron    # excluye archivos por nombre
```

Escribe `data/gold/camiones.parquet`, deduplicado por `DUA + VIN`.

### Referencia AAP y validación de cobertura

```bash
uv run python pipeline/aap.py                                  # refs/*.xlsx -> data/gold/aap_camiones.parquet
uv run python scripts/validar_cobertura.py --mes 6 --anio 2026  # cobertura Veritrade vs AAP por marca
```

Ver `metodologia_descarga_mensual.md` para el runbook completo de descarga + validación mensual.

### Dashboard

```bash
uv run streamlit run app.py
```

### Curar el diccionario

Edita `data/vocab_extra.json` y vuelve a correr `pipeline/gold.py` — **re-normaliza gratis desde
la cache** (sin nuevas llamadas al LLM):

```jsonc
{
  "aliases":        { "MITSUBISHI FUSO": "FUSO" },        // variantes de marca → canónica
  "marcas":         { "FORLAND": ["FD400", "F1100"] },     // marcas/modelos nuevos
  "model_aliases":  { "VOLKSWAGEN": { "17.280 LR MAN E5": "ROBUST 17.280" } }  // modelo → canónico
}
```

## Notas

- **No** subas tu `.env` (está en `.gitignore`). Cualquier `.xlsx` fuera de `data/gold/` también
  se ignora, para no publicar data privada por accidente.
- El seguimiento de tareas usa [beads](https://github.com/steveyegge/beads) (`bd`); ver `AGENTS.md`.
- Contexto de dominio/arquitectura más detallado para agentes de IA en `CLAUDE.md`.
