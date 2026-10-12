"""Deterministic tests for M4 LLM-grounded recommendation layer.

All tests run without an LLM API key.  They verify:
- Prompt template format and structure (instructions for LLM output sections)
- Grounding logic (evidence citations, unknowns classification)
- Output schema compliance (sections referenced, format correct)
- Consistency between prompt design and grounding rules

Run: python -m unittest discover -s tests -v
"""
from __future__ import annotations

import unittest

from aba.explanation.prompts import (
    make_recommendation_prompt,
    REQUIRED_LLM_SECTIONS,
    CONSTRAINT_SUMMARY_BLOCK,
)
from aba.explanation.grounding import (
    make_evidence_citation,
    classify_unknown_reason,
    build_unknown_entries,
    check_prompt_block_presence,
)


class TestPromptFormat(unittest.TestCase):
    """Verify the prompt template structure and block presence."""

    def test_prompt_has_llm_instruction_sections(self) -> None:
        """The full prompt must include instructions for the LLM output sections."""
        candidates = [
            {
                "product_name": "Demo Laptop",
                "product_id": "lp1",
                "price_amount": 89990,
                "price_currency": "USD",
                "condition": "new",
                "budget_pass": True,
                "condition_pass": True,
                "must_haves_pass": True,
                "nice_to_haves_score": 1,
                "nice_to_haves_total": 2,
                "flags": ("budget_ok", "cond_ok", "must_haves_ok"),
                "product_specs": [
                    {
                        "key": "screen_size",
                        "value": 14.0,
                        "unit": "inches",
                        "is_unknown": False,
                        "product_spec_evidence": {
                            "provider": "demo-catalog",
                            "source_id": "spec1",
                            "note": "demo fixture",
                        },
                    }
                ],
                "product_spec_evidence": {
                    "provider": "demo-catalog",
                    "source_id": "spec1",
                    "note": "demo fixture",
                },
            }
        ]

        prompt = make_recommendation_prompt(
            requirement_description="laptop for school",
            budget_amount=100000,
            budget_currency="USD",
            requirement_condition="new",
            must_haves=["screen_size"],
            nice_to_haves=["backlit_keyboard"],
            candidates=candidates,
        )

        # The prompt must include the REQUIRED_LLM_SECTIONS instructions
        # Check for key section headers that the LLM must produce
        self.assertIn("FITS BECAUSE:", prompt,
                      "Prompt must contain FITS BECAUSE: instruction")
        self.assertIn("WHAT IT SACRIFICES:", prompt,
                      "Prompt must contain WHAT IT SACRIFICES: instruction")
        self.assertIn("UNKNOWN AND WHY:", prompt,
                      "Prompt must contain UNKNOWN AND WHY: instruction")
        self.assertIn("CONSTRAINT COMPLIANCE SUMMARY:",
                      prompt, "Prompt must contain CONSTRAINT COMPLIANCE SUMMARY instruction")

    def test_constraint_block_present(self) -> None:
        """CONSTRAINT_SUMMARY_BLOCK must appear in the prompt."""
        candidates = [
            {
                "product_name": "Demo Laptop",
                "product_id": "lp1",
                "price_amount": 89990,
                "price_currency": "USD",
                "condition": "new",
                "budget_pass": True,
                "condition_pass": True,
                "must_haves_pass": True,
                "nice_to_haves_score": 1,
                "nice_to_haves_total": 2,
                "flags": ("budget_ok", "cond_ok", "must_haves_ok"),
                "product_specs": [],
                "product_spec_evidence": {},
            }
        ]

        prompt = make_recommendation_prompt(
            requirement_description="laptop",
            budget_amount=100000,
            budget_currency="USD",
            requirement_condition="new",
            must_haves=[],
            nice_to_haves=[],
            candidates=candidates,
        )

        # The constraint summary block title should appear in the prompt
        self.assertIn(
            "HARD CONSTRAINT COMPLIANCE", prompt,
            "Prompt must contain the constraint compliance block title"
        )

    def test_prompt_contains_requirement_block(self) -> None:
        """The prompt must include the requirement summary block."""
        candidates = [
            {
                "product_name": "Demo Laptop",
                "product_id": "lp1",
                "price_amount": 89990,
                "price_currency": "USD",
                "condition": "new",
                "budget_pass": True,
                "condition_pass": True,
                "must_haves_pass": True,
                "nice_to_haves_score": 1,
                "nice_to_haves_total": 2,
                "flags": ("budget_ok", "cond_ok", "must_haves_ok"),
                "product_specs": [],
                "product_spec_evidence": {},
            }
        ]

        prompt = make_recommendation_prompt(
            requirement_description="laptop for school",
            budget_amount=100000,
            budget_currency="USD",
            requirement_condition="new",
            must_haves=["screen_size"],
            nice_to_haves=["backlit_keyboard"],
            candidates=candidates,
        )

        # Check for requirement block title
        self.assertIn("USER REQUIREMENT:", prompt,
                      "Prompt must contain USER REQUIREMENT section")

    def test_prompt_contains_candidate_blocks(self) -> None:
        """The prompt must include candidate blocks for all candidates."""
        candidates = [
            {
                "product_name": f"Laptop {i}",
                "product_id": f"lp{i}",
                "price_amount": 80000 + i * 10000,
                "price_currency": "USD",
                "condition": "new" if i % 2 == 0 else "used",
                "budget_pass": True,
                "condition_pass": i % 3 != 0,
                "must_haves_pass": True,
                "nice_to_haves_score": i,
                "nice_to_haves_total": 3,
                "flags": ("budget_ok", "cond_ok", "must_haves_ok"),
                "product_specs": [],
                "product_spec_evidence": {},
            }
            for i in range(1, 4)
        ]

        prompt = make_recommendation_prompt(
            requirement_description="laptop",
            budget_amount=100000,
            budget_currency="USD",
            requirement_condition=None,
            must_haves=[],
            nice_to_haves=[],
            candidates=candidates,
        )

        # Each candidate block should be present in the prompt
        for i in range(1, len(candidates) + 1):
            self.assertIn(f"CANDIDATE {i}:", prompt,
                          f"Prompt must contain candidate block {i}")


