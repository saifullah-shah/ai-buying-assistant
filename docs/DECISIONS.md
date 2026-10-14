# Decision Log

Use the following status labels: `ACCEPTED`, `PROPOSED`, `OPEN`, `REJECTED`, `SUPERSEDED`.
Only record a choice as `ACCEPTED` when the user explicitly agrees or the implementation demonstrates it and the user approves it. Include date, context, alternatives, and consequences.

## D-001 â€” Develop incrementally
- Status: PROPOSED
- Date: 2026-10-13
- Decision: This is a long-running project, not a one-shot build. Work in small milestones, with documented handoffs and Git commits.
- Consequence: Each task should leave the project in a verifiable state and update project status.

## D-002 â€” Use OpenCode with VS Code and ChatGPT Free for research assistance
- Status: PROPOSED
- Date: 2026-10-13
- Decision: OpenCode is the coding agent; ChatGPT Free is a separate research, planning, and review assistant.
- Consequence: Keep canonical project files in the repository and selectively mirror key documents into a ChatGPT Project. Do not rely on either tool's chat history as the only memory.

## D-003 â€” Defer competitor positioning and commercial validation
- Status: ACCEPTED
- Date: 2026-10-13
- Decision: Focus for now on building a technically capable product. Detailed competitive positioning/commercial validation is a later phase unless the user requests it or an implementation dependency requires it.
- Consequence: Avoid repeatedly derailing implementation tasks into competitor analysis.

## D-004 â€” Use evidence-backed recommendations and deterministic constraints
- Status: ACCEPTED
- Date: 2026-10-13
- Decision: Do not let an LLM invent product facts or be the sole source of constraint filtering/ranking. Store evidence and unknowns explicitly.
- Consequence: Data provenance, hard-constraint tests, and scoring tests are core requirements.

## D-005 â€” Python/FastAPI + PostgreSQL as a candidate stack
- Status: PROPOSED
- Date: 2026-10-13
- Context: Fits Python/AI work and can support product data, offers, and price observations.
- Alternatives: Other backends/databases; delay stack choice until repository and MVP scope are inspected.
- Consequence: Do not scaffold the entire stack until the user approves or a small experiment establishes the need.

## D-006 â€” Laptops as first category
- Status: ACCEPTED
- Date: 2026-10-13
- Decision: Laptops are the first product category for the prototype.
- Context: Laptops have structured specifications and meaningful buyer trade-offs, making them suitable for testing requirement profiling, deterministic filtering, ranking, and grounded explanations.
- Consequences: Scope the initial dataset and tests to laptops. Keep the underlying domain model category-agnostic.

## D-007 - Initial prototype market
- Status: PROPOSED
- Date: 2026-10-13
- Decision: Use Pakistan as the initial prototype market, subject to review after data-source investigation.
- Context: Pakistan provides a concrete local buyer context. The availability of permitted, sufficiently complete live product data remains unverified.
- Alternatives: UK as the first live-data pilot if an accessible, permitted product feed offers better coverage.
- Consequences: Use PKR and Pakistan-specific buyer assumptions only where applicable. Clearly label demo data and do not claim live availability or pricing. Revisit the decision after testing provider access.

## D-008 â€” Product data source
- Status: OPEN
- Date: 2026-10-13
- Decision: Start prototype development with a curated, traceable CSV/JSON dataset. Do not approve a live provider yet.
- Context: No live source has been confirmed for account eligibility, laptop coverage, data fields, freshness, licensing, storage, or display permissions.
- Next actions:
  1. Create a small laptop dataset with explicit provenance and demo/live status.
  2. Investigate Awin feed availability for relevant UK laptop retailers.
  3. Investigate permitted local marketplace or retailer data access for Pakistan.
  4. Record official documentation, access requirements, a sample response, and data-use restrictions in DATA_SOURCE_RESEARCH.md.
  5. Approve a pilot provider only after access and usage rights have been verified.
- Consequences: The prototype remains testable without external dependencies. Live offers must not be fabricated or presented as verified until a permitted source is configured.

