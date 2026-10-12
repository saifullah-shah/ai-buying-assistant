"""Unit tests for the domain model: Product, ProductSpecification, SourceRef,
SellerOffer, Condition, and freshness policy.

Run: python -m unittest discover -s tests -v
"""
from __future__ import annotations

from datetime import datetime, timezone
import unittest

from aba.domain.provenance import (
    Product,
    ProductSpecification,
    SourceRef,
    Evidence,
    SellerOffer,
    Condition,
    PriceObservation,
)
from aba.domain.freshness import freshness, FreshnessStatus


class TestVerificationStatus(unittest.TestCase):
    """VerificationStatus is an explicit enum — UNKNOWN is never silently defaulted."""

    def test_unknown_is_a_valid_status(self):
        from aba.domain.provenance import VerificationStatus
        self.assertEqual(VerificationStatus.UNKNOWN.value, "unknown")

    def test_demo_is_a_valid_status(self):
        from aba.domain.provenance import VerificationStatus
        self.assertEqual(VerificationStatus.DEMO.value, "demo")


class TestSourceRef(unittest.TestCase):
    """SourceRef carries provider, source_id, url, and retrieved_at."""

    def test_source_ref_minimal(self):
        ref = SourceRef(provider="test-provider")
        self.assertEqual(ref.provider, "test-provider")
        self.assertIsNone(ref.source_id)
        self.assertIsNone(ref.url)
        self.assertIsNotNone(ref.retrieved_at)

    def test_source_ref_full(self):
        from datetime import datetime, timezone
        rt = datetime(2026, 1, 15, 10, 30, tzinfo=timezone.utc)
        ref = SourceRef(
            provider="amazon-pa-api",
            source_id="B09XYZ",
            url="https://example.com",
            retrieved_at=rt,
        )
        self.assertEqual(ref.provider, "amazon-pa-api")
        self.assertEqual(ref.source_id, "B09XYZ")
        self.assertEqual(ref.url, "https://example.com")
        self.assertEqual(ref.retrieved_at, rt)


class TestProductSpecification(unittest.TestCase):
    """ProductSpecification: key/value + unit + evidence. Unknown when value is None."""

    def test_known_spec(self):
        spec = ProductSpecification(key="screen_size", value=14.0, unit="inches")
        self.assertEqual(spec.key, "screen_size")
        self.assertEqual(spec.value, 14.0)
        self.assertEqual(spec.unit, "inches")
        # is_unknown() is False when a value is present, even if provenance
        # is default (provider="unknown").  The value itself is known; the
        # evidence status is a separate concern.
        self.assertFalse(spec.is_unknown())

    def test_known_spec_with_evidence(self):
        from aba.domain.provenance import SourceRef
        spec = ProductSpecification(
            key="cpu_model",
            value="Intel i7",
            unit="GHz",
            evidence=Evidence(
                source_ref=SourceRef(provider="spec-sheet", source_id="CPU-123"),
                note="extracted from API response",
            ),
        )
        self.assertEqual(spec.value, "Intel i7")
        self.assertEqual(spec.unit, "GHz")
        self.assertFalse(spec.is_unknown())

    def test_unknown_spec_returns_default(self):
        spec = ProductSpecification(key="missing", value=None)
        self.assertIsNone(spec.value)
        self.assertTrue(spec.is_unknown())

    def test_unknown_spec_with_reason(self):
        from aba.domain.provenance import SourceRef
        spec = ProductSpecification(
            key="manufacturer",
            value=None,
            evidence=Evidence(
                source_ref=SourceRef(provider="unknown", note="vendor refused to disclose"),
                note="vendor refused to disclose",
            ),
        )
        self.assertTrue(spec.is_unknown())


