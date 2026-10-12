# Reusable ChatGPT Research Prompts

## A. Research a product-data provider

Research [PROVIDER] for our AI Buying Decision Assistant targeting [MARKET] and [CATEGORY]. Browse current official documentation and terms. Do not assume access is available just because an API exists.

Answer with:
1. Exact product/API/feed and intended use.
2. Supported market and category.
3. Eligibility, registration, review and approval requirements.
4. Authentication steps and a minimal request/example from official docs.
5. Relevant returned fields and known freshness limitations.
6. Rate limits, pricing, and quotas if documented.
7. Rules for displaying, storing, caching, retaining price history, and images.
8. Affiliate tracking and eligibility, if relevant.
9. A minimal test we should perform with our own account.
10. Evidence table: claim, official source URL, what it supports, date checked.

Label each statement VERIFIED FACT, INFERENCE, ASSUMPTION, or UNVERIFIED. If the official docs do not answer a point, say so instead of guessing. End with a recommendation and explicit unresolved questions.

## B. Review a technical proposal

Review the attached proposal in the context of the project brief and decision log. Identify factual claims that need sources, hidden assumptions, overengineering, security risks, failure modes, and test gaps. Do not rewrite the whole architecture by default. Separate must-fix issues from optional improvements and give a small next step.

## C. Convert research into a coding task

Using the current project brief, decision log, and research evidence below, create one small implementation task for OpenCode. Include goal, scope, out-of-scope items, acceptance criteria, files likely to change, tests, known limitations, and any source links. Do not introduce unaccepted decisions. If research does not prove access/permission, keep the provider integration mocked or behind an interface and label it clearly.

## D. Verify a claim

Claim to verify: [CLAIM]
Find the strongest current primary source. Open it and check the specific passage. Tell me whether it supports the claim fully, partially, or not at all. Show the date/context, important caveats, and what direct test would still be needed. Do not defend the claim if the evidence contradicts it.

## E. Anti-hallucination review of an answer

Audit the answer below. Extract every external factual claim, API capability, price, policy, date, and asserted test result. For each, label supported / partly supported / unsupported / stale, and identify a primary source or direct test needed. Flag fabricated-looking specificity. Rewrite only after the audit, preserving uncertainty and adding citations where available.
