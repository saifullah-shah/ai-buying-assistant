# Project State / Handoff

Last updated: 2026-10-14

## Current stage

Milestones M1-M6 are complete and the project now has a working web application end to end.
The deterministic core (`aba/`) is unchanged in responsibility and remains the single source
of truth for domain logic; an additive FastAPI transport layer (`aba/api/`) exposes it over
HTTP, and a React + TypeScript frontend (`web/`) consumes only that API.

D-006 (laptops) is ACCEPTED. D-007 (Pakistan market) remains PROPOSED. D-008 (product data
source) remains OPEN - the curated synthetic dataset is in place and no live provider has been
approved, verified or integrated.

## Delivered

### Milestones (123 passing tests)

- M1 `aba/domain/provenance.py`, `aba/domain/freshness.py` - Product / SellerOffer /
  PriceObservation / ProductSpecification / SourceRef / Evidence, explicit VerificationStatus,
  clock-injective freshness policy, `is_demo` kill-switch.
- M2 `aba/requirements/model.py` - Requirement schema with deterministic validation.
- M3 `aba/shortlist/filter.py` - hard constraints (budget + currency match, condition,
  must-haves) and preference scoring, with per-constraint flags.
- M4 `aba/explanation/prompts.py`, `aba/explanation/grounding.py` - prompt construction,
  evidence citation, unknown labelling, section validation.
- M5 `demo_pipeline.py` - runnable end-to-end demonstration (`python demo_pipeline.py`).
- M6 `aba/api/assistant.py` - Gemini call through the M4 prompt with structural validation,
  plus an explicitly labelled deterministic fallback when no key is configured.

### Web application

- `serve.py` / `aba/api/app.py` - FastAPI read-only API: `/api/health`, `/api/dataset`,
  `/api/products`, `/api/products/{id}`, `POST /api/compare`, `POST /api/assistant`.
- `web/` - React 18 + TypeScript + Vite SPA with routes `/`, `/discover`, `/product/:id`,
  `/compare`, `/saved`, and a 404. Hand-written design-token CSS, no CSS framework.
- `e2e_check.py` - 42 HTTP assertions against a running backend.

### Bugs found and fixed during this work

1. `ProductSpecification.is_unknown()` treated only `None` as unknown, so a spec recorded as
   `"Unknown"` / `"Not specified"` counted as a *satisfied* preference and could satisfy a
   must-have. That directly contradicted D-004. Fixed with an explicit
   `NOT_DISCLOSED_SENTINELS` set plus regression tests.
2. FastAPI 0.143 silently fails to bind repeated list query params declared as
   `Optional[List[str]] = None` - they arrive as `None`. Fixed with explicit `Query(None)`.
3. `aba/api/service.py` reported `unknown_field_keys: []` because it tested `is None` instead
   of the domain model's `is_unknown()`. Fixed.
4. M4 prompt builders produced duplicated labels ("Need: Need: ...", "Budget: Budget: ...")
   because the `_format_req_*` helpers included a prefix the block template also added. Fixed.
5. Frontend: inline `gridTemplateColumns` styles overrode responsive media queries, so the
   hero and product-detail layouts stayed two-column at 360 px. Replaced with classes.
6. Frontend: the desktop filter rail rendered inline below the mobile breakpoint, duplicating
   the drawer and pushing products far down the page. Fixed.
7. Frontend: the mobile filter bar was declared after its `min-width: 1024px` override, so
   same-specificity source order made it win and it showed on desktop. Fixed.
8. Frontend: search criteria were merged from `localStorage` into URL-driven searches, so a
   shared link inherited the recipient's earlier filters. The URL now defines the whole search
   when it carries any parameter.
9. `demo_pipeline.py` contained only comments - M5 was recorded as complete with no executable
   code. Implemented.
10. Repo hygiene: removed ~20 stray pip log files and two throwaway catalog scripts; extended
    `.gitignore` for `node_modules` and build output; repaired `docs/DECISIONS.md` from cp1252
    to UTF-8.

## Verification actually run

| Check | Command | Result |
|---|---|---|
| Python suite | `python -m unittest discover tests` | 123 tests, 0 failures, 0 errors |
| Frontend types | `npm run typecheck` | clean |
| Production build | `npm run build` | built, 231 kB JS / 71 kB gzip, 28.5 kB CSS |
| API end to end | `python e2e_check.py` | 42/42 passed, live Gemini call returned a section-validated explanation |
| Browser render | headless Chrome `--dump-dom` | all 5 routes render with live API data |
| Browser interactions | per-profile Chrome runs | budget / min-ram / must-have / sort all produce the correct result sets and chips |
| Responsive | same-origin probe at exact widths | no horizontal overflow at 320, 360, 390, 768, 1024, 1440; rail and drawer swap at 1024; nav collapses at 860 |
| Visual review | screenshots at 360 / 768 / 1280 / 1440 | layout, contrast and hierarchy reviewed |

## Not yet verified

- Live provider access, eligibility, permitted fields, storage rights and affiliate terms.
  All candidates remain `UNVERIFIED` in `docs/DATA_SOURCE_RESEARCH.md`.
- No unit or integration tests run *inside* a browser runner; frontend behaviour was verified
  by headless Chrome render and interaction checks rather than a test framework.
- Accessibility was implemented to WCAG 2.2 AA patterns (landmarks, focus management, skip
  link, reduced motion, labelled controls, `aria-live` announcements) and spot-checked in the
  rendered DOM. No automated axe/Lighthouse audit was run.
- Core Web Vitals were not measured. Bundle size is small (71 kB gzip JS) but that is not a
  substitute for a measurement.
- Product photography. The dataset contains none and reuse rights are unverified, so artwork is
  generated deterministically and labelled "Illustration - no photo".

## Active next task

1. Review the web application and decide whether it meets the product intent.
2. Optionally add a frontend test runner (Vitest + Testing Library) for component behaviour
   and an accessibility audit (axe) in CI.
3. Keep D-007 provisional and D-008 open until a permitted provider is verified.

## Known blockers / risks

- Source access and terms are not verified.
- Product identity and configuration matching must be tested against real data before any
  live pilot.
- Current price and availability cannot be promised without timestamping and freshness
  controls; the prototype shows freshness honestly instead.
- The Gemini endpoint returned transient 503s under load during testing. The assistant falls
  back to labelled deterministic mode in that case, so the UI never shows a fabricated answer.
