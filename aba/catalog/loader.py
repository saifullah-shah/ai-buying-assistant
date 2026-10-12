"""Catalog loader for the source-neutral demo fixture.

Responsibilities:
- Load ``aba/catalog/demo_catalog.json``.
- Enforce that every loaded record carries ``is_demo=true`` — if any fixture
  lacks ``is_demo`` or has it set to ``false`` the loader raises, preventing
  accidental presentation of demo data as live.
- Return canonical ``Product`` and ``SellerOffer`` objects whose ``is_demo`` flag
  is set appropriately.
- Keep demo data completely separate from any live-sourcing logic; the loader is
  deliberately simple and does not connect to any external API.

Design notes (D-004, D-005):
- No pydantic dependency in the loader itself; validation is done with hand-written
  checks that match the domain model's own __post_init__ rules.
- The loader is a pure function — no network, no state, no imports beyond stdlib.
- The ``is_demo`` gate is the single kill-switch; if it fails, the loader aborts.
"""
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from aba.domain.provenance import Product, SellerOffer, Condition, ProductSpecification, SourceRef, Evidence
from aba.domain.freshness import freshness, FreshnessStatus


def _validate_demo_flags(data: dict) -> None:
    """Raise ValueError if any product or offer in *data* lacks ``is_demo=True``.

    This mirrors the checks inside ``load_demo_catalog`` so they can be
    unit‑tested independently.
    """
    for i, pd in enumerate(data.get("products", [])):
        if not isinstance(pd, dict):
            raise ValueError(f"product entry #{i} is not a JSON object")
        if pd.get("is_demo") is not True:
            raise ValueError(
                f"product entry #{i} must have is_demo=True (demo fixture); "
                f"got is_demo={pd.get('is_demo')!r}"
            )
    for i, od in enumerate(data.get("seller_offers", [])):
        if not isinstance(od, dict):
            raise ValueError(f"offer entry #{i} is not a JSON object")
        if od.get("is_demo") is not True:
            raise ValueError(
                f"offer entry #{i} must have is_demo=True (demo fixture); "
                f"got is_demo={od.get('is_demo')!r}"
            )


def _parse_observed_at(value: Any) -> datetime:
    """Parse an ISO-8601 datetime string assumed to be UTC.

    Raises ValueError if the string cannot be parsed or is naive (no timezone).
    """
    if value is None:
        raise ValueError("observed_at must not be None")
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ValueError("observed_at datetime must be timezone-aware (UTC)")
        return value
    # Assume string like "2026-10-13T12:00:00Z"
    s = value.strip()
    # Try Python 3.11+ fromisoformat with Z-handling
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except (ValueError, TypeError) as e:
        raise ValueError(f"cannot parse observed_at ISO string: {value!r}") from e
    if dt.tzinfo is None:
        raise ValueError("observed_at datetime must be timezone-aware (UTC)")
    return dt


def _parse_condition(value: str) -> Condition:
    """Map a string to the canonical Condition enum."""
    return Condition(value=value.lower())


