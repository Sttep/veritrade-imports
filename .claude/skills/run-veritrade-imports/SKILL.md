---
name: run-veritrade-imports
description: Build, run, and drive the veritrade-imports Streamlit dashboard. Use when asked to run/start the dashboard, take a screenshot of it, verify a dashboard change visually, inspect what data a specific chart is showing (marca/submarca/segmento/etc), or fuzz/stress-test it for bugs.
---

This is a Python (uv) Streamlit app. It's driven three ways: a **real
headless-Chromium screenshot driver** (`driver.py`, via the `playwright`
Python package — no `chromium-cli`/Node available in this environment,
so this talks to Playwright directly) for visual/layout verification, a
**headless data-inspection driver** (`apptest_inventory.py`, via
Streamlit's own `AppTest` harness) for "what values are actually in chart
X" questions without needing a server or a browser at all, and a
**fuzzer** (`fuzz_dashboard.py`, same `AppTest` harness) that
automatically sweeps every widget/value combination looking for unhandled
exceptions — see the `rompe-dashboard` agent
(`.claude/agents/rompe-dashboard.md`) for adversarial QA. Start with
`apptest_inventory.py` when you just need to confirm data is correct;
reach for `driver.py` when you need to see layout/CSS or hand someone a
picture; reach for `fuzz_dashboard.py` when you need to find bugs.

All paths below are relative to the repo root.

## Prerequisites

Playwright's Python package + a Chromium binary (one-time, already done
in this checkout — re-run only if `driver.py` reports the browser is
missing):

```bash
uv add --dev playwright
uv run playwright install chromium
```

No `apt-get`/`xvfb` needed — this environment is Windows (Git Bash), and
Playwright's bundled Chromium runs headless without an X server here.

## Setup

Nothing beyond the repo's normal `uv sync` — this skill has no separate
env vars. It does need `data/gold/camiones.parquet` to exist (it's
versioned in the repo, so a fresh clone already has it).

## Run (agent path) — data verification, no server/browser

```bash
PYTHONIOENCODING=utf-8 uv run python .claude/skills/run-veritrade-imports/apptest_inventory.py
```

Runs `pages/2_Camiones.py` headlessly end-to-end and prints: exception
count, total chart count, and (with `--grep`) the exact labels/values
inside matching charts. Verified output for this repo's current state:
`0` exceptions, `25` charts.

| flag | what it does |
|---|---|
| `--page <path>` | run a different page/entrypoint (default `pages/2_Camiones.py`) |
| `--grep <text>` | only print charts whose title or any label contains this (case-insensitive) |
| `--dump <file.json>` | write the full chart inventory (title + labels + values) as JSON |

Example — confirm a specific chart's real content:

```bash
PYTHONIOENCODING=utf-8 uv run python .claude/skills/run-veritrade-imports/apptest_inventory.py --grep HOWO
```
```
Excepciones: 0
Charts (plotly_chart): 25
--- chart #14: Por sub-marca declarada en aduana ---
  [pie] [('SINOTRUK', 5063), ('HOWO', 367), ('SITRAK', 289), ('HOWO MAX', 136), ...]
```

## Run (agent path) — real screenshots

```bash
PYTHONIOENCODING=utf-8 uv run python .claude/skills/run-veritrade-imports/driver.py
```

Launches `uv run streamlit run app.py --server.headless true` on port
8501, drives it with headless Chromium, and always produces 4 screenshots
in `.claude/skills/run-veritrade-imports/screenshots/`:

| file | what it shows |
|---|---|
| `01_home.png` | landing page (`app.py`) |
| `02_camiones_global.png` | Camiones dashboard, default "Global" view |
| `03_camiones_sinotruk_tab.png` | after clicking the "🟡 Sinotruk" radio (switches tab order + filters) |
| `04_submarca_chart.png` | scrolled to the "Sub-marca declarada en aduana" chart |

Kills the Streamlit process on exit either way (success or exception).
Exit code is `1` only on an **uncaught JS exception** (`page.on("pageerror")`)
— ignore the informational "Console errors" count, see Gotchas.

| flag | what it does |
|---|---|
| `--port <n>` | use a different port (default 8501) |
| `--no-server` | drive an already-running instance instead of launching one |

## Run (agent path) — fuzzing for bugs