## D-009 - Core domain model with provenance and freshness (M1)
- Status: ACCEPTED
- Date: 2026-10-13
- Decision: Implemented a source-neutral core data model comprising Product (canonical identity), SellerOffer (seller-specific price/condition), PriceObservation (time-series price snapshot), ProductSpecification (key/value attrs with explicit Evidence), SourceRef / Evidence provenance, and a deterministic freshness() policy. Validation is hand-written (no pydantic dependency in M1) but the shape is pydantic-compatible for future migration. Package layout is flat `aba/` at repo root for zero-install import. Demo catalog fixture is clearly labelled `is_demo=true` and the loader aborts if any fixture lacks it, preventing accidental presentation of demo data as live.
- Consequences: Every later layer (requirement profiling, constraint filtering, LLM explanation) can rely on explicit, provenance-rich records rather than implicit LLM assumptions. The model enforces hard constraints (budget, currency format, UTC datetimes) by code before any ranking. The `is_demo` gate is the single kill-switch separating demo fixtures from live offers. The design stays category- and market-agnostic so D-006/D-007 remain open. Drawback: adding a new dependency (pydantic) or changing the layout would require a follow-up refactor.


## D-010 - LLM-grounded recommendation layer (M4)
- Status: ACCEPTED
- Date: 2026-10-13
- Design: Prompt templates, grounding rules, and output schema for LLM-grounded recommendations. 
  LLM API integration deferred to future milestone.  All design-time logic (prompts, grounding 
  rules, unknowns labeling, output schema) is deterministic and testable without an API key.
- Consequences: The M3 shortlist entries can be fed to an LLM with explicit instructions 
  and evidence citations, producing grounded natural-language explanations.  The prompt design 
  and grounding logic are validated by a 14-test deterministic test suite.  Deferred step: 
  actual LLM API integration requires model selection, API key approval, and testing with 
  real LLM responses.


## D-011 - LLM API Integration (M6)
- Status: ACCEPTED
- Date: 2026-10-13
- Decision: LLM API integration (Gemini) via new google.genai SDK (v2.30.1). 
  M4 prompt design and grounding logic complete and test-validated without API key. Deprecated google.generativeai SDK replaced.
- Connections: M4 prompt templates, M5 pipeline output, .env configuration (API key + model ID).
- Connections: M1-M5 provide data foundation; M6 adds LLM call layer.
- Blockers: None (SDK installed, API key configured, model accessible).
- Future: None outstanding for the prototype path. Response parsing, section validation and the labelled deterministic fallback are implemented in `aba/api/assistant.py` and exercised by `tests/test_api.py`.

## D-012 - Web application and frontend stack
- Status: ACCEPTED
- Date: 2026-10-14
- Context: The repository contained no frontend and no HTTP layer - only the pure-Python
  `aba` library plus 80 tests. PROJECT_BRIEF lists "Backend: Python + FastAPI" and
  "Frontend: Next.js/React, if a web UI is chosen for the MVP" as *provisional*, so the stack
  was chosen to honour those proposals rather than replace them.
- Decision: Build (a) an additive FastAPI transport layer in `aba/api/` that delegates to the
  existing M1-M4 modules without re-implementing any of their logic, and (b) a React 18 +
  TypeScript + Vite single-page app in `web/`. Next.js was not used because the backend is a
  separate Python service and no server-side rendering benefit applies to a read-only JSON API.
  No CSS framework was added; the design system is hand-written from design tokens
  (`web/src/styles/tokens.css`) so the visual identity is distinctive and the dependency
  surface stays small.
- Consequences: `aba/` remains the single source of truth for domain logic and can still be
  used headlessly; the API is a thin transport layer with no constraint, scoring or product
  logic of its own. `npm run build` runs `tsc --noEmit` before `vite build`, so type errors
  fail the build. FastAPI/uvicorn are the only new Python dependencies; they are installed
  with `--no-deps` because this machine cannot write console-script shims (WinError 2), and
  `serve.py` starts uvicorn via `uvicorn.run()` instead of the `uvicorn` shim.
- Alternatives considered: Jinja templates + stdlib `http.server` (fewer dependencies, but no
  router, no component reuse and no credible path to the comparison/assistant experience);
  Next.js (matches the brief verbatim but adds a Node server duplicating the Python API).
