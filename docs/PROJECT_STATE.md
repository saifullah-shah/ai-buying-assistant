# Project State / Handoff

Last updated: 2026-10-12

## Current stage
Milestones M1, M2, and M3 complete. M3 adds deterministic candidate retrieval and hard-constraint filtering on top of the M1 domain model and M2 requirement schema. The system can reliably transform a validated requirement into a constrained, shortlisted candidate set using only offline, deterministic code — no provider integrations, no LLM ranking. Category (D-006) and market (D-007) remain OPEN; data provider (D-008) remains OPEN; LLM integration deferred per user directive.

## Work established in planning
- M1: Domain model with provenance (Product, SellerOffer, PriceObservation, ProductSpecification, SourceRef/Evidence), freshness policy, demo catalog with is_demo kill-switch (40 tests).
- M2: Requirement schema with deterministic validation (Requirement + RequirementValidationResult, 14 tests).
- M3: Candidate shortlisting with three hard constraints — budget (currency match + price ≤ budget), condition (offer condition must match requirement if specified), must-haves (product must have known spec for every required key) — plus nice-to-haves scoring and deterministic shortlist sorting (12 tests).
- All validation pure, clock-injective, zero third-party dependencies.
- Package layout: flat aba/ at repo root; shortlist logic in aba/shortlist/.
- Demo catalog clearly labelled is_demo=true; loader aborts if any fixture lacks it.

## Not yet verified
- LLM integration (pending reliable schema, validation, and filtering)
- Production API/feed access, approvals, costs, current terms, or data-storage/reuse permissions.
- Exact scoring formula and evaluation thresholds beyond NTH counting.
- Final UI and deployment choices.
- Category (D-006) and market (D-007) finalisation — remain OPEN as intended.
- Data provider approval (D-008) — remains OPEN.
- LLM integration — deferred per user directive; schema, validation, and filtering must be reliable first.

## Work established in planning
- Product identity (Product) separate from seller offers (SellerOffer) and price observations (PriceObservation) — M1.
- Canonical specification model (ProductSpecification) with explicit evidence and VerificationStatus — M1.
- Freshness policy (freshness()) pure and clock-injective for deterministic testing — M1.
- Demo catalog fixture (demo_catalog.json) clearly labelled is_demo=true; loader rejects any fixture without it — M1.
- .gitignore created from .gitignore.sample (closes secrets gap) — M1.
- Core domain model verified with 40 passing unittest suite — M1.
- **Requirement schema (Requirement + RequirementValidationResult)** — M2.
  - Parses need_description, budget_amount/budget_currency, market, condition, must_haves/nice_to_haves.
  - Validates: non-empty need, positive budget, 3-letter ISO-4217 currency, valid condition enum.
  - validate() is pure, deterministic, returns RequirementValidationResult (is_valid + errors tuple).
  - All validation by hand-written code; no pydantic dependency; zero third-party packages.
- Requirement validation tests (54 tests across test_products.py, test_catalog_loader.py, test_requirements.py) all pass.

## Not yet verified
- LLM integration (pending reliable schema, validation, and filtering)
- Production API/feed access, approvals, costs, current terms, or data-storage/reuse permissions.
- Exact scoring formula and evaluation thresholds.
- Final UI and deployment choices.
- Category (D-006) and market (D-007) finalisation — remain OPEN as intended.
- Data provider approval (D-008) — remains OPEN.
- LLM integration — deferred per user directive; schema and validation must be reliable first.

## Active next task
1. Inspect repository and git status.
2. Review this context pack with the user; do not implement a large scaffold until requested.
3. Select a bounded pilot category/market or create a source-neutral catalog prototype if that choice is intentionally postponed.
4. Build the source access matrix and verify current primary documentation for candidate providers.

## Last completed task
Prepared project-context templates and research/verification workflow. No code implementation is asserted by this file.

## Known blockers / risks
- Source access and terms are not verified.
- Product identity and configuration matching must be tested.
- Current price/availability cannot be promised without timestamping and freshness controls.
