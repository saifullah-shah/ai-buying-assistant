"""Assistant service.

Two clearly-separated execution modes:

**LIVE mode** — an API key is present *and* the Gemini call succeeds. The prompt is
built by the existing, test-validated M4 builder
(:func:`aba.explanation.prompts.make_recommendation_prompt`), sent via the
``google.genai`` SDK, and the response is structurally validated by the existing M4
helper :func:`aba.explanation.grounding.check_prompt_block_presence`.

**DEMO mode** — no key, the SDK is unavailable, or the call fails. The response is
generated *deterministically* from the curated catalog using the existing M4
grounding helpers. It is explicitly flagged ``mode="demo"`` and carries a notice
telling the user it was not produced by a live AI service. A fabricated "LLM
answer" is never presented as a real one.
"""
from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Tuple

from aba.explanation.grounding import (
    build_unknown_entries,
    check_prompt_block_presence,
    make_constraint_summary,
    make_evidence_citation,
)
from aba.explanation.prompts import make_recommendation_prompt

#: Sections the LLM is contractually required to emit (from M4).
REQUIRED_BLOCKS = [
    "FITS BECAUSE:",
    "WHAT IT SACRIFICES:",
    "UNKNOWN AND WHY:",
    "CONSTRAINT COMPLIANCE SUMMARY:",
]

MODEL_ENV_VAR = "GEMINI_MODEL"
KEY_ENV_VAR = "GEMINI_API_KEY"

#: Model used when the environment does not pin one. Documented default only.
DEFAULT_MODEL = "gemini-3.8-flash"

DEMO_NOTICE = (
    "Demonstration mode: this explanation was generated deterministically from the "
    "curated demo dataset by local code, not by a live AI service."
)


def load_dotenv(path: str = ".env") -> None:
    """Minimal ``.env`` loader.

    Deliberately stdlib-only — the project has no python-dotenv dependency, and
    adding one for two keys would be unnecessary. Never logs or returns values.
    """
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            # Never overwrite a real environment variable.
            os.environ.setdefault(key, value)


def available_models() -> List[str]:
    """Best-effort list of model IDs the current key can reach (may be empty)."""
    key = os.environ.get(KEY_ENV_VAR)
    if not key:
        return []
    try:
        from google import genai
    except Exception:
        return []
    try:
        client = genai.Client(api_key=key)
        return [m.name for m in client.models.list()]
    except Exception:
        return []


def _selected_model() -> str:
    configured = (os.environ.get(MODEL_ENV_VAR) or "").strip()
    if configured and not configured.startswith("put_the_selected"):
        return configured
    return DEFAULT_MODEL


def _split_sections(text: str) -> Dict[str, str]:
    """Split a model response into the M4 sections, tolerating extra prose."""
    out: Dict[str, str] = {}
    pattern = re.compile(
        r"(FITS BECAUSE:|WHAT IT SACRIFICES:|UNKNOWN AND WHY:|CONSTRAINT COMPLIANCE SUMMARY:)"
    )
    matches = list(pattern.finditer(text))
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out[match.group(1)] = text[start:end].strip()
    return out


