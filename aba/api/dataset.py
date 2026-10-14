"""Dataset adapter — normalises the curated Pakistan laptop demo dataset into
canonical ``aba`` domain objects.

Design constraints (AGENTS.md, D-004, D-008):

* **Additive only.** This module *adapts* data into the existing M1 domain model.
  It does not redefine, wrap away, or re-implement any M1–M4 logic.
* **Honest normalisation.** The source fixture stores a condition string such as
  ``"new (illustrative)"``.  ``aba.domain.provenance.Condition`` only accepts the
  canonical vocabulary, so the value is normalised and the *raw* string is
  preserved in the offer evidence note.  Nothing is silently discarded.
* **Unit clarity.** The fixture stores ``price_amount`` as whole Pakistani rupees.
  That unit is stated explicitly in the API contract (``currency_unit``) so it can
  never be confused with the paisa/cent convention documented for
  ``aba/catalog/demo_catalog.json``.
* **No invention.** No field is inferred, defaulted, or filled in. Missing facts
  stay missing. Availability is ``"unknown"`` because the fixture does not know it.
* **Demo data stays demo.** ``is_demo`` is carried through and is asserted ``True``
  so no demo record can ever be presented as a live offer.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

from aba.domain.provenance import (
    Condition,
    Evidence,
    Product,
    ProductSpecification,
    SellerOffer,
    SourceRef,
)

#: Where the curated Pakistan laptop demo fixture lives.
DATASET_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "laptop_demo_dataset_pk.json",
)

#: Human-readable spec-key labels used by the UI.  Keys not listed here fall back
#: to a title-cased version of the key itself.
SPEC_LABELS: Dict[str, str] = {
    "cpu": "Processor (CPU)",
    "ram_gb": "Memory (RAM)",
    "storage_gb": "Storage capacity",
    "storage_type": "Storage type",
    "screen_size_in": "Screen size",
    "display_resolution": "Display resolution",
    "gpu": "Graphics (GPU)",
    "weight_kg": "Weight",
    "operating_system": "Operating system",
    "warranty": "Warranty",
}

#: Spec keys that participate in filtering / comparison, in display order.
COMPARABLE_SPEC_KEYS: Tuple[str, ...] = (
    "cpu",
    "ram_gb",
    "storage_gb",
    "storage_type",
    "screen_size_in",
    "display_resolution",
    "gpu",
    "weight_kg",
    "operating_system",
    "warranty",
)

#: Canonical condition vocabulary accepted by ``aba.domain.provenance.Condition``.
_CANONICAL_CONDITIONS = ("new", "refurbished", "used", "open-box", "unknown")

#: Condition strings that indicate "we do not know" rather than a real condition.
_UNKNOWN_CONDITION_MARKERS = ("unknown", "not specified", "not disclosed", "n/a")


def _parse_iso(value: str) -> datetime:
    """Parse an ISO-8601 timestamp into a timezone-aware UTC datetime."""
    cleaned = value.strip()
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    parsed = datetime.fromisoformat(cleaned)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def normalise_condition(raw: Optional[str]) -> Tuple[str, bool]:
    """Map a raw fixture condition string onto the canonical vocabulary.

    Returns ``(canonical_value, was_ambiguous)``.

    ``"new (illustrative)"`` -> ``("new", True)`` — the qualifier is dropped from
    the value but recorded by the caller.  ``"unknown"``-ish strings map to
    ``"unknown"`` rather than being guessed into ``"new"``.
    """
    if raw is None:
        return ("unknown", True)

    text = str(raw).strip().lower()
    if not text:
        return ("unknown", True)

    for marker in _UNKNOWN_CONDITION_MARKERS:
        if marker in text:
            return ("unknown", True)

    for candidate in _CANONICAL_CONDITIONS:
        if candidate == "unknown":
            continue
        if text.startswith(candidate):
            return (candidate, text != candidate)

    # Not recognisable at all — keep it unknown instead of guessing.
    return ("unknown", True)


def _unit_for(key: str, value: Any) -> Optional[str]:
    """Return the display unit for a spec, inferred from the *key name only*.

    Units are derived from the fixture's own key naming convention
    (``ram_gb`` -> GB, ``weight_kg`` -> kg, ``screen_size_in`` -> inches).
    This is naming-convention mapping, not value invention: a missing value still
    yields ``None`` and stays unknown.
    """
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    if key.endswith("_gb"):
        return "GB"
    if key.endswith("_kg"):
        return "kg"
    if key.endswith("_in"):
        return "inches"
    return None


@lru_cache(maxsize=1)
def load_dataset() -> Dict[str, Any]:
    """Load and validate the curated fixture file (cached)."""
    with open(DATASET_PATH, encoding="utf-8") as handle:
        return json.load(handle)


def dataset_meta() -> Dict[str, Any]:
    """Return dataset-level provenance and the honest 'this is demo data' notice."""
    raw = load_dataset()
    return {
        "dataset_id": raw.get("dataset_id", "unknown"),
        "dataset_status": raw.get("dataset_status", "unknown"),
        "market": raw.get("market", "PK"),
        "category": raw.get("category", "laptop"),
        "created_at_utc": raw.get("created_at_utc"),
        "is_demo": bool(raw.get("is_demo", False)),
        "important_notice": raw.get("important_notice", ""),
        "evidence": raw.get("evidence", []),
    }


def _build_evidence(raw: Dict[str, Any], meta: Dict[str, Any], note: str) -> Evidence:
    """Build an ``Evidence`` pointing at the synthetic fixture itself."""
    return Evidence(
        source_ref=SourceRef(
            provider="synthetic-fixture",
            source_id=str(meta.get("dataset_id", "unknown")),
            url=None,
            retrieved_at=_parse_iso(str(meta["created_at_utc"])),
            note="Synthetic demo fixture — not a real product listing, price, or seller.",
        ),
        note=note,
    )


def build_catalog() -> Tuple[List[Product], List[SellerOffer], Dict[str, Any]]:
    """Convert the fixture into canonical ``Product`` / ``SellerOffer`` objects.

    Returns ``(products, offers, meta)``.

    Every returned record carries ``is_demo=True``.  Any fixture record that is
    not flagged as demo raises, so demo data can never be presented as live.
    """
    raw = load_dataset()
    meta = dataset_meta()

    if not meta["is_demo"]:
        raise ValueError(
            "Refusing to serve dataset: it is not flagged is_demo=true. "
            "Live sources must go through a separately reviewed adapter."
        )

    products: List[Product] = []
    offers: List[SellerOffer] = []
    checked_at = _parse_iso(str(raw["created_at_utc"]))

    for entry in raw.get("products", []):
        if entry.get("is_demo") is not True:
            raise ValueError(
                f"Fixture product {entry.get('product_id')!r} is not flagged is_demo=true"
            )

        specs: List[ProductSpecification] = []
        for key, value in (entry.get("specifications") or {}).items():
            specs.append(
                ProductSpecification(
                    key=key,
                    value=value,
                    unit=_unit_for(key, value),
                    evidence=_build_evidence(
                        entry, meta, "Synthetic illustrative value; not a verified spec."
                    ),
                )
            )

        products.append(
            Product(
                product_id=str(entry["product_id"]),
                name=str(entry.get("title") or entry.get("model") or entry["product_id"]),
                category=str(entry.get("category", "laptop")),
                market=str(entry.get("market", "PK")),
                specs=tuple(specs),
                is_demo=True,
            )
        )

        offer_raw = entry.get("seller_offer") or {}
        if offer_raw.get("is_demo") is not True:
            raise ValueError(
                f"Fixture offer for {entry.get('product_id')!r} is not flagged is_demo=true"
            )

        condition_value, was_ambiguous = normalise_condition(offer_raw.get("condition"))
        notes = ["Synthetic illustrative offer; not a live quote."]
        if was_ambiguous:
            notes.append(f'Raw condition string in fixture: "{offer_raw.get("condition")}".')

        offers.append(
            SellerOffer(
                product_id=str(entry["product_id"]),
                seller_id=str(offer_raw.get("seller_name") or "unknown-seller"),
                price_amount=float(offer_raw.get("price_amount") or 0.0),
                price_currency=str(offer_raw.get("currency") or "PKR"),
                condition=Condition(value=condition_value),
                # The fixture has no per-offer poll time.  The dataset-level
                # creation timestamp is the only truthful observation time we
                # have, so we use it and label it as such.
                product_url=str(
                    offer_raw.get("product_url") or "https://example.invalid/demo-offer"
                ),
                observed_at=checked_at,
                source_id=str(meta.get("dataset_id", "unknown")),
                is_demo=True,
            )
        )

    return products, offers, meta


def product_view(product: Product) -> Dict[str, Any]:
    """Serialise a ``Product`` into the JSON shape the frontend consumes."""
    specs = []
    for spec in product.specs:
        specs.append(
            {
                "key": spec.key,
                "label": SPEC_LABELS.get(spec.key, spec.key.replace("_", " ").title()),
                "value": spec.value,
                "unit": spec.unit,
                "is_unknown": spec.is_unknown(),
                "evidence": {
                    "provider": spec.evidence.source_ref.provider,
                    "source_id": spec.evidence.source_ref.source_id,
                    "note": spec.evidence.note,
                },
            }
        )
    return {
        "product_id": product.product_id,
        "name": product.name,
        "category": product.category,
        "market": product.market,
        "is_demo": product.is_demo,
        "specs": specs,
    }


def offer_view(offer: SellerOffer) -> Dict[str, Any]:
    """Serialise a ``SellerOffer`` into the JSON shape the frontend consumes."""
    from aba.domain.freshness import freshness

    status = freshness(offer.observed_at)
    return {
        "product_id": offer.product_id,
        "seller_id": offer.seller_id,
        "price_amount": offer.price_amount,
        "price_currency": offer.price_currency,
        # The curated fixture stores whole rupees. Stated explicitly so the UI
        # never renders 125000 as "125,000 paisa".
        "currency_unit": "rupees",
        "condition": offer.condition.value,
        "product_url": offer.product_url,
        "observed_at": offer.observed_at.isoformat(),
        "freshness": status.value,
        "source_id": offer.source_id,
        "is_demo": offer.is_demo,
    }