# veritrade-imports — AI Agent Instructions

## Domain / Scientific Context

- **Problema**: estructurar y normalizar el campo de texto libre "Descripción Comercial" de exports
  de Veritrade (inteligencia comercial de aduanas peruanas) para vehículos (camiones, partida
  8704229000 y afines) y maquinaria, y contrastar la cobertura resultante contra los reportes
  mensuales de la AAP (Asociación Automotriz del Perú) para detectar brechas de descarga.
- **Outcome / target**: un `data/gold/camiones.parquet` (y `maquinaria.parquet`) limpio, deduplicado
  por DUA+VIN, con marca/modelo normalizados contra un vocabulario controlado, listo para el
  dashboard Streamlit (`app.py`, `pages/2_Camiones.py`) y para análisis de market share.
- **Data provenance**: los `.xlsx` crudos vienen de Veritrade (proveedor pago de inteligencia de
  aduanas) y se descargan manualmente siguiendo `metodologia_descarga_mensual.md`. Son datos
  comerciales privados — por eso casi todo `*.xlsx` y `data/bronze/`, `data/silver/` están en
  `.gitignore`; solo los parquet de `data/gold/` se versionan (Streamlit Cloud los sirve directo
  desde el repo).

## Architecture

Arquitectura medallion (bronze → silver → gold):

```bash
uv run python pipeline/aap.py            # refs/*.xlsx (AAP) -> bronze/gold de referencia
uv run python pipeline/run.py            # orquesta silver.py + gold.py (o --silver-only / --gold-only)
uv run python pipeline/build_parquet.py  # consolida gold/*_normalizado.xlsx -> data/gold/camiones.parquet
uv run python scripts/validar_cobertura.py --mes N --anio YYYY  # valida cobertura vs AAP
```

- **Fase 1 (silver, determinístico, gratis)**: `pipeline/silver.py` tokeniza `CÓDIGO:valor` de la
  descripción comercial en ~28 columnas tipadas.
- **Fase 2 (gold, LLM)**: `pipeline/gold.py` normaliza marca/modelo/atributos contra el vocabulario
  (`data/vocab_extra.json` + semilla) usando DeepSeek (`pipeline/llm/client.py`, API OpenAI-compatible),
  con cache reanudable en `.cache/llm/` (`pipeline/llm/cache.py`) y flags de confianza
  (`ok`/`alias`/`low`/`nomatch`) vía `pipeline/llm/validate.py` (rapidfuzz + fallback difflib).
- **Dashboard**: `app.py` + `pages/2_Camiones.py` (Streamlit) leen `data/gold/*.parquet` vía
  `shared/loader.py` y quedan desplegados en Streamlit Cloud.

## Key Files

| File | Purpose |
|------|---------|
| `pipeline/run.py` | Orquestador silver→gold (subprocess) |
| `pipeline/silver.py` | Bronze→Silver: parser determinístico de "Descripción Comercial" |
| `pipeline/gold.py` | Silver→Gold: normalización LLM (DeepSeek) |
| `pipeline/aap.py` | ETL de reportes AAP de referencia (`refs/*.xlsx`) |
| `pipeline/build_parquet.py` | Consolida gold xlsx → `data/gold/camiones.parquet` (dedup DUA+VIN) |
| `pipeline/llm/` | vocab, validate, client (DeepSeek), cache, sampler, report |
| `scripts/validar_cobertura.py` | Validación mensual de cobertura Veritrade vs AAP por marca |
| `data/vocab_extra.json` | Extensión curada del vocabulario (marcas/alias nuevos) |
| `metodologia_descarga_mensual.md` | Runbook de descarga mensual + checklist |
| `informe_auditoria_cobertura.md` | Log de auditoría de cobertura (append-only) |

⚠️ **Duplicación conocida sin resolver**: `scripts/extract_descripcion.py` / `scripts/extract_llm.py`
/ `scripts/llm/` son una versión anterior (documentada en `README.md`, interfaz `inputs/`→`outputs/`)
que **difiere** de `pipeline/` (arquitectura medallion actual). No asumir que son intercambiables ni
borrar uno a favor del otro sin antes diffear con cuidado — ver issues de `bd` para el seguimiento.