```bash
PYTHONIOENCODING=utf-8 uv run python .claude/skills/run-veritrade-imports/fuzz_dashboard.py --random-n 15 --max-opciones 6
```

Three passes, no server/browser needed (same `AppTest` harness as
`apptest_inventory.py`): a one-factor-at-a-time sweep of every radio/
selectbox/multiselect value, a handful of hand-picked adversarial combos
(inverted date range, `Marca A == Marca B`, empty carrocería filter,
etc.), and `--random-n` random multi-widget combinations. Reports any
combination that raises an uncaught exception, with the exact inputs and
traceback. Exit code `1` if it found any crash.

Baseline verified 2026-07-09: 101 cases (full sweep + 6 adversarial + 15
random), 0 crashes. For real adversarial QA see the `rompe-dashboard`
agent (`.claude/agents/rompe-dashboard.md`) — it knows this baseline and
pushes further instead of just re-running it.

| flag | what it does |
|---|---|
| `--random-n <n>` | how many random multi-widget combos to try (default 20) |
| `--max-opciones <n>` | cap on values tried per selectbox in the sweep (default 8) — some selects have 50+ options |
| `--skip-sweep` / `--skip-adversarial` / `--skip-random` | skip a pass |
| `--page <path>` | fuzz a different page (default `pages/2_Camiones.py`) |

## Run (human path)

```bash
uv run streamlit run app.py   # → opens http://localhost:8501 in your default browser. Ctrl-C to stop.
```

## Test

No test suite exists for `pages/`/`pipeline/` in this repo (see PR review
notes) — `apptest_inventory.py` above is currently the closest thing to
one for the dashboard.

---

## Gotchas

- **`PYTHONIOENCODING=utf-8` is not optional.** Both drivers (and this
  repo's other scripts) print emoji/unicode. Without this env var,
  Windows' console encoding (cp1252) crashes with `UnicodeEncodeError` on
  the first emoji print — this is a known repo issue (bead `liz-d33`).
- **Streamlit multipage URLs strip the numeric prefix**: `pages/2_Camiones.py`
  is served at `/Camiones`, not `/2_Camiones` or `/pages/2_Camiones`.
- **`st.tabs()` bodies all execute server-side regardless of which tab is
  visually active.** `apptest_inventory.py` sees every tab's charts in one
  `.run()` — you don't need to simulate a click to get tab3's (Sinotruk)
  data via that driver. `driver.py` still clicks the "🟡 Sinotruk" radio
  because that's a `st.radio`, not a tab, and it changes *which data* is
  loaded (filters to the Sinotruk family) as well as tab order.
- **Locator ambiguity on chart titles**: chart headings appear twice in
  the DOM — once as an `st.markdown()` heading and once as the Plotly
  SVG `<tspan>` title inside the chart itself. `page.get_by_text(...)`
  needs `.first` or it raises a strict-mode violation.
- **Two harmless "Failed to load resource: 404" console errors** appear
  after clicking the Sinotruk radio / switching views — reproduced
  consistently, but they don't affect rendering (verified: the resulting
  screenshots show fully-correct data every time) and don't reproduce on
  the initial page load alone. `driver.py` reports them as informational
  and does not fail the run on them; only a real `pageerror` (uncaught JS
  exception) sets the exit code.
- **Plotly chart data isn't plain JSON.** `AppTest`'s `chart.proto.spec`
  encodes big arrays (typically `values`, sometimes `labels`) as
  `{"dtype": "...", "bdata": "<base64>"}` instead of a list — both driver
  scripts' `_decode()` helper handles this (base64-decode +
  `np.frombuffer`); a naive `json.loads(...)['data'][0]['values']` will
  silently hand you a 2-key dict instead of the numbers.

## Troubleshooting

- **`playwright._impl._errors.Error: Executable doesn't exist`**: the
  Chromium binary wasn't installed. Run `uv run playwright install chromium`.
- **`driver.py` hangs at "Streamlit launching..."**: something's already
  bound to port 8501 (a previous run that didn't get killed). Find and
  kill it, or pass `--port 8502`.
- **`AttributeError: 'AppTest' object has no attribute 'plotly_chart'`**:
  use `at.get("plotly_chart")`, not `at.plotly_chart` — the direct
  attribute only exists for a handful of widget types in this Streamlit
  version.
