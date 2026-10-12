# Research and Hallucination-Control Protocol

Use this protocol for ChatGPT, OpenCode, and any other AI research helper.

## Required output labels
Every important statement should fit one of these categories:
- `VERIFIED FACT`: supported by a checked source or a test we actually ran.
- `INFERENCE`: conclusion drawn from stated facts; explain the reasoning.
- `ASSUMPTION`: a temporary working premise, not established evidence.
- `UNVERIFIED`: plausible but not checked against adequate evidence.
- `RECOMMENDATION`: advice based on constraints and evidence.

## Source hierarchy
1. Official provider/API/product documentation, policy, contracts, release notes, standards, or source repository.
2. Directly run experiments and responses from the actual account/environment (especially for access and behavior).
3. High-quality independent technical sources or research papers.
4. Community posts/blogs for leads only unless independently corroborated.
5. Search snippets or AI-generated claims are not sufficient evidence for important decisions.

## Research workflow
1. Turn the question into specific claims that need evidence.
2. Search for primary sources and note publication/update and access dates.
3. Open the sources and check that each one supports the associated claim.
4. For APIs, verify authentication, approval, quotas, supported markets, returned fields, cost, and data rights separately.
5. Where possible, perform a small request/test and save a sanitized result. Documentation alone does not prove our access works.
6. Record contradictory evidence, caveats, and unresolved questions.
7. Give a recommendation only after separating facts from assumptions.
8. Add a research-log entry before relying on the result in implementation.

## Anti-hallucination behavior
- Never fabricate URLs, citations, sources, API parameters, output fields, prices, quotas, policy statements, or test results.
- If evidence is missing, say what is unknown and propose a way to check it.
- Do not say a provider supports something just because a related API exists.
- Do not claim code works unless it was run or clearly say it is untested.
- Do not use made-up product offers in production UI. Use clearly labelled test fixtures.
- For changing facts, recheck current official documentation before implementation.
- Use precise dates instead of "recently" or "currently" when a date matters.
- For critical claims, seek a second independent confirmation or conduct a direct test.