def _candidate_payloads(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Shape discovery results into the dicts ``make_recommendation_prompt`` expects."""
    payloads = []
    for item in results:
        product = item["product"]
        specs = []
        for spec in product["specs"]:
            specs.append(
                {
                    "key": spec["key"],
                    "value": spec["value"],
                    "unit": spec["unit"],
                    "product_spec_evidence": spec["evidence"],
                }
            )
        payloads.append(
            {
                "product_id": product["product_id"],
                "product_name": product["name"],
                "price_amount": item["offer"]["price_amount"],
                "price_currency": item["offer"]["price_currency"],
                "condition": item["offer"]["condition"],
                "budget_pass": item["matches"]["budget"],
                "condition_pass": item["matches"]["condition"],
                "must_haves_pass": item["matches"]["must_haves"],
                "nice_to_haves_score": item["matches"]["nice_to_haves_score"],
                "nice_to_haves_total": item["matches"]["nice_to_haves_total"],
                "flags": (),
                "product_specs": specs,
            }
        )
    return payloads


def _demo_explanation(results: List[Dict[str, Any]], query: Optional[str], budget: Optional[float]) -> List[Dict[str, Any]]:
    """Deterministic explanation built from the record itself using M4 grounding."""
    out = []
    for index, item in enumerate(results, start=1):
        product = item["product"]
        offer = item["offer"]
        matches = item["matches"]
        spec_rows = [
            {"key": s["key"], "label": s["label"], "value": s["value"], "unit": s["unit"]}
            for s in product["specs"]
        ]

        known = [r for r in spec_rows if r["value"] not in (None, "", "Unknown", "Not specified")]
        highlights = ", ".join(
            f"{r['label']} {r['value']}{(' ' + r['unit']) if r['unit'] else ''}"
            for r in known[:3]
        )
        fits = (
            f"{product['name']} matches the stated constraints. "
            f"Known highlights: {highlights}."
            if highlights
            else f"{product['name']} matches the stated constraints, but few specifications "
                 f"are recorded in the demo dataset."
        )
        if budget is not None:
            fits += (
                f" The listed price of {offer['price_amount']:,.0f} {offer['price_currency']} "
                f"is within the budget of {budget:,.0f} {offer['price_currency']}."
            )

        unknown_entries = build_unknown_entries(
            [{"key": s["key"], "value": s["value"], "product_spec_evidence": s["evidence"]}
             for s in product["specs"]]
        )

        sacrifices = (
            "This candidate meets all specified constraints."
            if matches["nice_to_haves_total"] == 0
            else f"It satisfies {matches['nice_to_haves_score']} of "
                 f"{matches['nice_to_haves_total']} stated nice-to-have specifications."
        )
        if matches["budget"]:
            headroom = budget - offer["price_amount"] if budget is not None else None
            if headroom is not None and headroom > 0:
                sacrifices += f" Budget headroom is {headroom:,.0f} {offer['price_currency']}."

        out.append(
            {
                "index": index,
                "product_id": product["product_id"],
                "product_name": product["name"],
                "fits_because": fits,
                "what_it_sacrifices": sacrifices,
                "unknown_and_why": unknown_entries
                or ["All specifications have known values."],
                "constraint_summary": make_constraint_summary(
                    matches["budget"],
                    matches["condition"],
                    matches["must_haves"],
                    matches["nice_to_haves_score"],
                    matches["nice_to_haves_total"],
                ),
                "evidence": make_evidence_citation(
                    {"provider": "synthetic-fixture", "note": "curated demo dataset"}
                ),
            }
        )
    return out


def explain(
    results: List[Dict[str, Any]],
    query: Optional[str] = None,
    budget_amount: Optional[float] = None,
    budget_currency: str = "PKR",
) -> Dict[str, Any]:
    """Explain the shortlist. Uses Gemini when possible, else deterministic demo mode."""
    load_dotenv()

    if not results:
        return {
            "mode": "none",
            "notice": "No candidates matched, so there is nothing to explain yet.",
            "explanations": [],
            "model": None,
            "raw_response": None,
            "validated": False,
        }

    candidates = _candidate_payloads(results)
    prompt = make_recommendation_prompt(
        requirement_description=query or "laptop purchase",
        budget_amount=budget_amount if budget_amount is not None else 0.0,
        budget_currency=budget_currency,
        requirement_condition=None,
        must_haves=[],
        nice_to_haves=[],
        candidates=candidates,
    )

    api_key = os.environ.get(KEY_ENV_VAR)
    model_name = _selected_model()
    error: Optional[str] = None

    if api_key:
        try:
            from google import genai

            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model_name, contents=prompt
            )
            raw = (getattr(response, "text", "") or "").strip()
            if raw:
                validated = check_prompt_block_presence(raw, REQUIRED_BLOCKS)
                sections = _split_sections(raw)
                return {
                    "mode": "live",
                    "notice": (
                        "Generated by the Gemini model. Automated checks confirm every "
                        "explanation must cite recorded specifications; verify claims "
                        "against the dataset before purchasing."
                        if validated
                        else "Generated by the Gemini model, but the response did not "
                             "contain every required section — treat it with caution."
                    ),
                    "explanations": [
                        {
                            "index": i + 1,
                            "product_id": cand["product_id"],
                            "product_name": cand["product_name"],
                            "fits_because": sections.get("FITS BECAUSE:", "").strip(),
                            "what_it_sacrifices": sections.get("WHAT IT SACRIFICES:", "").strip(),
                            "unknown_and_why": [
                                line.strip("- ").strip()
                                for line in sections.get("UNKNOWN AND WHY:", "").splitlines()
                                if line.strip()
                            ]
                            or ["Not reported by the model."],
                            "constraint_summary": sections.get(
                                "CONSTRAINT COMPLIANCE SUMMARY:", ""
                            ).strip(),
                        }
                        for i, cand in enumerate(candidates)
                    ],
                    "model": model_name,
                    "raw_response": raw,
                    "validated": validated,
                }
            error = "Gemini returned an empty response."
        except Exception as exc:  # network, auth, quota, model-not-found, ...
            error = f"{type(exc).__name__}: {str(exc)[:300]}"

    # Deterministic fallback — clearly labelled, never passed off as an LLM answer.
    return {
        "mode": "demo",
        "notice": DEMO_NOTICE + (f" Live call was not used because: {error}" if error else
                                 " No API key was configured."),
        "explanations": _demo_explanation(results, query, budget_amount),
        "model": None,
        "raw_response": None,
        "validated": False,
    }