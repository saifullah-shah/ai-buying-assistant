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
