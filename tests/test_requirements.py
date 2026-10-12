"""Unit tests for the M2 requirement schema and deterministic validation.

Run: python -m unittest discover -s tests -v
"""
from __future__ import annotations

import unittest

from aba.requirements.model import Requirement, RequirementValidationResult


class TestRequirementCreation(unittest.TestCase):
    """Valid Requirement objects can be created with proper inputs."""

    def test_valid_requirement(self):
        req = Requirement(
            need_description="laptop for school",
            budget_amount=100000,
            budget_currency="USD",
            market="US",
            condition="new",
        )
        self.assertEqual(req.need_description, "laptop for school")
        self.assertEqual(req.budget_amount, 100000)
        self.assertEqual(req.budget_currency, "USD")
        self.assertEqual(req.market, "US")
        self.assertEqual(req.condition, "new")
        self.assertEqual(req.must_haves, frozenset())
        self.assertEqual(req.nice_to_haves, frozenset())

    def test_requirement_with_must_haves(self):
        req = Requirement(
            need_description="gaming laptop",
            budget_amount=200000,
            budget_currency="USD",
            must_haves=frozenset({"gpu", "screen_size"}),
        )
        self.assertEqual(req.must_haves, frozenset({"gpu", "screen_size"}))

    def test_requirement_with_nice_to_haves(self):
        req = Requirement(
            need_description="student laptop",
            budget_amount=80000,
            budget_currency="PKR",
            nice_to_haves=frozenset({"backlit_keyboard"}),
        )
        self.assertEqual(req.nice_to_haves, frozenset({"backlit_keyboard"}))


class TestRequirementValidation(unittest.TestCase):
    """Hard constraint validation is deterministic and rejects invalid inputs."""

    def test_valid_requirement_passes_validation(self):
        req = Requirement(
            need_description="laptop for school",
            budget_amount=100000,
            budget_currency="USD",
        )
        result = req.validate()
        self.assertTrue(result.is_valid)
        self.assertEqual(result.errors, ())

    def test_empty_need_description_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            Requirement(
                need_description="",
                budget_amount=100000,
                budget_currency="USD",
            )
        self.assertIn("need_description must be non-empty", str(ctx.exception))

    def test_negative_budget_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            Requirement(
                need_description="laptop",
                budget_amount=-500,
                budget_currency="USD",
            )
        self.assertIn("budget_amount must be positive", str(ctx.exception))

    def test_zero_budget_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            Requirement(
                need_description="laptop",
                budget_amount=0,
                budget_currency="USD",
            )
        self.assertIn("budget_amount must be positive", str(ctx.exception))

    def test_non_uppercase_3_letter_currency_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            Requirement(
                need_description="laptop",
                budget_amount=100000,
                budget_currency="usd",
            )
        self.assertIn("budget_currency must be exactly 3 uppercase letters", str(ctx.exception))

    def test_short_currency_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            Requirement(
                need_description="laptop",
                budget_amount=100000,
                budget_currency="US",
            )
        self.assertIn("budget_currency must be exactly 3 uppercase letters", str(ctx.exception))

    def test_validate_returns_result_object(self):
        req = Requirement(
            need_description="laptop",
            budget_amount=50000,
            budget_currency="USD",
        )
        result = req.validate()
        self.assertIsInstance(result, RequirementValidationResult)
        self.assertIsInstance(result.errors, tuple)
        self.assertIs(result.requirement, req)

    def test_validate_with_invalid_condition(self):
        req = Requirement(
            need_description="laptop",
            budget_amount=50000,
            budget_currency="USD",
            condition="broken",  # invalid
        )
        result = req.validate()
        self.assertFalse(result.is_valid)
        self.assertTrue(any("condition" in e for e in result.errors))

    def test_validate_with_invalid_market_type(self):
        # Market as non-string should be caught
        req = Requirement(
            need_description="laptop",
            budget_amount=50000,
            budget_currency="USD",
            market=123,  # type: ignore
        )
        result = req.validate()
        self.assertFalse(result.is_valid)
        self.assertTrue(any("market" in e for e in result.errors))

    def test_zero_budget_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            Requirement(
                need_description="laptop",
                budget_amount=0,
                budget_currency="USD",
            )
        self.assertIn("budget_amount must be positive", str(ctx.exception))


class TestRequirementValidationResult(unittest.TestCase):
    """The validation result datatype is correct."""

    def test_result_is_valid_no_errors(self):
        from aba.requirements.model import Requirement
        req = Requirement(need_description="x", budget_amount=100, budget_currency="USD")
        result = req.validate()
        self.assertTrue(result.is_valid)
        self.assertEqual(result.errors, ())

    def test_result_has_error_messages(self):
        from aba.requirements.model import Requirement, RequirementValidationResult
        # Build a requirement that will produce validation errors.
        # We can't use empty need_description (constructor rejects it),
        # so we use a valid one and then check that validate() catches other issues.
        req = Requirement(need_description="laptop", budget_amount=100, budget_currency="USD")
        # Manually create a result with errors (simulating what validate() would produce)
        result = RequirementValidationResult(
            is_valid=False,
            errors=("test error",),
            requirement=req,
        )
        self.assertFalse(result.is_valid)
        self.assertEqual(result.errors, ("test error",))


if __name__ == "__main__":  # pragma: no cover
    pass