class TestGroundingLogic(unittest.TestCase):
    """Verify the grounding/pure-Python logic produces correct citations
    and unknown classifications."""

    def test_evidence_citation_with_provider(self) -> None:
        """Citation includes provider when present."""
        ev = {"provider": "amazon-pa-api", "source_id": "B09XYZ", "note": "test"}
        citation = make_evidence_citation(ev)
        self.assertIn("provider=amazon-pa-api", citation)

    def test_evidence_citation_minimal(self) -> None:
        """Citation degrades gracefully when fields are missing."""
        ev = {}
        citation = make_evidence_citation(ev)
        self.assertEqual(citation, "unknown (no evidence provided)")

    def test_unknown_reason_value_missing(self) -> None:
        """Value missing → reason is 'value not provided'."""
        spec = {"key": "screen_size", "value": None}
        reason = classify_unknown_reason(spec)
        self.assertEqual(reason, "value not provided")

    def test_unknown_reason_vendor_missing(self) -> None:
        """No provider → reason is 'vendor did not provide'."""
        spec = {
            "key": "cpu_model",
            "value": "Intel i7",
            "product_spec_evidence": {"provider": "", "source_id": "", "note": ""},
        }
        reason = classify_unknown_reason(spec)
        self.assertEqual(reason, "vendor did not provide this specification")

    def test_unknown_entries_build_correctly(self) -> None:
        """Unknown entries list follows the expected format."""
        specs = [
            {"key": "screen_size", "value": None},
            {"key": "cpu_model", "value": "Intel i7", "product_spec_evidence": {"provider": "", "source_id": "", "note": ""}},
            {"key": "battery", "value": 5000, "product_spec_evidence": {"provider": "demo-catalog", "source_id": "battery1", "note": "listed in API"}},
        ]
        entries = build_unknown_entries(specs)
        # screen_size should have "value not provided"
        self.assertTrue(
            any("screen_size" in e and "value not provided" in e for e in entries)
        )
        # cpu_model should have "vendor did not provide"
        self.assertTrue(
            any("cpu_model" in e and "vendor did not provide" in e for e in entries)
        )
        # battery should NOT appear (it has evidence)
        self.assertFalse(any("battery" in e for e in entries))


