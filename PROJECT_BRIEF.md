# Project Brief — AI Buying Decision Assistant

## Product vision
Build an AI application that helps consumers make better purchase decisions by comparing products against their budget, requirements, and long-term preferences.

The initial experience should let a user describe a need and budget in natural language and receive a researched shortlist with clear trade-offs and traceable sources. Over time, the application may monitor price changes, check compatibility, compare alternatives, and help users organize warranties and returns.

## Product principles
1. Evidence before confident claims.
2. Explain trade-offs rather than merely list products.
3. Hard requirements are enforced by code before preference ranking.
4. Separate product identity from seller offers and historical observations.
5. Show source, currency, and last-observed time for prices.
6. Unknown facts must remain unknown, not be guessed by an LLM.
7. Keep the system extensible but only implement one well-scoped category/market at a time.

## Current development approach
- Work incrementally in VS Code using OpenCode.
- Use ChatGPT Free for research, architecture discussion, prompt review, and independent critique.
- Learn and implement MCP by exposing useful, tested product-data and comparison services as tools after the core functions exist.
- Use Git commits for small, reversible milestones.
- Treat documentation in this repository as the project record, not chat history.

## Provisional technical direction
These are proposals, not irreversible decisions:
- Backend: Python + FastAPI.
- Validation: Pydantic.
- Database: PostgreSQL; category-specific attributes may use JSONB alongside normal indexed columns.
- Frontend: Next.js/React, if a web UI is chosen for the MVP.
- AI: LLM for need parsing, clarification, tool selection, and explanation; deterministic code for constraints, matching, and scores.
- Sources: start with a small curated dataset and one verified, permitted source of live offers; add adapters only when they bring measurable coverage.
- MCP: expose stable application functions such as `search_products`, `get_product_details`, and `compare_products` through a server once those functions work.

## Out of scope for the first milestone
- Support for every product category.
- Autonomous purchases or payment handling.
- Fully automated warranty claims/returns.
- Complex multi-agent architecture.
- Large-scale scraping without source permission and data-quality controls.
- Price alerts before offer refresh and timestamp handling are reliable.

## Choices still open
- Launch market (Pakistan or another market).
- First product category (laptops are a candidate, not a finalized decision).
- Actual data provider(s) and access rights.
- Exact frontend and hosting choices.
- Monetization implementation. Affiliate revenue and premium features are future hypotheses, not current requirements.

## Competition and commercial validation
The user explicitly wants to focus first on building a genuinely capable product. Detailed competitor positioning and commercial validation are deferred to a later stage. Do not repeatedly redirect early engineering work into market validation unless the user asks or a technical decision depends on it.

## Definition of a successful early prototype
Given a bounded and traceable catalog, the application can parse a user request into validated requirements, retrieve candidate products, enforce mandatory constraints, rank candidates with explicit rules, and produce an explanation whose factual claims are traceable to supplied evidence. The prototype clearly labels demo data and does not pretend demo offers are live.
