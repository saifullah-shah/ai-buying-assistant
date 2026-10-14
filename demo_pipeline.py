"""M5 - end-to-end prototype pipeline.

Wires the existing deterministic layers together and prints a readable
demonstration of the whole flow:

    natural-language need
        -> M2  validated ``Requirement``
        -> M3  hard-constraint filtering + nice-to-have scoring
        -> M1  freshness of each surviving offer
        -> M4  prompt text for a grounded explanation

No LLM API call is made here. The prompt is *prepared* using the real
``aba.explanation.prompts.make_recommendation_prompt`` builder so its shape can
be inspected; sending it to a model is a separate concern handled by
``aba.api.assistant``.

Run it with::

    python demo_pipeline.py
    python demo_pipeline.py --budget 300000 --need "a light laptop for university"

Output is deliberately ASCII-only: the Windows console defaults to cp1252 and
cannot encode box-drawing or bullet glyphs.
"""
from __future__ import annotations

import argparse
import sys
from typing import Dict, List, Tuple

from aba.api.dataset import build_catalog, product_view
from aba.domain.freshness import freshness
from aba.explanation.prompts import make_recommendation_prompt
from aba.requirements.model import Requirement, RequirementValidationResult
from aba.shortlist.filter import (
    _check_budget,
    _check_condition,
    _check_must_haves,
    _score_nice_to_haves,
)

CURRENCY = "PKR"
BAR = "-" * 74


def rule(title: str = "") -> None:
    if title:
        print(f"\n{BAR}\n{title}\n{BAR}")
    else:
        print(BAR)


def build_requirement(
    need: str,
    budget: float,
    condition: str | None,
    must_haves: List[str],
    nice_to_haves: List[str],
) -> Requirement:
    """M2 - construct the structured requirement (validated on construction)."""
    return Requirement(
        need_description=need,
        budget_amount=budget,
        budget_currency=CURRENCY,
        market="PK",
        condition=condition,
        must_haves=frozenset(must_haves),
        nice_to_haves=frozenset(nice_to_haves),
    )


def filter_candidates(
    requirement: Requirement,
) -> Tuple[List[Dict], List[Dict], Dict]:
    """M3 - apply hard constraints and score the survivors.

    Reuses the very helpers that ``aba.shortlist.filter.get_shortlist`` uses, so
    this demonstration cannot drift from the tested behaviour.
    """
    products, offers, _meta = build_catalog()

    matched: List[Dict] = []
    rejected: List[Dict] = []

    for offer in offers:
        product = next(p for p in products if p.product_id == offer.product_id)

        budget_ok = _check_budget(
            offer.price_amount,
            offer.price_currency,
            requirement.budget_amount,
            requirement.budget_currency,
        )
        condition_ok = _check_condition(offer.condition, requirement.condition)
        must_ok = _check_must_haves(product.specs, requirement.must_haves)
        nth_score, nth_total = _score_nice_to_haves(
            product.specs, requirement.nice_to_haves
        )

        record = {
            "product": product,
            "offer": offer,
            "budget_ok": budget_ok,
            "condition_ok": condition_ok,
            "must_ok": must_ok,
            "nth_score": nth_score,
            "nth_total": nth_total,
        }

        if budget_ok and condition_ok and must_ok:
            matched.append(record)
        else:
            failed = []
            if not budget_ok:
                failed.append("budget")
            if not condition_ok:
                failed.append("condition")
            if not must_ok:
                failed.append("must-haves")
            record["failed"] = failed
            rejected.append(record)

    matched.sort(key=lambda r: (-r["nth_score"], r["offer"].price_amount))
    return matched, rejected, {"count": len(matched) + len(rejected)}