def load_demo_catalog() -> Tuple[List[Product], List[SellerOffer]]:
    """Load the demo catalog and return ``(products, seller_offers)``.

    Returns:
        Tuple of (products, seller_offers) — each a list of canonical domain
        objects.  Every object has ``is_demo=True``.

    Raises:
        ValueError: If any fixture in the JSON lacks ``is_demo=True``, or if
            required fields are missing/malformed.
        FileNotFoundError: If ``demo_catalog.json`` does not exist (unlikely
            in a checked-out repo, but we surface it clearly).
    """
    import os
    catalogue_path = os.path.join(
        os.path.dirname(__file__),
        "..",
 "catalog",
        "demo_catalog.json",
    )
    # Resolve relative to the repo root so the test can also call this directly.
    # The path ``aba/catalog/demo_catalog.json`` is relative to ``aba/``.
    # When invoked from the repo root: .../aba/catalog/demo_catalog.json
    # When invoked from ``aba/``: .../catalog/demo_catalog.json
    # Resolve reliably:
    repo_root = os.path.abspath(os.path.join(__file__, "..", "..", ".."))
    resolved = os.path.join(repo_root, "aba", "catalog", "demo_catalog.json")

    with open(resolved, "r", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)

    products_data: List[Dict[str, Any]] = data.get("products", [])
    offers_data: List[Dict[str, Any]] = data.get("seller_offers", [])

    # ---- Validate products ----
    products: List[Product] = []
    for i, pd in enumerate(products_data):
        if not isinstance(pd, dict):
            raise ValueError(f"product entry #{i} is not a JSON object")
        if pd.get("is_demo") is not True:
            raise ValueError(
                f"product entry #{i} must have is_demo=True (demo fixture); "
                f"got is_demo={pd.get('is_demo')!r}"
            )
        pid = pd.get("product_id", "").strip()
        name = pd.get("name", "").strip()
        category = pd.get("category", "").strip()
        market = pd.get("market", "").strip()

        if not pid:
            raise ValueError(f"product entry #{i} missing product_id")
        if not name:
            raise ValueError(f"product entry #{i} missing name")

        # Build specs tuple
        specs_list = pd.get("specs", [])
        specs: Tuple[ProductSpecification, ...] = ()
        for j, sp in enumerate(specs_list):
            if not isinstance(sp, dict):
                raise ValueError(f"product #{pid} specs entry #{j} is not a JSON object")
            key = sp.get("key", "").strip()
            val = sp.get("value")
            unit = sp.get("unit")
            ev = sp.get("evidence", {})
            if not key:
                raise ValueError(f"product #{pid} specs entry #{j} missing key")

            # Build Evidence
            er = ev.get("source_ref", {})
            if not isinstance(er, dict):
                er = {}
            provider = er.get("provider", "unknown")
            er_note = er.get("note", "")
            source_ref = SourceRef(provider=provider, source_id=er.get("source_id"), url=er.get("url"), retrieved_at=er.get("retrieved_at"))
            evidence = Evidence(source_ref=source_ref, note=ev.get("note", ""))

            spec = ProductSpecification(
                key=key,
                value=val,
                unit=unit,
                evidence=evidence,
            )
            specs = specs + (spec,)

        # Parse observed_at from the first product as a reference, but products
        # themselves don't have observed_at — that's on offers.
        product = Product(
            product_id=pid,
            name=name,
            category=category,
            market=market,
            specs=specs,
            is_demo=True,
        )
        products.append(product)

    # ---- Validate seller offers ----
    offers: List[SellerOffer] = []
    for i, od in enumerate(offers_data):
        if not isinstance(od, dict):
            raise ValueError(f"offer entry #{i} is not a JSON object")
        if od.get("is_demo") is not True:
            raise ValueError(
                f"offer entry #{i} must have is_demo=True (demo fixture); "
                f"got is_demo={od.get('is_demo')!r}"
            )

        pid = od.get("product_id", "").strip()
        seller_id = od.get("seller_id", "").strip()
        price_amount = od.get("price_amount")
        price_currency = od.get("price_currency", "").strip()
        cond_str = od.get("condition", "new").strip()
        product_url = od.get("product_url", "").strip()
        observed_at_raw = od.get("observed_at")
        source_id = od.get("source_id", "").strip()

        if not pid:
            raise ValueError(f"offer entry #{i} missing product_id")
        if not seller_id:
            raise ValueError(f"offer entry #{i} missing seller_id")
        if price_amount is None:
            raise ValueError(f"offer entry #{i} missing price_amount")
        if not price_currency:
            raise ValueError(f"offer entry #{i} missing price_currency")
        if not product_url:
            raise ValueError(f"offer entry #{i} missing product_url")
        if not source_id:
            raise ValueError(f"offer entry #{i} missing source_id")

        try:
            observed_at = _parse_observed_at(observed_at_raw)
        except ValueError as e:
            raise ValueError(f"offer entry #{i} observed_at: {e}") from e

        try:
            condition = _parse_condition(cond_str)
        except ValueError as e:
            raise ValueError(f"offer entry #{i} condition '{cond_str}': {e}") from e

        # Build the offer
        offer = SellerOffer(
            product_id=pid,
            seller_id=seller_id,
            price_amount=float(price_amount),
            price_currency=price_currency,
            condition=condition,
            product_url=product_url,
            observed_at=observed_at,
            source_id=source_id,
            is_demo=True,
        )
        offers.append(offer)

    return products, offers


# ---------------------------------------------------------------------------
# Quick self-test when run as a script
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    products, offers = load_demo_catalog()
    print(f"Loaded {len(products)} demo product(s) and {len(offers)} demo offer(s)")
    for p in products:
        print(f"  - {p.name} (id={p.product_id}, demo={p.is_demo})")
    for o in offers:
        print(f"  - {o.seller_id}: {o.price_amount} {o.price_currency} "
              f"(observed={o.observed_at.isoformat()}, demo={o.is_demo})")