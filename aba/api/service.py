"""Discovery / shortlist service.

Every filtering decision in this module is delegated to the existing, tested M3
helpers in :mod:`aba.shortlist.filter` (and the M1 freshness policy).  Nothing
here re-implements constraint logic; this module only:

1. builds canonical ``Requirement`` objects from an HTTP query,
2. calls ``get_shortlist``-equivalent helpers,
3. assembles a JSON-friendly view model for the UI.

Rejected candidates are **not** discarded silently: the response carries a
``rejected`` array with the specific failed constraint so the UI can explain why
something did not appear.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from aba.domain.freshness import FreshnessStatus, freshness
from aba.domain.provenance import Product, SellerOffer
from aba.requirements.model import Requirement, RequirementValidationResult
from aba.shortlist.filter import (
    _check_budget,
    _check_condition,
    _check_must_haves,
    _score_nice_to_haves,
)

from aba.api.dataset import COMPARABLE_SPEC_KEYS, SPEC_LABELS, build_catalog, offer_view, product_view

#: Condition values the frontend may request.
VALID_CONDITIONS = ("new", "refurbished", "used", "open-box")

#: Sort options exposed to the UI.
SORT_OPTIONS = (
    "relevance",
    "price_asc",
    "price_desc",
    "ram_desc",
    "screen_desc",
    "weight_asc",
)


def _spec_map(product: Product) -> Dict[str, Any]:
    return {spec.key: spec.value for spec in product.specs}


def _numeric(value: Any) -> Optional[float]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def build_requirement(
    need_description: str,
    budget_amount: Optional[float],
    budget_currency: str = "PKR",
    market: str = "PK",
    condition: Optional[str] = None,
    must_haves: Optional[List[str]] = None,
    nice_to_haves: Optional[List[str]] = None,
) -> Requirement:
    """Construct an ``aba.requirements.model.Requirement``.

    Raises ``ValueError`` from the M2 schema when the input is invalid — the
    caller surfaces that as HTTP 400 with the M2 error strings.
    """
    return Requirement(
        need_description=need_description,
        budget_amount=float(budget_amount) if budget_amount else 1.0,
        budget_currency=budget_currency,
        market=market,
        condition=condition,
        must_haves=frozenset(must_haves or ()),
        nice_to_haves=frozenset(nice_to_haves or ()),
    )


def _use_case_hints(text: str) -> Dict[str, Any]:
    """Derive *suggested* spec keys from free text.

    This is a transparent keyword map, not an LLM and not a score.  It only ever
    produces **nice-to-have suggestions** which the UI shows to the user for
    confirmation; it never silently hard-filters on an inferred key.
    """
    lowered = text.lower()
    hints: Dict[str, List[str]] = {}
    rules = (
        (("study", "university", "college", "school", "assignment", "exam"),
         ["ram_gb", "storage_gb", "weight_kg"]),
        (("program", "coding", "software", "developer", "engineer"),
         ["ram_gb", "cpu"]),
        (("machine learning", "ml", "ai", "data science", "deep learning"),
         ["ram_gb", "gpu", "storage_gb"]),
        (("gaming", "game", "valorant", "pubg", "fps"),
         ["gpu", "ram_gb"]),
        (("light", "portable", "travel", "commute", "carry"),
         ["weight_kg", "screen_size_in"]),
        (("office", "word", "excel", "office work", "accounting"),
         ["ram_gb", "cpu"]),
        (("design", "photo", "video", "creative", "editing"),
         ["ram_gb", "screen_size_in", "gpu"]),
    )
    for keywords, keys in rules:
        if any(word in lowered for word in keywords):
            for key in keys:
                hints.setdefault(key, [])
                if key not in hints[key]:
                    hints[key].append(key)
    return {"suggested_nice_to_haves": sorted(hints.keys())}


def discover(
    query: Optional[str] = None,
    budget_amount: Optional[float] = None,
    budget_currency: str = "PKR",
    condition: Optional[str] = None,
    must_haves: Optional[List[str]] = None,
    nice_to_haves: Optional[List[str]] = None,
    min_ram: Optional[float] = None,
    min_storage: Optional[float] = None,
    max_weight: Optional[float] = None,
    min_screen: Optional[float] = None,
    sort: str = "relevance",
) -> Dict[str, Any]:
    """Run the real M3 hard-constraint logic and return a UI-ready result.

    Hard constraints, applied in this order by existing M3 helpers:
      1. budget — currency must match and price must not exceed budget
      2. condition — offer condition must match when one is requested
      3. must-haves — every required spec key must have a *known* value
    Nice-to-haves are *scored*, never used to reject.
    """
    products, offers, meta = build_catalog()
    by_id: Dict[str, Product] = {p.product_id: p for p in products}
    specs_by_id: Dict[str, Tuple] = {p.product_id: p.specs for p in products}

    notes: List[str] = []
    validation: Optional[RequirementValidationResult] = None
    effective_budget = float(budget_amount) if budget_amount else None

    if effective_budget is not None and effective_budget <= 0:
        validation = RequirementValidationResult(
            is_valid=False,
            errors=("budget_amount must be positive",),
            requirement=None,  # type: ignore[arg-type]
        )

    matched: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []

    for offer in offers:
        if not offer.is_demo:
            continue
        product = by_id.get(offer.product_id)
        if product is None:
            continue
        p_specs = specs_by_id.get(offer.product_id, ())
        smap = _spec_map(product)

        # --- 1. budget (real M3 helper) -------------------------------
        if effective_budget is None:
            budget_ok = True
            budget_reason = "No budget supplied — budget check skipped."
        else:
            budget_ok = _check_budget(
                offer.price_amount, offer.price_currency, effective_budget, budget_currency
            )
            budget_reason = (
                f"Price {offer.price_amount:,.0f} {offer.price_currency} "
                f"vs budget {effective_budget:,.0f} {budget_currency}"
            )

        # --- 2. condition (real M3 helper) ----------------------------
        condition_ok = _check_condition(offer.condition, condition)

        # --- 3. must-haves (real M3 helper) ---------------------------
        must_ok = _check_must_haves(p_specs, frozenset(must_haves or ()))

        # --- soft spec sliders (UI filters, not M3 constraints) ------
        slider_failures: List[str] = []
        if min_ram is not None:
            ram = _numeric(smap.get("ram_gb"))
            if ram is None or ram < min_ram:
                slider_failures.append(
                    f"RAM {smap.get('ram_gb', 'unknown')} GB is below the requested {min_ram:g} GB"
                )
        if min_storage is not None:
            storage = _numeric(smap.get("storage_gb"))
            if storage is None or storage < min_storage:
                slider_failures.append(
                    f"Storage {smap.get('storage_gb', 'unknown')} GB is below the requested {min_storage:g} GB"
                )
        if max_weight is not None:
            weight = _numeric(smap.get("weight_kg"))
            if weight is None or weight > max_weight:
                slider_failures.append(
                    f"Weight {smap.get('weight_kg', 'unknown')} kg exceeds the requested {max_weight:g} kg"
                )
        if min_screen is not None:
            screen = _numeric(smap.get("screen_size_in"))
            if screen is None or screen < min_screen:
                slider_failures.append(
                    f"Screen {smap.get('screen_size_in', 'unknown')} in is below the requested {min_screen:g} in"
                )

        failed: List[str] = []
        if not budget_ok:
            failed.append("budget")
        if not condition_ok:
            failed.append("condition")
        if not must_ok:
            failed.append("must_haves")
        if slider_failures:
            failed.append("filters")

        nth_score, nth_total = _score_nice_to_haves(
            p_specs, frozenset(nice_to_haves or ())
        )

        record = {
            "product": product_view(product),
            "offer": offer_view(offer),
            "matches": {
                "budget": budget_ok,
                "condition": condition_ok,
                "must_haves": must_ok,
                "filters_ok": not slider_failures,
                "nice_to_haves_score": nth_score,
                "nice_to_haves_total": nth_total,
            },
            "reasons": {
                "budget": budget_reason,
                "condition": (
                    "No condition requested."
                    if condition is None
                    else (f"Offer condition '{offer.condition.value}' matches."
                          if condition_ok else
                          f"Offer condition '{offer.condition.value}' does not match '{condition}'.")
                ),
                "must_haves": (
                    "No must-have specs required."
                    if not must_haves else
                    ("All required specs have known values."
                     if must_ok else "One or more required specs are missing or undisclosed.")
                ),
                "filters": slider_failures,
            },
        }

        if failed:
            record["failed_constraints"] = failed
            rejected.append(record)
        else:
            matched.append(record)

    # --- sorting ------------------------------------------------------
    def sort_key(item: Dict[str, Any]):
        product_obj = by_id[item["product"]["product_id"]]
        pmap = _spec_map(product_obj)
        price = item["offer"]["price_amount"]
        ram = _numeric(pmap.get("ram_gb")) or 0.0
        screen = _numeric(pmap.get("screen_size_in")) or 0.0
        weight = _numeric(pmap.get("weight_kg"))
        weight = weight if weight is not None else 99.0
        if sort == "price_asc":
            return (price,)
        if sort == "price_desc":
            return (-price,)
        if sort == "ram_desc":
            return (-ram, price)
        if sort == "screen_desc":
            return (-screen, price)
        if sort == "weight_asc":
            return (weight, price)
        # relevance: preference matches, then cheaper first
        return (-item["matches"]["nice_to_haves_score"], price)

    matched.sort(key=sort_key)

    if query:
        notes.append(
            f"Filtered {len(offers)} curated demo offers against your criteria; "
            f"{len(matched)} matched."
        )
    else:
        notes.append(
            f"Showing all {len(matched)} curated demo laptops. Add a budget or filters to narrow."
        )

    hints = _use_case_hints(query) if query else {"suggested_nice_to_haves": []}

    return {
        "meta": meta,
        "query": query,
        "budget_amount": effective_budget,
        "budget_currency": budget_currency,
        "condition": condition,
        "sort": sort,
        "total_matched": len(matched),
        "total_considered": len(offers),
        "results": matched,
        "rejected": rejected,
        "notes": notes,
        "hints": hints,
        "validation": {
            "is_valid": validation.is_valid if validation else True,
            "errors": list(validation.errors) if validation else [],
        },
    }


def get_product(product_id: str) -> Optional[Dict[str, Any]]:
    """Return the full detail view for one product, or ``None`` if not in catalog."""
    products, offers, meta = build_catalog()
    product = next((p for p in products if p.product_id == product_id), None)
    if product is None:
        return None

    product_offers = [offer_view(o) for o in offers if o.product_id == product_id]

    # Deterministic trade-off summary computed from the *record itself* — never
    # from an LLM opinion, and never inventing a missing value.
    # `is_unknown()` (not a plain `is None` test) is the source of truth, so
    # sentinel values such as "Not specified" are correctly reported as unknown.
    specs_view = product_view(product)["specs"]
    unknown_labels = [s["label"] for s in specs_view if s["is_unknown"]]
    unknown_keys = [s["key"] for s in specs_view if s["is_unknown"]]

    return {
        "product": product_view(product),
        "offers": product_offers,
        "meta": meta,
        "unknown_fields": unknown_labels,
        "unknown_field_keys": unknown_keys,
    }


def compare(product_ids: List[str]) -> Dict[str, Any]:
    """Build a side-by-side comparison from the curated catalog."""
    products, offers, meta = build_catalog()
    by_id = {p.product_id: p for p in products}
    chosen: List[Dict[str, Any]] = []
    for pid in product_ids:
        if pid not in by_id:
            continue
        product = by_id[pid]
        product_offers = [o for o in offers if o.product_id == pid]
        entry = {
            "product": product_view(product),
            "offer": offer_view(product_offers[0]) if product_offers else None,
            "offer_count": len(product_offers),
        }
        chosen.append(entry)

    rows: List[Dict[str, Any]] = []
    for key in COMPARABLE_SPEC_KEYS:
        cells = []
        for entry in chosen:
            spec = next((s for s in entry["product"]["specs"] if s["key"] == key), None)
            if spec is None:
                cells.append({"value": None, "is_unknown": True, "display": "Not listed"})
            elif spec["is_unknown"]:
                cells.append(
                    {"value": spec["value"], "is_unknown": True, "display": "Unknown"}
                )
            else:
                unit = f" {spec['unit']}" if spec["unit"] else ""
                cells.append(
                    {"value": spec["value"], "is_unknown": False, "display": f"{spec['value']}{unit}"}
                )
        rows.append(
            {
                "key": key,
                "label": SPEC_LABELS.get(key, key),
                "cells": cells,
            }
        )

    return {"meta": meta, "products": chosen, "rows": rows}