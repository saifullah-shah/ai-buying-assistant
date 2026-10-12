"""Grounding rules and evidence-citation logic for M4 LLM-grounded recommendation layer.

All functions are pure (no LLM, no API, no external services) and designed for
deterministic testing.  They map M1 domain model fields to the text the LLM
should cite, and produce the "unknown + why" labels that the prompt template
expects.

Design (RESEARCH_PROTOCOL.md, D-004):
- Source hierarchy: product spec evidence > offer observed_at + source_id
- Unknown fields are explicitly labelled, never guessed
- Every factual claim must trace back to a source_ref + observed_at (or documented reason)
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Evidence citation from M1 domain model fields
# ---------------------------------------------------------------------------

def make_evidence_citation(spec_evidence: Optional[Dict[str, Any]]) -> str:
    """Produce a citation string from a ProductSpecification's Evidence.

    Maps to the format expected in the prompt template's spec_evidence blocks.
    If evidence is missing, returns a standardized "unknown" marker.
    """
    if not spec_evidence:
        return "unknown (no evidence provided)"

    provider = spec_evidence.get("provider", "unknown")
    source_id = spec_evidence.get("source_id", "")
    note = spec_evidence.get("note", "")

    parts: List[str] = [f"provider={provider}"]
    if source_id:
        parts.append(f"source_id={source_id}")
    if note:
        parts.append(f'note="{note}"')

    return ", ".join(parts)


def classify_unknown_reason(spec: Dict[str, Any]) -> str:
    """Determine why a specification is unknown, based on its data.

    Used by the grounding logic to produce the "UNKNOWN AND WHY" section text.
    Returns a short human-readable reason.
    """
    # If value is None or empty, value-missing reason
    if spec.get("value") in (None, ""):
        return "value not provided"

    # If evidence provider is "unknown" or empty
    ev = spec.get("product_spec_evidence", {})
    provider = ev.get("provider", "")
    if not provider or provider == "unknown":
        return "vendor did not provide this specification"

    # If evidence exists but no note — check if value seems absent
    if not spec.get("value"):
        return "specification not disclosed in API response"

    # Default: known (should not reach here if caller logic is correct)
    return "known"


# ---------------------------------------------------------------------------
# Unknown-field labeling for "UNKNOWN AND WHY" section
# ---------------------------------------------------------------------------

def build_unknown_entries(
    product_specs: List[Dict[str, Any]],
) -> List[str]:
    """Build the list of "field: unknown — reason" entries for the prompt.

    Scans all product specifications and produces one entry per spec that is
    classified as unknown.  The order follows the spec list order from M3.

    Returns a list of strings like:
    - "screen_size: unknown — value not provided"
    - "cpu_model: unknown — vendor did not provide this specification"
    """
    entries: List[str] = []
    for spec in product_specs:
        if spec.get("value") in (None, ""):
            entries.append(
                f"{spec.get('key', 'unnamed_spec')}: unknown — value not provided"
            )
        else:
            reason = classify_unknown_reason(spec)
            if reason != "known":
                entries.append(
                    f"{spec.get('key', 'unnamed_spec')}: unknown — {reason}"
                )
    return entries


# ---------------------------------------------------------------------------
# Constraint-compliance summary from M3 flags
# ---------------------------------------------------------------------------

def make_constraint_summary(
    budget_pass: bool,
    condition_pass: bool,
    must_haves_pass: bool,
    nice_score: int,
    nice_total: int,
) -> str:
    """Produce the CONSTRAINT COMPLIANCE SUMMARY block text.

    Exactly matches the format in the prompt template so the LLM output
    can be validated against it deterministically.
    """
    budget_str = "compliant" if budget_pass else "non-compliant"
    condition_str = "compliant" if condition_pass else "non-compliant"
    must_haves_str = "compliant" if must_haves_pass else "non-compliant"
    return f"""CONSTRAINT COMPLIANCE SUMMARY:
- Budget: {budget_str}
- Condition: {condition_str}
- Must-haves: {must_haves_str}
- Nice-to-haves matched: {nice_score}/{nice_total}"""


# ---------------------------------------------------------------------------
# Output format validation (deterministic, no LLM)
# ---------------------------------------------------------------------------

def check_prompt_block_presence(
    response: str,
    block_names: List[str],
) -> bool:
    """Check that the LLM's response contains each named block.

    Used by the test suite to verify the prompt structure without calling
    an LLM (by testing the prompt *design* itself), or to validate actual
    LLM output against the expected schema.

    block_names: e.g. ["FITS BECAUSE:", "WHAT IT SACRIFICES:", "UNKNOWN AND WHY:"]
    """
    return all(block in response for block in block_names)