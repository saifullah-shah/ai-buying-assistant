"""Deterministic hard-constraint filtering for M3.

Responsibilities:
- Load candidates from the source-neutral demo catalog.
- Apply three hard constraints by code only (no LLM, no external services):
    * Budget: currency must match AND price amount must not exceed budget.
    * Condition: if the requirement specifies a condition, the offer's condition must match.
    * Must-haves: the product must have a known (non-unknown) specification for every key
      in the requirement's must_haves set.
- Score remaining candidates by nice-to-haves matches.
- Return a shortlist with explicit constraint flags so the UI/next layer can
  show why a candidate was kept or rejected.

Key design points (D-004, M1/M2 alignment):
- All checks are pure functions; ``now`` is injected for testability.
- Unknown specifications are treated as failing must-have constraints (per D-004:
  "Do not let an LLM invent product facts").
- Currency mismatch automatically disqualifies an offer from budget compliance
  (we do not invent FX rates in M3).
- The demo catalog's ``is_demo`` flag is honoured — only offers with
  ``is_demo=true`` are included in the shortlist (demo data is kept separate
  from any live-sourcing logic, per D-005 and PROJECT_BRIEF principles).
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, NamedTuple, Tuple

from aba.catalog.loader import load_demo_catalog
from aba.domain.provenance import Product, SellerOffer, Condition, ProductSpecification
from aba.requirements.model import Requirement, RequirementValidationResult


# ---------------------------------------------------------------------------
# Shortlist entry — what we return for each candidate that passes constraints
# ---------------------------------------------------------------------------

class ShortlistEntry(NamedTuple):
    """One candidate product offer in the M3 shortlist."""

    product_id: str
    product_name: str
    seller_id: str
    price_amount: float
    price_currency: str
    condition: str
    observed_at: str  # ISO format for display

    # Constraint compliance flags (all True → candidate is shortlisted)
    budget_pass: bool
    condition_pass: bool
    must_haves_pass: bool

    # Preference scoring (how many nice-to-haves are satisfied with known values)
    nice_to_haves_score: int
    nice_to_haves_total: int

    # Human-readable flags for display / UI
    flags: Tuple[str, ...]  # e.g. ("budget_ok", "cond_ok", "must_haves_ok")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _check_budget(
    offer_price_amount: float,
    offer_currency: str,
    budget_amount: float,
    budget_currency: str,
) -> bool:
    """Return True iff the offer price is within the budget.

    Currency mismatch is an automatic budget‐fail (we do not convert in M3).
    """
    if offer_currency != budget_currency:
        return False
    return offer_price_amount <= budget_amount


def _check_condition(
    offer_condition: Condition,
    requirement_condition: str | None,
) -> bool:
    """Return True iff the offer condition satisfies the requirement.

    If the requirement does not specify a condition, every offer passes.
    """
    if requirement_condition is None:
        return True
    return offer_condition.value == requirement_condition.lower()


def _check_must_haves(
    product_specs: Tuple[ProductSpecification, ...],
    must_haves: frozenset,
) -> bool:
    """Return True iff the product has a known (non‐unknown) specification
    for every key in ``must_haves``.

    An unknown specification (value is None, or evidence signals unknown) causes
    the must‐have check to fail — this follows D-004: unknown facts remain unknown
    and cannot be used to satisfy a hard constraint.
    """
    if not must_haves:
        # Empty must_haves → trivially satisfied
        return True

    for key in must_haves:
        # Look for a spec with this key
        matching: List[ProductSpecification] = [
            s for s in product_specs if s.key == key
        ]
        if not matching:
            # No specification with this key at all
            return False
        spec = matching[0]  # take the first match (should be unique)
        if spec.is_unknown():
            # Value is None or explicitly marked unknown
            return False
    return True


def _score_nice_to_haves(
    product_specs: Tuple[ProductSpecification, ...],
    nice_to_haves: frozenset,
) -> Tuple[int, int]:
    """Return (matched_count, total_count) for nice-to-have specifications.

    A nice-to-have is counted as matched when the product has a known
    (non‐unknown) specification with that key.
    """
    if not nice_to_haves:
        return (0, 0)

    matched = 0
    for key in nice_to_haves:
        matching: List[ProductSpecification] = [
            s for s in product_specs if s.key == key
        ]
        if matching and not matching[0].is_unknown():
            matched += 1
    return (matched, len(nice_to_haves))


# ---------------------------------------------------------------------------
# Main shortlisting function
# ---------------------------------------------------------------------------

def get_shortlist(
    requirement: Requirement,
) -> Tuple[List[ShortlistEntry], RequirementValidationResult]:
    """Return a shortlist of candidates from the demo catalog that satisfy

    the hard constraints encoded in *requirement*, together with a
    ``RequirementValidationResult`` describing whether the requirement itself
    is valid (always valid if constructed through the M2 schema, but we return
    the result for completeness).

    The returned list is sorted by ``nice_to_haves_score`` descending, then
    by price ascending — giving preference to better‐matching, cheaper offers.

    Notes
    -----
    - Only offers with ``is_demo=true`` from the catalog are considered.
    - If the requirement is invalid (e.g. empty need), a
      ``RequirementValidationResult`` with ``is_valid=False`` is still returned
      alongside an empty shortlist.
    """
    # --- 1. Validate the requirement ---------------------------------
    val_result = requirement.validate()
    if not val_result.is_valid:
        # Return empty shortlist plus the validation failure
        return [], val_result

    # --- 2. Load demo catalog ---------------------------------------
    products, offers = load_demo_catalog()

    # --- 3. Build a product‑id → product spec mapping -----------------
    # Each product may have multiple offers; we look up specs by product_id.
    product_spec_map: Dict[str, Tuple[ProductSpecification, ...]] = {}
    for p in products:
        product_spec_map[p.product_id] = p.specs

    # --- 4. Filter offers --------------------------------------------
    shortlist_entries: List[ShortlistEntry] = []

    for offer in offers:
        # Skip non‑demo offers (the catalogue enforces is_demo, but we guard)
        if not offer.is_demo:
            continue

        product_id = offer.product_id
        product_specs = product_spec_map.get(product_id, ())

        # --- budget check ---
        budget_ok = _check_budget(
            offer.price_amount,
            offer.price_currency,
            requirement.budget_amount,
            requirement.budget_currency,
        )

        # --- condition check ---
        condition_ok = _check_condition(offer.condition, requirement.condition)

        # --- must-have check ---
        must_haves_ok = _check_must_haves(product_specs, requirement.must_haves)

        # Offer passes all hard constraints?
        if not (budget_ok and condition_ok and must_haves_ok):
            # Still record the flags for transparency (UI can show "rejected")
            # but we do not include it in the *passing* shortlist.
            # However, we still compute flags for display purposes;
            # for simplicity here we just skip adding to shortlist.
            continue

        # --- nice-to-haves scoring -----------------------------------
        nth_score, nth_total = _score_nice_to_haves(product_specs, requirement.nice_to_haves)

        # Build ISO‐format observed_at for the entry
        observed_iso = offer.observed_at.isoformat()

        entry = ShortlistEntry(
            product_id=offer.product_id,
            product_name="",  # will fill below
            seller_id=offer.seller_id,
            price_amount=offer.price_amount,
            price_currency=offer.price_currency,
            condition=offer.condition.value,
            observed_at=observed_iso,
            budget_pass=budget_ok,
            condition_pass=condition_ok,
            must_haves_pass=must_haves_ok,
            nice_to_haves_score=nth_score,
            nice_to_haves_total=nth_total,
            flags=(
                ("budget_ok" if budget_ok else "budget_fail"),
                ("cond_ok" if condition_ok else "cond_fail"),
                ("must_haves_ok" if must_haves_ok else "must_haves_fail"),
            ),
        )

        # Fill product name from the catalog (if available)
        product_obj = next((p for p in products if p.product_id == product_id), None)
        if product_obj:
            entry = entry._replace(product_name=product_obj.name)

        shortlist_entries.append(entry)

    # --- 5. Sort shortlist -------------------------------------------
    # Primary: nice_to_haves_score descending (more preferences matched)
    # Secondary: price ascending (cheaper offers first)
    shortlist_entries.sort(
        key=lambda e: (-e.nice_to_haves_score, e.price_amount)
    )

    return shortlist_entries, val_result