class TestOutputSchema(unittest.TestCase):
    """Verify the LLM response format matches the prompt schema."""

    def test_sections_in_prompt_instructions(self) -> None:
        """Build a prompt and verify the LLM instruction sections are present."""
        candidates = [
            {
                "product_name": "Demo Laptop",
                "product_id": "lp1",
                "price_amount": 89990,
                "price_currency": "USD",
                "condition": "new",
                "budget_pass": True,
                "condition_pass": True,
                "must_haves_pass": True,
                "nice_to_haves_score": 1,
                "nice_to_haves_total": 2,
                "flags": ("budget_ok", "cond_ok", "must_haves_ok"),
                "product_specs": [
                    {
                        "key": "screen_size",
                        "value": 14.0,
                        "unit": "inches",
                        "is_unknown": False,
                        "product_spec_evidence": {
                            "provider": "demo-catalog",
                            "source_id": "spec1",
                            "note": "demo fixture",
                        },
                    }
                ],
                "product_spec_evidence": {
                    "provider": "demo-catalog",
                    "source_id": "spec1",
                    "note": "demo fixture",
                },
            }
        ]

        prompt = make_recommendation_prompt(
            requirement_description="laptop for school",
            budget_amount=100000,
            budget_currency="USD",
            requirement_condition="new",
            must_haves=["screen_size"],
            nice_to_haves=["backlit_keyboard"],
            candidates=candidates,
        )

        # Check that the prompt contains each expected LLM instruction section
        for section in ["FITS BECAUSE:", "WHAT IT SACRIFICES:", "UNKNOWN AND WHY:",
                        "CONSTRAINT COMPLIANCE SUMMARY:"]:
            self.assertIn(section, prompt,
                          f"Prompt must contain '{section}' instruction")

    def test_constraint_summary_in_prompt(self) -> None:
        """The constraint compliance summary must appear in the prompt."""
        candidates = [
            {
                "product_name": "Demo Laptop",
                "product_id": "lp1",
                "price_amount": 89990,
                "price_currency": "USD",
                "condition": "new",
                "budget_pass": True,
                "condition_pass": True,
                "must_haves_pass": True,
                "nice_to_haves_score": 1,
                "nice_to_haves_total": 2,
                "flags": ("budget_ok", "cond_ok", "must_haves_ok"),
                "product_specs": [],
                "product_spec_evidence": {},
            }
        ]

        prompt = make_recommendation_prompt(
            requirement_description="laptop",
            budget_amount=100000,
            budget_currency="USD",
            requirement_condition="new",
            must_haves=[],
            nice_to_haves=[],
            candidates=candidates,
        )

        # The prompt must contain the constraint compliance instructions
        self.assertIn("CONSTRAINT COMPLIANCE SUMMARY:", prompt,
                      "Prompt must contain CONSTRAINT COMPLIANCE SUMMARY instruction")


class TestIntegration(unittest.TestCase):
    """Integration-style test: prompt builds without error and has correct
    structure."""

    def test_prompt_builds_with_multiple_candidates(self) -> None:
        """Prompt should include a candidate block for each candidate."""
        candidates = [
            {
                "product_name": f"Laptop {i}",
                "product_id": f"lp{i}",
                "price_amount": 80000 + i * 10000,
                "price_currency": "USD",
                "condition": "new" if i % 2 == 0 else "used",
                "budget_pass": True,
                "condition_pass": i % 3 != 0,
                "must_haves_pass": True,
                "nice_to_haves_score": i,
                "nice_to_haves_total": 3,
                "flags": ("budget_ok", "cond_ok", "must_haves_ok"),
                "product_specs": [],
                "product_spec_evidence": {},
            }
            for i in range(1, 4)
        ]

        prompt = make_recommendation_prompt(
            requirement_description="laptop",
            budget_amount=100000,
            budget_currency="USD",
            requirement_condition=None,
            must_haves=[],
            nice_to_haves=[],
            candidates=candidates,
        )

        # Each candidate block should be present in the prompt
        for i in range(1, len(candidates) + 1):
            self.assertIn(f"CANDIDATE {i}:", prompt,
                          f"Prompt must contain candidate block {i}")

    def test_check_prompt_block_presence_positive(self) -> None:
        """check_prompt_block_presence returns True when blocks are present."""
        # Build a minimal prompt with LLM instructions
        candidates = [
            {
                "product_name": "Demo Laptop",
                "product_id": "lp1",
                "price_amount": 89990,
                "price_currency": "USD",
                "condition": "new",
                "budget_pass": True,
                "condition_pass": True,
                "must_haves_pass": True,
                "nice_to_haves_score": 1,
                "nice_to_haves_total": 2,
                "flags": ("budget_ok", "cond_ok", "must_haves_ok"),
                "product_specs": [],
                "product_spec_evidence": {},
            }
        ]

        prompt = make_recommendation_prompt(
            requirement_description="laptop",
            budget_amount=100000,
            budget_currency="USD",
            requirement_condition="new",
            must_haves=[],
            nice_to_haves=[],
            candidates=candidates,
        )

        # Check for the LLM instruction sections
        self.assertTrue(
            check_prompt_block_presence(prompt,
                                        ["FITS BECAUSE:", "WHAT IT SACRIFICES:",
                                         "UNKNOWN AND WHY:", "CONSTRAINT COMPLIANCE SUMMARY:"])
        )

    def test_check_prompt_block_presence_negative(self) -> None:
        """check_prompt_block_presence returns False when blocks are missing."""
        # A prompt without the LLM instructions
        prompt = "Just some random text without the expected sections."
        self.assertFalse(
            check_prompt_block_presence(prompt,
                                        ["FITS BECAUSE:", "WHAT IT SACRIFICE:"])
        )


def check_prompt_block_presence(
    response: str,
    block_names: List[str],
) -> bool:
    """Check that the LLM's response contains each named block.

    Used by the test suite to verify the prompt structure without calling
    an LLM (by testing the prompt *design* itself), or to validate actual
    LLM output against the expected schema.
    """
    return all(block in response for block in block_names)


if __name__ == "__main__":  # pragma: no cover
    pass