## Data Conventions

- **Layers**: `data/bronze/` (xlsx crudo), `data/silver/` (estructurado), `data/gold/` (normalizado,
  parquet — el único nivel versionado en git).
- **Pandas + PyArrow** es el stack actual (no polars/duckdb). Cuidado con el backend Arrow de pandas
  en Python 3.14: ya hubo bugs de `pd.NA` incompatible con `.round()` y con `.upper()` en lambdas
  sobre columnas string — siempre null-guard antes de esas operaciones.
- **DuckDB/Polars**: no se usan en este repo — no asumir su disponibilidad.
- Dedup de filas: por `DUA + VIN` (ver `pipeline/build_parquet.py`).
- El `.env` (con `DEEPSEEK_API_KEY`) nunca se commitea; se carga con un loader casero (no hay
  dependencia `python-dotenv`).

## Conventions

- **Issue tracking**: este proyecto usa **beads** (`bd`) — ver `AGENTS.md` para el flujo completo
  (`bd ready`, `bd show`, `bd update --claim`, `bd close`). No usar TodoWrite/TaskCreate/MEMORY.md.
- **Gestor de dependencias**: `uv` + `pyproject.toml` es la fuente de verdad; `requirements.txt` se
  regenera con `uv export --no-hashes --no-dev -o requirements.txt` (y se le quita la línea `-e .`
  a mano) porque Streamlit Cloud lo lee directo para el deploy — no lo edites a mano.
- **Commits**: estilo Conventional Commits en español (`fix:`, `feat:`, `docs:`, `audit:`), descriptivos,
  a veces con cuerpo resumiendo métricas de resultado (cobertura %, etc.).
- **PRs**: `main` está protegido — se requiere PR (sin approval obligatorio, un solo dev) con CI en
  verde y conversaciones resueltas antes de mergear. Es para trazabilidad, no para bloquear el flujo.
- Excepciones de cobertura conocidas y permanentes (HOWO MAX, SINOTRUK, RAM, FORD) están hardcodeadas
  en `scripts/validar_cobertura.py` (`EXCEPCIONES`) — no son bugs, son anomalías documentadas.


<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:970c3bf2 -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

**Architecture in one line:** issues live in a local Dolt DB; sync uses `refs/dolt/data` on your git remote; `.beads/issues.jsonl` is a passive export. See https://github.com/gastownhall/beads/blob/main/docs/SYNC_CONCEPTS.md for details and anti-patterns.

## Agent Context Profiles

The managed Beads block is task-tracking guidance, not permission to override repository, user, or orchestrator instructions.

- **Conservative (default)**: Use `bd` for task tracking. Do not run git commits, git pushes, or Dolt remote sync unless explicitly asked. At handoff, report changed files, validation, and suggested next commands.
- **Minimal**: Keep tool instruction files as pointers to `bd prime`; use the same conservative git policy unless active instructions say otherwise.
- **Team-maintainer**: Only when the repository explicitly opts in, agents may close beads, run quality gates, commit, and push as part of session close. A current "do not commit" or "do not push" instruction still wins.

## Session Completion

This protocol applies when ending a Beads implementation workflow. It is subordinate to explicit user, repository, and orchestrator instructions.

1. **File issues for remaining work** - Create beads for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **Handle git/sync by active profile**:
   ```bash
   # Conservative/minimal/default: report status and proposed commands; wait for approval.
   git status

   # Team-maintainer opt-in only, unless current instructions forbid it:
   git pull --rebase
   bd dolt push
   git push
   git status
   ```
5. **Hand off** - Summarize changes, validation, issue status, and any blocked sync/commit/push step

**Critical rules:**
- Explicit user or orchestrator instructions override this Beads block.
- Do not commit or push without clear authority from the active profile or the current user request.
- If a required sync or push is blocked, stop and report the exact command and error.
<!-- END BEADS INTEGRATION -->