class TestProduct(unittest.TestCase):
    """Product canonical identity — non-empty name and product_id."""

    def test_valid_product(self):
        p = Product(product_id="p1", name="Laptop X")
        self.assertEqual(p.product_id, "p1")
        self.assertEqual(p.name, "Laptop X")
        self.assertFalse(p.is_demo)

    def test_empty_name_rejected(self):
        with self.assertRaises(ValueError):
            Product(product_id="p1", name="")

    def test_empty_product_id_rejected(self):
        with self.assertRaises(ValueError):
            Product(product_id="", name="Laptop X")

    def test_lookup_and_get_spec(self):
        p = Product(
            product_id="p1",
            name="Laptop X",
            specs=(
                ProductSpecification(key="screen_size", value=14.0, unit="inches"),
                ProductSpecification(key="cpu_model", value="Intel i7", unit="GHz"),
            ),
        )
        self.assertEqual(p.lookup_spec("screen_size").value, 14.0)
        self.assertEqual(p.get_spec_value("screen_size"), 14.0)
        self.assertIsNone(p.get_spec_value("nonexistent"))
        # Unknown spec (value is None) returns default
        self.assertIsNone(p.get_spec_value("missing"))


class TestCondition(unittest.TestCase):
    """Condition enum: new / refurbished / used / open-box / unknown."""

    def test_valid_conditions(self):
        for val in ("new", "refurbished", "used", "open-box", "unknown"):
            c = Condition(value=val)
            self.assertEqual(c.value, val)

    def test_invalid_condition_rejected(self):
        with self.assertRaises(ValueError):
            Condition(value="broken")


class TestSellerOffer(unittest.TestCase):
    """SellerOffer validation: positive price, 3-letter uppercase currency,
    timezone-aware observed_at, non-empty strings."""

    def test_valid_offer(self):
        from datetime import datetime, timezone
        offer = SellerOffer(
            product_id="p1",
            seller_id="seller-01",
            price_amount=89990.0,
            price_currency="USD",
            condition=Condition(value="new"),
            product_url="https://example.com/p1",
            observed_at=datetime(2026, 10, 13, 12, 0, 0, tzinfo=timezone.utc),
            source_id="demo-catalog",
        )
        self.assertEqual(offer.product_id, "p1")
        self.assertEqual(offer.seller_id, "seller-01")

    def test_negative_price_rejected(self):
        with self.assertRaises(ValueError):
            SellerOffer(
                product_id="p1",
                seller_id="s",
                price_amount=-100.0,
                price_currency="USD",
                condition=Condition(value="new"),
                product_url="https://example.com/p1",
                observed_at=datetime(2026, 10, 13, 12, 0, 0, tzinfo=timezone.utc),
                source_id="src",
            )

    def test_zero_price_rejected(self):
        with self.assertRaises(ValueError):
            SellerOffer(
                product_id="p1",
                seller_id="s",
                price_amount=0.0,
                price_currency="USD",
                condition=Condition(value="new"),
                product_url="https://example.com/p1",
                observed_at=datetime(2026, 10, 13, 12, 0, 0, tzinfo=timezone.utc),
                source_id="src",
            )

    def test_non_uppercase_3_letter_currency_rejected(self):
        with self.assertRaises(ValueError):
            SellerOffer(
                product_id="p1",
                seller_id="s",
                price_amount=89990.0,
                price_currency="usd",  # lowercase
                condition=Condition(value="new"),
                product_url="https://example.com/p1",
                observed_at=datetime(2026, 10, 13, 12, 0, 0, tzinfo=timezone.utc),
                source_id="src",
            )

    def test_short_currency_rejected(self):
        with self.assertRaises(ValueError):
            SellerOffer(
                product_id="p1",
                seller_id="s",
                price_amount=89990.0,
                price_currency="US",  # only 2 letters
                condition=Condition(value="new"),
                product_url="https://example.com/p1",
                observed_at=datetime(2026, 10, 13, 12, 0, 0, tzinfo=timezone.utc),
                source_id="src",
            )

    def test_naive_observed_at_rejected(self):
        with self.assertRaises(ValueError):
            SellerOffer(
                product_id="p1",
                seller_id="s",
                price_amount=89990.0,
                price_currency="USD",
                condition=Condition(value="new"),
                product_url="https://example.com/p1",
                observed_at=datetime(2026, 10, 13, 12, 0, 0),  # naive
                source_id="src",
            )

    def test_empty_product_id_rejected(self):
        with self.assertRaises(ValueError):
            SellerOffer(
                product_id="",
                seller_id="s",
                price_amount=89990.0,
                price_currency="USD",
                condition=Condition(value="new"),
                product_url="https://example.com/p1",
                observed_at=datetime(2026, 10, 13, 12, 0, 0, tzinfo=timezone.utc),
                source_id="src",
            )

    def test_empty_seller_id_rejected(self):
        with self.assertRaises(ValueError):
            SellerOffer(
                product_id="p1",
                seller_id="",
                price_amount=89990.0,
                price_currency="USD",
                condition=Condition(value="new"),
                product_url="https://example.com/p1",
                observed_at=datetime(2026, 10, 13, 12, 0, 0, tzinfo=timezone.utc),
                source_id="src",
            )

    def test_empty_product_url_rejected(self):
        with self.assertRaises(ValueError):
            SellerOffer(
                product_id="p1",
                seller_id="s",
                price_amount=89990.0,
                price_currency="USD",
                condition=Condition(value="new"),
                product_url="",
                observed_at=datetime(2026, 10, 13, 12, 0, 0, tzinfo=timezone.utc),
                source_id="src",
            )

    def test_empty_source_id_rejected(self):
        with self.assertRaises(ValueError):
            SellerOffer(
                product_id="p1",
                seller_id="s",
                price_amount=89990.0,
                price_currency="USD",
                condition=Condition(value="new"),
                product_url="https://example.com/p1",
                observed_at=datetime(2026, 10, 13, 12, 0, 0, tzinfo=timezone.utc),
                source_id="",
            )


