# The Buying Studio — AI Buying Decision Assistant

A buying decision assistant that filters laptops against your **real budget first**, then
explains what each remaining option gives up and which facts are genuinely unknown.

The backend is deterministic Python. The frontend is a React + TypeScript single-page app
that reads only from that backend — there is no mock data layer and no fabricated AI output.

> **Demonstration build.** Every product, specification, seller, price and offer served by
> this project is **synthetic** (`is_demo=true`). Nothing is a real listing, verified market
> price, stock status or seller quote. Live provider integration is deliberately deferred to
> the end of the project; see `docs/DECISIONS.md` (D-008).

---

## Quick start

Two terminals. The API must be running before the frontend is useful.

### 1. Backend (Python 3.12)

```bash
python -m pip install --break-system-packages --no-deps fastapi starlette uvicorn click sniffio
python serve.py                 # http://127.0.0.1:8000  (docs at /docs)
```

`--no-deps` is required on this machine: pip cannot write `.exe` console-script shims into
`C:\python312\Scripts` (fails with `WinError 2` on every console-script install). The
packages themselves install and import correctly, and `serve.py` launches uvicorn through
`uvicorn.run()` so no shim is needed.

### 2. Frontend (Node 18+)

```bash
cd web
npm install
npm run dev                    # http://localhost:5173
```

The Vite dev server proxies `/api` to `127.0.0.1:8000`, so the browser only ever talks to one
origin in development.

### Optional: live model explanations

Add to `.env` (already present, never commit it):

```
GEMINI_API_KEY=<your key>
GEMINI_MODEL=gemini-3.8-flash
```

Without a key the assistant still works: it generates a **deterministic, clearly labelled**
explanation from the catalogue instead. The UI always shows which mode produced the answer.

---

## Tests

```bash
# Python: 123 tests (domain, requirements, catalog, shortlist, prompts, grounding, API)
python -m unittest discover tests

# Frontend: strict TypeScript check + production build
cd web && npm run build        # runs tsc --noEmit then vite build

# End-to-end HTTP checks against a *running* backend
python e2e_check.py            # 42 assertions, includes a real Gemini call when a key exists
```

`tests/test_api.py` skips itself cleanly if FastAPI is not installed, so the pure-Python
tests still run in a bare environment.

---

## How it works

Deterministic code decides; the language model only explains.

| Layer | Module | Responsibility |
|---|---|---|
| M1 | `aba/domain/provenance.py`, `aba/domain/freshness.py` | Product / offer / evidence records, freshness policy |
| M2 | `aba/requirements/model.py` | Requirement schema + deterministic validation |
| M3 | `aba/shortlist/filter.py` | Hard constraints (budget, condition, must-haves) + preference scoring |
| M4 | `aba/explanation/prompts.py`, `aba/explanation/grounding.py` | Prompt construction, evidence citation, unknown labelling |
| M6 | `aba/api/assistant.py` | Gemini call via the M4 prompt, or labelled deterministic fallback |
| API | `aba/api/*`, `serve.py` | Read-only HTTP transport over the modules above |
| Web | `web/src/*` | React + TypeScript SPA |

Three invariants are enforced in code and covered by tests:

1. **Hard constraints precede ranking.** An over-budget offer is excluded, not de-ranked.
2. **Unknown is not satisfied.** A specification recorded as `"Unknown"` / `"Not specified"`
   fails a must-have and never counts as a matched preference.
3. **Demo data can never be presented as live.** Every record carries `is_demo=true` and the
   loader refuses to serve a fixture that is not flagged.

### Dataset

`laptop_demo_dataset_pk.json` — 4 synthetic Pakistan-market laptops with 10 specifications
each, one seller offer each, and a dataset-level provenance block. The API adapter
(`aba/api/dataset.py`) normalises these into canonical `aba` domain objects, mapping
`"new (illustrative)"` to the canonical condition `new` while preserving the raw string in
evidence notes.

Price units are declared explicitly (`currency_unit: "rupees"`) so the whole-rupee figures in
the fixture can never be confused with the paisa/cent convention used by
`aba/catalog/demo_catalog.json`.

---

## Repository layout

```
aba/
  domain/        M1 provenance + freshness
  requirements/  M2 requirement schema
  shortlist/     M3 hard-constraint filtering
  explanation/   M4 prompt + grounding
  catalog/       demo catalog + loader (enforces is_demo)
  api/           additive HTTP layer (dataset, service, assistant, app)
web/             React + TypeScript frontend
tests/           123 unittest tests
docs/            decisions, state, data-source research
laptop_demo_dataset_pk.json   curated synthetic catalogue
serve.py         API launcher
demo_pipeline.py M1-M5 end-to-end demonstration (no network)
e2e_check.py     HTTP end-to-end verification script
```

---

## Documentation

- `PROJECT_BRIEF.md` — product vision and principles
- `docs/DECISIONS.md` — accepted decisions (D-001 … D-012)
- `docs/PROJECT_STATE.md` — current status and next task
- `docs/DATA_SOURCE_RESEARCH.md` — provider investigation register (all entries `UNVERIFIED`)
- `docs/PRODUCT_REQUIREMENTS.md` — functional and non-functional requirements
- `AGENTS.md` — working rules for this repository

## Known limitations

- Catalogue contains 4 synthetic laptops; no live provider is integrated (D-008 open).
- No checkout, payment, warranty or delivery flow — deliberately out of scope.
- Availability is unknown for every record and is shown as unknown, never as "in stock".
- No product photographs: the dataset contains none and reuse rights are unverified, so
  product art is generated deterministically from each record and labelled "Illustration".
- Saved items and comparison persist to `localStorage` only. There is no account system, so
  nothing is synced between devices and the UI does not claim otherwise.