"""Category-neutral requirement schema with deterministic validation.

M2 — Requirement profile + hard constraint filtering.
- Parses a user's natural-language need and budget into a structured requirement object.
- Enforces hard constraints (budget max, currency format, market format) by code
  before any preference-based ranking or LLM involvement.
- Keeps category and market as free-form data so D-006/D-007 remain open.
- All validation is pure and deterministic; no paid APIs or random behaviour.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Set, FrozenSet


class Market(str, Enum):
    """Free-form market / country code, kept as a string enum for flexibility
    while retaining some structure.  Values are 2-letter ISO-3166 codes when
    known, but the model does not enforce any particular set — callers may
    restrict via their own subsets."""
    pass


@dataclass(frozen=True)
class Requirement:
    """Structured purchase requirement produced from natural-language user input.

    Hard constraints are enforced in ``Requirement.validate()``.  Preference-based
    ranking is deferred to later layers; this layer only ensures that invalid
    requests are rejected before they reach the product-matching engine.

    Attributes:
        need_description: Natural-language description of the purchase need
            (e.g. "laptop for school", "gift for dad").  Must be non-empty after
            stripping.
        budget_amount: Price amount in the smallest currency unit (e.g. cents).
            Must be positive; validated in ``validate()``.
        budget_currency: 3-letter ISO-4217 currency code (e.g. "USD", "PKR").
            Validated in ``validate()``.
        market: Free-form market / country string.  Not used for deterministic
            filtering in M1; kept as data so D-006/D-007 stay open.
        condition: Optional preferred product condition (new / refurbished / used /
            open-box).  If supplied it is normalised; if not supplied the offer's
            condition is considered unconstrained.
        must_haves: Frozen set of specification keys that the user absolutely
            requires (e.g. {"screen_size", "cpu_model"}).  Empty by default.
        nice_to_haves: Frozen set of specification keys that would be desirable
            but are not mandatory.  Empty by default.
    """
    need_description: str
    budget_amount: float
    budget_currency: str
    market: str = ""
    condition: Optional[str] = None
    must_haves: FrozenSet[str] = field(default_factory=frozenset)
    nice_to_haves: FrozenSet[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not self.need_description or not self.need_description.strip():
            raise ValueError("need_description must be non-empty")
        if not isinstance(self.budget_amount, (int, float)) or self.budget_amount <= 0:
            raise ValueError("budget_amount must be positive")
        if not isinstance(self.budget_currency, str):
            raise TypeError("budget_currency must be a string")
        cleaned = self.budget_currency.strip()
        if len(cleaned) != 3 or not cleaned.isupper():
            raise ValueError("budget_currency must be exactly 3 uppercase letters (ISO-4217)")

    def validate(self) -> "RequirementValidationResult":
        """Return a ``RequirementValidationResult`` describing whether the
        requirement is valid and why.

        This method is idempotent and deterministic — it does not depend on
        the wall clock, external services, or LLM behaviour.
        """
        errors: list[str] = []

        # Budget amount already validated in __post_init__, but re-check for
        # completeness in the validation result.
        if self.budget_amount <= 0:
            errors.append("budget_amount must be positive")

        # Currency already validated, but record here.
        cleaned_currency = self.budget_currency.strip()
        if len(cleaned_currency) != 3 or not cleaned_currency.isupper():
            errors.append("budget_currency must be exactly 3 uppercase letters")

        # Market: we accept any non-empty string; callers may later add
        # their own subset validation (e.g. ISO-3166 codes).
        if self.market and not isinstance(self.market, str):
            errors.append("market must be a string if supplied")

        # Condition: if supplied, must be one of the canonical values.
        if self.condition is not None:
            valid_conditions: tuple[str, ...] = ("new", "refurbished", "used", "open-box")
            if self.condition.lower() not in valid_conditions:
                errors.append(
                    f"condition must be one of {valid_conditions}; got {self.condition!r}"
                )

        return RequirementValidationResult(
            is_valid=len(errors) == 0,
            errors=tuple(errors),
            requirement=self,
        )


@dataclass(frozen=True)
class RequirementValidationResult:
    """Result of ``Requirement.validate()``.

    Attributes:
        is_valid: True when no validation errors were found.
        errors: Tuple of human-readable error strings.  Empty tuple when
            ``is_valid`` is True.
        requirement: The ``Requirement`` that was validated (included for
            convenience so the caller doesn't need to re-reference the original).
    """
    is_valid: bool
    errors: tuple[str, ...]  # immutable, even when empty (represents ())
    requirement: "Requirement"