class TestPriceObservation(unittest.TestCase):
    """PriceObservation validation: same currency/amount guards as SellerOffer,
    but attached separately (identity/offer separation per PROJECT_BRIEF)."""

    def test_valid_observation(self):
        from datetime import datetime, timezone
        obs = PriceObservation(
            offer_id="offer-01",
            observed_at=datetime(2026, 10, 13, 12, 0, 0, tzinfo=timezone.utc),
            price_amount=89990.0,
            price_currency="USD",
            source_ref={"provider": "test", "note": "demo"},
        )
        self.assertEqual(obs.offer_id, "offer-01")

    def test_naive_observed_at_rejected(self):
        with self.assertRaises(ValueError):
            PriceObservation(
                offer_id="offer-01",
                observed_at=datetime(2026, 10, 13, 12, 0, 0),  # naive
                price_amount=89990.0,
                price_currency="USD",
                source_ref={"provider": "test"},
            )


class TestFreshness(unittest.TestCase):
    """freshness() is pure and deterministic when now is injected."""

    def test_fresh_within_ttl(self):
        now = datetime(2026, 10, 13, 12, 30, 0, tzinfo=timezone.utc)  # 30 min later
        observed = datetime(2026, 10, 13, 12, 0, 0, tzinfo=timezone.utc)  # 30 min ago
        result = freshness(observed_at=observed, now=now, ttl_seconds=3600)
        self.assertEqual(result, FreshnessStatus.FRESH)

    def test_stale_over_ttl(self):
        now = datetime(2026, 10, 13, 15, 0, 0, tzinfo=timezone.utc)
        observed = datetime(2026, 10, 13, 12, 0, 0, tzinfo=timezone.utc)
        result = freshness(observed_at=observed, now=now, ttl_seconds=3600)
        self.assertEqual(result, FreshnessStatus.STALE)

    def test_fresh_with_custom_now_injection(self):
        """Injecting a fixed now makes the test deterministic regardless of wall clock."""
        observed = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        fixed_now = datetime(2026, 1, 1, 0, 0, 30, tzinfo=timezone.utc)  # 30s later
        result = freshness(observed_at=observed, now=fixed_now, ttl_seconds=60)
        self.assertEqual(result, FreshnessStatus.FRESH)

    def test_stale_with_custom_now_injection(self):
        observed = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        fixed_now = datetime(2026, 1, 1, 0, 1, 0, tzinfo=timezone.utc)  # 60s later
        result = freshness(observed_at=observed, now=fixed_now, ttl_seconds=30)
        self.assertEqual(result, FreshnessStatus.STALE)

    def test_unknown_when_observed_at_is_none(self):
        result = freshness(observed_at=None)
        self.assertEqual(result, FreshnessStatus.UNKNOWN)

    def test_unknown_when_observed_at_naive(self):
        # Naive datetime is rejected at the model level, but freshness guards anyway
        result = freshness(observed_at=datetime(2026, 10, 13, 12, 0, 0))
        # Naive datetime → UNKNOWN (guard, not crash)
        self.assertEqual(result, FreshnessStatus.UNKNOWN)