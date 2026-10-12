"""Unit tests for the demo catalog loader.

Run: python -m unittest discover -s tests -v
"""
from __future__ import annotations

import unittest
import json
import tempfile
import os

from aba.catalog.loader import load_demo_catalog, _validate_demo_flags
from aba.domain.provenance import Product, SellerOffer, Condition


class TestLoadDemoCatalog(unittest.TestCase):
    """Loading the demo catalog returns canonical objects with is_demo=True."""

    def test_load_returns_products_and_offers(self):
        products, offers = load_demo_catalog()
        self.assertIsInstance(products, list)
        self.assertIsInstance(offers, list)
        self.assertGreater(len(products), 0)
        self.assertGreater(len(offers), 0)

    def test_all_products_have_is_demo_true(self):
        products, _ = load_demo_catalog()
        for p in products:
            with self.subTest(product=p.product_id):
                self.assertTrue(p.is_demo, f"{p.product_id} must have is_demo=True")

    def test_all_offers_have_is_demo_true(self):
        _, offers = load_demo_catalog()
        for o in offers:
            with self.subTest(offer=o.seller_id):
                self.assertTrue(o.is_demo, f"{o.seller_id} must have is_demo=True")

    def test_products_are_canonical(self):
        products, _ = load_demo_catalog()
        for p in products:
            self.assertIsInstance(p, Product)
            self.assertTrue(p.product_id.strip())
            self.assertTrue(p.name.strip())

    def test_offers_are_canonical(self):
        _, offers = load_demo_catalog()
        for o in offers:
            self.assertIsInstance(o, SellerOffer)
            self.assertTrue(o.product_id.strip())
            self.assertTrue(o.seller_id.strip())
            self.assertTrue(o.price_amount > 0)
            self.assertTrue(len(o.price_currency) == 3 and o.price_currency.isupper())
            self.assertIsNotNone(o.observed_at.tzinfo)
            self.assertIsInstance(o.condition, Condition)


class TestValidateDemoFlags(unittest.TestCase):
    """Direct unit tests for the _validate_demo_flags helper."""

    def test_valid_catalog_passes(self):
        good = {
            "products": [{"product_id": "p1", "name": "X", "is_demo": True}],
            "seller_offers": [{"seller_id": "s1", "is_demo": True}],
        }
        _validate_demo_flags(good)  # should not raise

    def test_product_missing_is_demo_raises(self):
        bad = {
            "products": [{"product_id": "p1", "name": "X"}],  # no is_demo
            "seller_offers": [{"seller_id": "s1", "is_demo": True}],
        }
        with self.assertRaises(ValueError):
            _validate_demo_flags(bad)

    def test_offer_missing_is_demo_raises(self):
        bad = {
            "products": [{"product_id": "p1", "name": "X", "is_demo": True}],
            "seller_offers": [{"seller_id": "s1"}],  # no is_demo
        }
        with self.assertRaises(ValueError):
            _validate_demo_flags(bad)


if __name__ == "__main__":  # pragma: no cover
    pass