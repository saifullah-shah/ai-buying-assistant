# Product Requirements — Initial Draft

Status: DRAFT / NOT YET APPROVED

## User problem
Consumers have trouble choosing among many products, understanding specifications, balancing requirements against budget, and determining whether seller offers and claims are trustworthy.

## Intended core workflow
1. User describes the intended purchase, needs, budget, market, and must-haves.
2. The assistant asks targeted clarification questions only when missing information materially affects suitability.
3. The app creates a validated, structured requirement profile.
4. It retrieves candidates and offers from configured permitted sources or a clearly labeled test catalog.
5. It normalizes products/offers, deduplicates carefully, validates data, and retains provenance.
6. It filters out candidates that fail hard constraints.
7. It ranks remaining candidates using explicit deterministic scoring and user-adjustable preferences.
8. The LLM explains why each candidate fits, what it sacrifices, and what remains unknown.
9. The user can compare alternatives, change preferences, and refine the shortlist.

## Functional requirements for a first prototype
- Natural-language requirement intake.
- Structured schema for budget, currency, country/market, category, condition, hard constraints, and weighted preferences.
- A bounded product catalog with category-specific attributes.
- A separate seller-offer model containing seller, currency, price, product URL, conditions, and observation timestamp.
- Evidence/source references for important specifications and offers.
- Product candidate retrieval via an adapter interface.
- Deterministic hard filtering and scoring.
- Evidence-grounded recommendation text.
- Comparison of selected candidates.
- Clear stale/missing/unknown data indicators.
- A small evaluation set and automated tests.

## Non-functional requirements
- Security: no secrets in source control; validate inputs; avoid arbitrary SQL from an LLM; constrain tool capabilities.
- Reliability: tests for hard constraints, product matching, missing data, stale offers, and source failures.
- Traceability: every displayed offer has a source reference and observation time.
- Modularity: source integrations should not be tightly coupled to the scoring engine or specific LLM provider.
- Cost control: log requests and approximate model/source costs when feasible.
- Privacy: minimize stored personal data; persistence of preferences must be deliberate and controllable.

## Acceptance criteria for the first meaningful end-to-end demo
- A test request turns into a validated requirement object.
- Candidate products come only from the seeded/test catalog or a source explicitly marked as configured.
- Mandatory requirements are enforced before scoring.
- A candidate over a strict budget is never labelled as compliant.
- Scores are calculated by code and can be explained from named score components.
- Claims in the buyer guide come from product/evidence records; unsupported fields are marked unknown.
- Each offer displays its currency, source, and last-observed timestamp.
- Tests run and their actual results are recorded.

## Not decided yet
- First category and market.
- Data provider(s), licensing, and affiliate access.
- Final score components/weights.
- Account/authentication requirements.
- Production hosting and UI choices.
