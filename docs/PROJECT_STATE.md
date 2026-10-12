# Project State / Handoff

Last updated: 2026-10-12

## Current stage
Concept and architecture planning. This note is based on discussion, not an inspection of the local repository. The next OpenCode session must inspect the actual working tree and Git status before making assumptions about implemented code.

## Known goals
- Build a long-running AI Buying Decision Assistant project incrementally.
- Initial experience: describe need/budget, receive a researched shortlist with transparent trade-offs.
- Future possibilities: price changes, compatibility, alternatives, warranty/returns management.
- Learn practical AI engineering and MCP along the way.
- Use OpenCode in VS Code for coding and ChatGPT Free for research/independent review.
- Focus on product capability now; competitor positioning and commercial validation are deferred.

## Work established in planning
- Identified product catalog, seller offers, evidence, and historical price observations as separate data concerns.
- Discussed candidate retrieval routes: curated dataset, affiliate feeds, retailer APIs, product-search providers, manufacturer documentation, and direct retailer agreements.
- Proposed canonical product/offer/evidence/price snapshot records.
- Proposed deterministic filtering/ranking with LLM-generated explanations grounded in sourced fields.

## Not yet verified
- Actual repository state and existing implementation.
- First category and market.
- Any production API/feed access, approvals, costs, current terms, or data-storage/reuse permissions.
- Exact scoring formula and evaluation thresholds.
- Final UI and deployment choices.

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
