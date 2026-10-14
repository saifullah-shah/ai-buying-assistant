"""Marks ``aba.api`` as an additive HTTP/presentation layer.

This package does **not** redefine domain logic. Every endpoint delegates to the
existing, test-validated M1–M4 modules:

* :mod:`aba.domain.provenance` — canonical ``Product`` / ``SellerOffer`` records
* :mod:`aba.domain.freshness`   — deterministic freshness policy
* :mod:`aba.requirements.model`— ``Requirement`` schema and validation
* :mod:`aba.shortlist.filter``  — hard-constraint checks and nice-to-have scoring
* :mod:`aba.explanation.prompts`— the M4 LLM prompt builder
* :mod:`aba.explanation.grounding`` — evidence citation / unknown labelling
"""