def spec_lines(product) -> str:
    view = product_view(product)
    parts = []
    for spec in view["specs"]:
        if spec["is_unknown"]:
            parts.append(f"{spec['key']}=<unknown>")
        else:
            unit = f" {spec['unit']}" if spec["unit"] else ""
            parts.append(f"{spec['key']}={spec['value']}{unit}")
    return ", ".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the M1-M5 demonstration pipeline")
    parser.add_argument(
        "--need", default="a laptop for university study",
        help="natural-language need",
    )
    parser.add_argument(
        "--budget", type=float, default=200000.0,
        help=f"maximum budget in {CURRENCY}",
    )
    parser.add_argument(
        "--condition", default=None,
        choices=["new", "refurbished", "used", "open-box"],
    )
    parser.add_argument(
        "--must-have", action="append", default=[],
        help="spec key that must have a known value (repeatable)",
    )
    parser.add_argument(
        "--nice-to-have", action="append", default=[],
        help="spec key used for preference scoring (repeatable)",
    )
    parser.add_argument(
        "--show-prompt", action="store_true",
        help="print the full M4 prompt text",
    )
    args = parser.parse_args()

    # ---------------------------------------------------------------- M2 ----
    rule("M2 | REQUIREMENT")
    try:
        requirement = build_requirement(
            args.need, args.budget, args.condition,
            args.must_have, args.nice_to_have,
        )
    except (ValueError, TypeError) as exc:
        print(f"  Invalid requirement: {exc}")
        return 1

    validation: RequirementValidationResult = requirement.validate()
    print(f"  need            : {requirement.need_description}")
    print(f"  budget          : {requirement.budget_amount:,.0f} {requirement.budget_currency}")
    print(f"  market          : {requirement.market}")
    print(f"  condition       : {requirement.condition or 'any'}")
    print(f"  must-have specs : {sorted(requirement.must_haves) or '-'}")
    print(f"  prefer specs    : {sorted(requirement.nice_to_haves) or '-'}")
    print(f"  valid           : {validation.is_valid}")
    for error in validation.errors:
        print(f"    ! {error}")
    if not validation.is_valid:
        return 1

    # ---------------------------------------------------------------- M3 ----
    rule("M3 | CONSTRAINT FILTERING")
    matched, rejected, info = filter_candidates(requirement)
    print(f"  considered {info['count']} demonstration offers")
    print(f"  matched {len(matched)} | excluded {len(rejected)}")

    if rejected:
        print("\n  Excluded:")
        for record in rejected:
            print(
                f"    [x] {record['product'].name:<34}"
                f"{record['offer'].price_amount:>10,.0f} {record['offer'].price_currency}"
                f"  [{', '.join(record['failed'])}]"
            )

    if not matched:
        print("\n  No candidate satisfies every hard constraint.")
        print("  Nothing can be ranked or explained - this is the correct outcome.")
        return 0

    print("\n  Shortlist (preference match desc, then price asc):")
    for index, record in enumerate(matched, start=1):
        nth = f"{record['nth_score']}/{record['nth_total']}" if record["nth_total"] else "-"
        print(
            f"    {index}. {record['product'].name:<34}"
            f"{record['offer'].price_amount:>10,.0f} {record['offer'].price_currency}"
            f"  prefer {nth}"
        )

    # ---------------------------------------------------------------- M1 ----
    rule("M1 | PROVENANCE AND FRESHNESS")
    for record in matched:
        offer = record["offer"]
        status = freshness(offer.observed_at)
        print(f"  {record['product'].name}")
        print(f"    seller      : {offer.seller_id}")
        print(f"    observed at : {offer.observed_at.isoformat()}")
        print(f"    freshness   : {status.value}")
        print(f"    source      : {offer.source_id}")
        print(f"    specs       : {spec_lines(record['product'])}")

    unknown = {}
    for record in matched:
        labels = [
            s["label"]
            for s in product_view(record["product"])["specs"]
            if s["is_unknown"]
        ]
        if labels:
            unknown[record["product"].name] = labels
    if unknown:
        print("\n  Unknown facts (never guessed, never scored as satisfied):")
        for name, labels in unknown.items():
            print(f"    - {name}: {', '.join(labels)}")

    # ---------------------------------------------------------------- M4 ----
    rule("M4 | GROUNDED EXPLANATION PROMPT (prepared, not sent)")
    candidates = []
    for record in matched:
        view = product_view(record["product"])
        candidates.append(
            {
                "product_id": record["product"].product_id,
                "product_name": record["product"].name,
                "price_amount": record["offer"].price_amount,
                "price_currency": record["offer"].price_currency,
                "condition": record["offer"].condition.value,
                "budget_pass": record["budget_ok"],
                "condition_pass": record["condition_ok"],
                "must_haves_pass": record["must_ok"],
                "nice_to_haves_score": record["nth_score"],
                "nice_to_haves_total": record["nth_total"],
                "flags": (),
                "product_specs": [
                    {
                        "key": s["key"],
                        "value": s["value"],
                        "unit": s["unit"],
                        "product_spec_evidence": s["evidence"],
                    }
                    for s in view["specs"]
                ],
            }
        )

    prompt = make_recommendation_prompt(
        requirement_description=requirement.need_description,
        budget_amount=requirement.budget_amount,
        budget_currency=requirement.budget_currency,
        requirement_condition=requirement.condition,
        must_haves=sorted(requirement.must_haves),
        nice_to_haves=sorted(requirement.nice_to_haves),
        candidates=candidates,
    )

    if args.show_prompt:
        print(prompt)
    else:
        preview = prompt.splitlines()
        print(f"  prompt built: {len(prompt)} characters, {len(preview)} lines")
        print("  (run with --show-prompt to print it in full)")
        for line in preview[:6]:
            print(f"    | {line}")
        print("    | ...")

    rule()
    print("Demo data only - nothing above is a real listing, price or availability claim.")
    return 0


if __name__ == "__main__":
    sys.exit(main())