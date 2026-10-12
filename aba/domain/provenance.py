"""Provenance, evidence, and verification status for product data.

Key design points (see D-004: evidence-backed recommendations and deterministic constraints):
- Unknown data remains unknown; never invented.
- Every datum carries its source/provider and observed-at time.
- Verification status is an explicit enum — data without evidence is UNKNOWN,
  not silently defaulted to VERIFIED.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class VerificationStatus(Enum):
    """Explicit status of how well a fact is supported."""

    VERIFIED = "verified"       # supported by a checked source or a test we actually ran
    UNVERIFIED = "unverified"   # plausible but not checked against adequate evidence
    UNKNOWN = "unknown"         # deliberately withheld / missing / not applicable
    DEMO = "demo"               # deliberately labelled demo / fabricated data


@dataclass(frozen=True)
class SourceRef:
    """Minimal reference to the origin of a piece of data.

    AGENTS.md §7 provenance minimum: source/provider, observed-at time, currency, units,
    product identifiers, and freshness/verification status where relevant.
    """
    provider: str            # e.g. "amazon-pa-api", "daraz-api", "curated-csv"
    source_id: Optional[str] = None  # e.g. ASIN, product ID from the provider
    url: Optional[str] = None        # link to the source page / API spec / listing
    retrieved_at: Optional[datetime] = field(default_factory=lambda: datetime.now(timezone.utc))
    note: str = ""             # optional human-readable note

    def is_recent(self, max_age_seconds: int = 86400) -> bool:
        """Return True if retrieved_at is within ``max_age_seconds`` of now."""
        if self.retrieved_at is None:
            return False
        age = (datetime.now(timezone.utc) - self.retrieved_at).total_seconds()
        return age <= max_age_seconds


@dataclass(frozen=True)
class Evidence:
    """A piece of evidence supporting a specification value.

    Used on ProductSpecification to explain where a fact came from, or that it is unknown.
    """
    source_ref: SourceRef
    # A human-readable note that can surface in explanations, e.g.
    # "listed in API response but no model number supplied"
    note: str = ""


@dataclass(frozen=True)
class ProductSpecification:
    """A key/value specification attached to a canonical Product.

    The key is a plain string (e.g. "screen_size", "cpu_model").
    The value is a typed primitive + unit.  Unknown fields must carry an
    ``Evidence`` with ``source_ref.provider == "unknown"`` and
    ``source_ref.note`` explaining why.
    """
    key: str
    value: object              # str, int, float, bool, or None
    unit: Optional[str] = None  # e.g. "inches", "GHz", "GB"
    evidence: Evidence = field(
        default_factory=lambda: Evidence(
            source_ref=SourceRef(provider="unknown", note="no evidence provided")
        )
    )

    def is_unknown(self) -> bool:
        """Return True when the value is None (i.e. the spec has no assigned value).

        A spec that has a value but default provenance (provider="unknown")
        is not "unknown" in the sense of having no value — it merely lacks
        evidence.  Callers who need to know about evidence should check
        ``evidence.source_ref.provider`` directly.
        """
        return self.value is None


@dataclass(frozen=True)
class Product:
    """Canonical product identity — distinct from seller offers and price observations.

    Attributes:
        product_id: A stable internal identifier (e.g. "lp1234").
        name: Human-readable product name.  Must not be empty.
        category: Free-form category string.  Not used for deterministic filtering;
            kept as data so D-006/D-007 stay open.
        market: Free-form market / country code (e.g. "PK", "US").  Not used for
            filtering in M1.
        specs: Mapping of key/value specifications.  Unknown specs must carry a
            reason; they are never silently defaulted.
        is_demo: When True, this product was generated from a demo fixture and
            must not be presented as a live offer.
    """
    product_id: str
    name: str
    category: str = ""
    market: str = ""
    specs: tuple[ProductSpecification, ...] = field(default_factory=tuple)
    is_demo: bool = False

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Product.name must be non-empty")
        if not self.product_id or not self.product_id.strip():
            raise ValueError("Product.product_id must be non-empty")

    def lookup_spec(self, key: str) -> Optional[ProductSpecification]:
        """Return the specification with the given key, or None."""
        for s in self.specs:
            if s.key == key:
                return s
        return None

    def get_spec_value(self, key: str, default: object = None) -> object:
        """Return the value for *key*, or *default* if absent/unknown."""
        spec = self.lookup_spec(key)
        if spec is None:
            return default
        # If the spec is explicitly marked unknown, return default rather than
        # silently exposing the bare value.
        if spec.is_unknown():
            return default
        return spec.value


@dataclass(frozen=True)
class Condition:
    """Product condition as used in seller offers."""
    value: str  # e.g. "new", "refurbished", "used", "open-box"

    def __post_init__(self) -> None:
        if self.value not in {"new", "refurbished", "used", "open-box", "unknown"}:
            raise ValueError(f"Uncondition value {self.value!r}")


@dataclass(frozen=True)
class SellerOffer:
    """A seller's offer for a canonical Product.

    Attributes:
        product_id: The canonical product_id this offer is for.
        seller_id: A stable identifier for the seller (e.g. "seller_abc").
        price_amount: Positive price in the smallest currency unit (e.g. cents).
            Validation enforced.
        price_currency: 3-letter ISO-4217 currency code (e.g. "USD", "PKR").
        condition: Product condition (new / refurbished / used / open-box).
        product_url: URL to the product page on the seller's site.
        observed_at: UTC-aware datetime when this observation was recorded.
            Naive datetimes are rejected.
        source_id: Identifier of the source/provider for this offer.
        is_demo: When True, this offer was generated from a demo fixture.
    """
    product_id: str
    seller_id: str
    price_amount: float
    price_currency: str
    condition: Condition
    product_url: str
    observed_at: datetime
    source_id: str
    is_demo: bool = False

    def __post_init__(self) -> None:
        # Validate price amount: must be positive
        if not isinstance(self.price_amount, (int, float)):
            raise TypeError("price_amount must be numeric")
        if self.price_amount <= 0:
            raise ValueError("price_amount must be positive ( > 0 )")

        # Validate currency: exactly 3 uppercase letters
        if not isinstance(self.price_currency, str):
            raise TypeError("price_currency must be a string")
        cleaned = self.price_currency.strip()
        if len(cleaned) != 3 or not cleaned.isupper():
            raise ValueError("price_currency must be exactly 3 uppercase letters (ISO-4217)")

        # Validate observed_at is timezone-aware (UTC required)
        if self.observed_at.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware (UTC)")

        # Non-empty strings
        if not self.product_id or not self.product_id.strip():
            raise ValueError("product_id must be non-empty")
        if not self.seller_id or not self.seller_id.strip():
            raise ValueError("seller_id must be non-empty")
        if not self.product_url or not self.product_url.strip():
            raise ValueError("product_url must be non-empty")
        if not self.source_id or not self.source_id.strip():
            raise ValueError("source_id must be non-empty")


@dataclass(frozen=True)
class PriceObservation:
    """A price observation attached to a SellerOffer.

    Kept separate from the offer per PROJECT_BRIEF §12 — price history should not
    mutate the offer record.  Observations are time-stamped and source-referenced.
    """
    offer_id: str          # the seller_id or a composite key tying back to the offer
    observed_at: datetime   # UTC-aware, when the price was observed
    price_amount: float
    price_currency: str
    source_ref: object      # SourceRef or similar; minimal, not duplicated
    notes: str = ""

    def __post_init__(self) -> None:
        if self.observed_at.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware (UTC)")
        if not isinstance(self.price_amount, (int, float)) or self.price_amount <= 0:
            raise ValueError("price_amount must be positive")
        if not isinstance(self.price_currency, str) or len(self.price_currency.strip()) != 3 or not self.price_currency.strip().isupper():
            raise ValueError("price_currency must be exactly 3 uppercase letters")