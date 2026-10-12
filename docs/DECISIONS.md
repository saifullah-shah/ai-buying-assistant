# Decision Log

Use the following status labels: `ACCEPTED`, `PROPOSED`, `OPEN`, `REJECTED`, `SUPERSEDED`.
Only record a choice as `ACCEPTED` when the user explicitly agrees or the implementation demonstrates it and the user approves it. Include date, context, alternatives, and consequences.

## D-001 — Develop incrementally
- Status: ACCEPTED
- Date: 2026-10-12
- Decision: This is a long-running project, not a one-shot build. Work in small milestones, with documented handoffs and Git commits.
- Consequence: Each task should leave the project in a verifiable state and update project status.

## D-002 — Use OpenCode with VS Code and ChatGPT Free for research assistance
- Status: ACCEPTED
- Date: 2026-10-12
- Decision: OpenCode is the coding agent; ChatGPT Free is a separate research, planning, and review assistant.
- Consequence: Keep canonical project files in the repository and selectively mirror key documents into a ChatGPT Project. Do not rely on either tool's chat history as the only memory.

## D-003 — Defer competitor positioning and commercial validation
- Status: ACCEPTED
- Date: 2026-10-12
- Decision: Focus for now on building a technically capable product. Detailed competitive positioning/commercial validation is a later phase unless the user requests it or an implementation dependency requires it.
- Consequence: Avoid repeatedly derailing implementation tasks into competitor analysis.

## D-004 — Use evidence-backed recommendations and deterministic constraints
- Status: ACCEPTED
- Date: 2026-10-12
- Decision: Do not let an LLM invent product facts or be the sole source of constraint filtering/ranking. Store evidence and unknowns explicitly.
- Consequence: Data provenance, hard-constraint tests, and scoring tests are core requirements.

## D-005 — Python/FastAPI + PostgreSQL as a candidate stack
- Status: PROPOSED
- Date: 2026-10-12
- Context: Fits Python/AI work and can support product data, offers, and price observations.
- Alternatives: Other backends/databases; delay stack choice until repository and MVP scope are inspected.
- Consequence: Do not scaffold the entire stack until the user approves or a small experiment establishes the need.

## D-006 — Laptops as first category
- Status: OPEN
- Date: 2026-10-12
- Context: A useful candidate because product attributes and buyer trade-offs are structured, but the user has not finalized it.

## D-007 — Launch market
- Status: OPEN
- Date: 2026-10-12
- Context: Pakistan and international markets have different retailer coverage, pricing, languages, affiliate eligibility, and data access.

## D-008 — Product data source
- Status: OPEN
- Context: Candidate routes include a curated dataset, affiliate feeds, permitted retailer/marketplace APIs, product-search services, manufacturer documentation, and direct retailer feeds. No provider is approved yet; access rights and available fields must be verified.

## D-009 � Core domain model with provenance and freshness (M1)
- Status: ACCEPTED
- Date: 2026-10-13
- Decision: Implemented a source-neutral core data model comprising Product (canonical identity), SellerOffer (seller-specific price/condition), PriceObservation (time-series price snapshot), ProductSpecification (key/value attrs with explicit Evidence), SourceRef / Evidence provenance, and a deterministic freshness() policy. Validation is hand-written (no pydantic dependency in M1) but the shape is pydantic-compatible for future migration. Package layout is flat `aba/` at repo root for zero-install import. Demo catalog fixture is clearly labelled `is_demo=true` and the loader aborts if any fixture lacks it, preventing accidental presentation of demo data as live.
- Consequences: Every later layer (requirement profiling, constraint filtering, LLM explanation) can rely on explicit, provenance-rich records rather than implicit LLM assumptions. The model enforces hard constraints (budget, currency format, UTC datetimes) by code before any ranking. The `is_demo` gate is the single kill-switch separating demo fixtures from live offers. The design stays category- and market-agnostic so D-006/D-007 remain open. Drawback: adding a new dependency (pydantic) or changing the layout would require a follow-up refactor.


## D-010 � LLM-grounded recommendation layer (M4)
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
