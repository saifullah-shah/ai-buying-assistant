"""Tests for the additive API layer (``aba.api``).

These tests cover the new HTTP surface *and* the two real bugs found while
building it:

1. ``ProductSpecification.is_unknown()`` must treat "not disclosed" sentinel
   strings as unknown, so an undisclosed field can never satisfy a must-have.
2. FastAPI 0.143 requires ``Query(None)`` for repeated list query params; a bare
   ``Optional[List[str]] = None`` silently binds nothing.

The whole module skips cleanly when FastAPI/uvicorn are not installed, so the
project's zero-dependency unit tests still run in a bare environment.
"""
import unittest

try:
    from fastapi.testclient import TestClient

    from aba.api import assistant as assistant_mod
    from aba.api.app import app
    from aba.api.dataset import normalise_condition

    API_AVAILABLE = True
    IMPORT_ERROR = ""
except Exception as exc:  # pragma: no cover - environment dependent
    API_AVAILABLE = False
    IMPORT_ERROR = f"{type(exc).__name__}: {exc}"

from aba.domain.provenance import NOT_DISCLOSED_SENTINELS, ProductSpecification
from aba.shortlist.filter import _check_must_haves, _score_nice_to_haves


class TestUnknownSentinelHandling(unittest.TestCase):
    """Regression tests for the D-004 violation fixed in aba.domain.provenance."""

    def test_none_value_is_unknown(self):
        self.assertTrue(ProductSpecification(key="k", value=None).is_unknown())

    def test_blank_string_is_unknown(self):
        self.assertTrue(ProductSpecification(key="k", value="   ").is_unknown())

    def test_not_disclosed_sentinels_are_unknown(self):
        for raw in ("Unknown", "unknown", "Not specified", "N/A", "n/a",
                    "not available", "-", "TBD"):
            with self.subTest(raw=raw):
                self.assertTrue(
                    ProductSpecification(key="k", value=raw).is_unknown(),
                    f"{raw!r} should be treated as unknown",
                )

    def test_real_values_are_known(self):
        for raw in ("Intel Core i7", "16 GB", "Windows 11", "1920x1080",
                    "Integrated (illustrative)", "SSD (illustrative)"):
            with self.subTest(raw=raw):
                self.assertFalse(ProductSpecification(key="k", value=raw).is_unknown())

    def test_numeric_zero_is_known(self):
        # 0 is a real value; it must not be confused with "missing".
        self.assertFalse(ProductSpecification(key="k", value=0).is_unknown())

    def test_sentinel_list_contains_expected_entries(self):
        for expected in ("unknown", "not specified", "n/a", "none"):
            self.assertIn(expected, NOT_DISCLOSED_SENTINELS)

    def test_undisclosed_spec_cannot_satisfy_must_have(self):
        specs = (
            ProductSpecification(key="warranty", value="Unknown"),
            ProductSpecification(key="ram_gb", value=16),
        )
        self.assertFalse(_check_must_haves(specs, frozenset({"warranty"})))
        self.assertTrue(_check_must_haves(specs, frozenset({"ram_gb"})))

    def test_undisclosed_spec_does_not_score_as_nice_to_have(self):
        specs = (
            ProductSpecification(key="ram_gb", value=16),
            ProductSpecification(key="warranty", value="Unknown"),
        )
        matched, total = _score_nice_to_haves(specs, frozenset({"ram_gb", "warranty"}))
        self.assertEqual((matched, total), (1, 2))


@unittest.skipUnless(API_AVAILABLE, f"FastAPI stack unavailable: {IMPORT_ERROR}")
class TestConditionNormalisation(unittest.TestCase):

    def test_illustrative_suffix_is_stripped(self):
        self.assertEqual(normalise_condition("new (illustrative)"), ("new", True))

    def test_exact_value_is_not_flagged(self):
        self.assertEqual(normalise_condition("new"), ("new", False))

    def test_unknown_markers_map_to_unknown(self):
        for raw in ("Unknown", "not specified", "n/a", None, ""):
            with self.subTest(raw=raw):
                self.assertEqual(normalise_condition(raw)[0], "unknown")

    def test_unrecognised_does_not_guess(self):
        self.assertEqual(normalise_condition("slightly worn")[0], "unknown")


@unittest.skipUnless(API_AVAILABLE, f"FastAPI stack unavailable: {IMPORT_ERROR}")
class TestApiEndpoints(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    # ---- health / dataset -------------------------------------------------
    def test_health_ok(self):
        r = self.client.get("/api/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "ok")

    def test_dataset_reports_demo_status(self):
        r = self.client.get("/api/dataset")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertTrue(body["meta"]["is_demo"])
        self.assertEqual(body["meta"]["market"], "PK")
        self.assertIn("synthetic", body["meta"]["important_notice"].lower())
        self.assertEqual(body["product_count"], body["offer_count"])

    # ---- discovery --------------------------------------------------------
    def test_all_products_returned_without_filters(self):
        body = self.client.get("/api/products").json()
        self.assertEqual(body["total_matched"], 4)
        self.assertEqual(body["total_considered"], 4)

    def test_every_product_is_flagged_demo(self):
        body = self.client.get("/api/products").json()
        for item in body["results"]:
            self.assertTrue(item["product"]["is_demo"])
            self.assertTrue(item["offer"]["is_demo"])

    def test_budget_filters_and_explains_rejections(self):
        body = self.client.get("/api/products", params={"budget": 150000}).json()
        self.assertEqual(body["total_matched"], 1)
        self.assertEqual(body["results"][0]["offer"]["price_amount"], 125000.0)
        self.assertEqual(len(body["rejected"]), 3)
        for item in body["rejected"]:
            self.assertIn("budget", item["failed_constraints"])
            self.assertIn("budget", item["reasons"])

    def test_budget_is_a_hard_constraint_not_a_sort(self):
        body = self.client.get("/api/products", params={"budget": 100000}).json()
        self.assertEqual(body["total_matched"], 0)

    def test_condition_filter(self):
        body = self.client.get("/api/products", params={"condition": "used"}).json()
        self.assertEqual(body["total_matched"], 0)
        self.assertEqual(len(body["rejected"]), 4)

    def test_must_have_rejects_undisclosed_spec(self):
        """Regression: must_have=warranty must reject everything (warranty is Unknown)."""
        body = self.client.get("/api/products", params={"must_have": "warranty"}).json()
        self.assertEqual(body["total_matched"], 0)
        self.assertEqual(len(body["rejected"]), 4)
        for item in body["rejected"]:
            self.assertIn("must_haves", item["failed_constraints"])

    def test_must_have_accepts_known_spec(self):
        body = self.client.get("/api/products", params={"must_have": "ram_gb"}).json()
        self.assertEqual(body["total_matched"], 4)

    def test_repeated_list_query_params_bind(self):
        """Regression: FastAPI 0.143 needs Query(None) for repeated params."""
        body = self.client.get(
            "/api/products", params=[("must_have", "ram_gb"), ("must_have", "gpu")]
        ).json()
        self.assertEqual(body["total_matched"], 4)

    def test_nice_to_haves_are_scored_not_filtered(self):
        body = self.client.get(
            "/api/products", params=[("nice_to_have", "ram_gb"), ("nice_to_have", "gpu")]
        ).json()
        self.assertEqual(body["total_matched"], 4)
        self.assertEqual(body["results"][0]["matches"]["nice_to_haves_total"], 2)

    def test_min_ram_filter(self):
        body = self.client.get("/api/products", params={"min_ram": 16}).json()
        self.assertEqual(body["total_matched"], 3)
        self.assertNotIn("demo-laptop-001", [r["product"]["product_id"] for r in body["results"]])

    def test_sort_price_ascending(self):
        body = self.client.get("/api/products", params={"sort": "price_asc"}).json()
        prices = [r["offer"]["price_amount"] for r in body["results"]]
        self.assertEqual(prices, sorted(prices))

    def test_sort_price_descending(self):
        body = self.client.get("/api/products", params={"sort": "price_desc"}).json()
        prices = [r["offer"]["price_amount"] for r in body["results"]]
        self.assertEqual(prices, sorted(prices, reverse=True))

    def test_currency_unit_is_declared(self):
        body = self.client.get("/api/products").json()
        for item in body["results"]:
            self.assertEqual(item["offer"]["price_currency"], "PKR")
            self.assertEqual(item["offer"]["currency_unit"], "rupees")

    def test_freshness_is_reported(self):
        body = self.client.get("/api/products").json()
        for item in body["results"]:
            self.assertIn(item["offer"]["freshness"], ("fresh", "stale", "unknown"))

    # ---- validation -------------------------------------------------------
    def test_invalid_condition_is_400(self):
        self.assertEqual(
            self.client.get("/api/products", params={"condition": "mint"}).status_code, 400
        )

    def test_invalid_sort_is_400(self):
        self.assertEqual(
            self.client.get("/api/products", params={"sort": "wat"}).status_code, 400
        )

    def test_negative_budget_is_400(self):
        self.assertEqual(
            self.client.get("/api/products", params={"budget": -5}).status_code, 400
        )

    # ---- detail -----------------------------------------------------------
    def test_product_detail(self):
        r = self.client.get("/api/products/demo-laptop-001")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["product"]["product_id"], "demo-laptop-001")
        self.assertEqual(len(body["offers"]), 1)

    def test_product_detail_reports_unknown_fields(self):
        body = self.client.get("/api/products/demo-laptop-001").json()
        self.assertIn("Warranty", body["unknown_fields"])
        self.assertIn("warranty", body["unknown_field_keys"])

    def test_unknown_product_is_404(self):
        self.assertEqual(self.client.get("/api/products/nope").status_code, 404)

    # ---- compare ----------------------------------------------------------
    def test_compare_rows_align(self):
        r = self.client.post(
            "/api/compare",
            json={"product_ids": ["demo-laptop-001", "demo-laptop-003"]},
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(len(body["products"]), 2)
        for row in body["rows"]:
            self.assertEqual(len(row["cells"]), 2)

    def test_compare_marks_missing_not_zero(self):
        r = self.client.post(
            "/api/compare", json={"product_ids": ["demo-laptop-001", "demo-laptop-002"]}
        ).json()
        warranty = next(x for x in r["rows"] if x["key"] == "warranty")
        for cell in warranty["cells"]:
            self.assertTrue(cell["is_unknown"])
            self.assertEqual(cell["display"], "Unknown")

    def test_compare_requires_ids(self):
        self.assertEqual(self.client.post("/api/compare", json={"product_ids": []}).status_code, 400)

    def test_compare_limits_to_four(self):
        ids = ["demo-laptop-001", "demo-laptop-002", "demo-laptop-003", "demo-laptop-004", "x"]
        self.assertEqual(
            self.client.post("/api/compare", json={"product_ids": ids}).status_code, 422
        )

    def test_compare_unknown_id_is_404(self):
        self.assertEqual(
            self.client.post("/api/compare", json={"product_ids": ["nope"]}).status_code, 404
        )

    # ---- assistant --------------------------------------------------------
    def test_assistant_returns_explanations_for_results(self):
        r = self.client.post("/api/assistant", json={"budget_amount": 200000})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn(body["mode"], ("live", "demo"))
        self.assertTrue(body["explanations"])
        first = body["explanations"][0]
        for key in ("fits_because", "what_it_sacrifices", "unknown_and_why", "constraint_summary"):
            self.assertIn(key, first)

    def test_demo_mode_is_explicitly_labelled(self):
        """With no API key the assistant must fall back to labelled demo mode.

        The live Gemini endpoint is flaky (transient 503s under load), so this
        test pins the deterministic path by hiding the key from the process.
        """
        import os

        saved = os.environ.pop(assistant_mod.KEY_ENV_VAR, None)
        real_loader = assistant_mod.load_dotenv
        assistant_mod.load_dotenv = lambda *a, **k: None  # stop .env re-seeding the key
        try:
            body = self.client.post("/api/assistant", json={"budget_amount": 200000}).json()
        finally:
            assistant_mod.load_dotenv = real_loader
            if saved is not None:
                os.environ[assistant_mod.KEY_ENV_VAR] = saved
        self.assertEqual(body["mode"], "demo")
        self.assertIn("demonstration mode", body["notice"].lower())
        self.assertIsNone(body["model"])

    def test_demo_mode_does_not_claim_validation(self):
        """Demo output must not claim it passed live-model validation."""
        import os

        saved = os.environ.pop(assistant_mod.KEY_ENV_VAR, None)
        real_loader = assistant_mod.load_dotenv
        assistant_mod.load_dotenv = lambda *a, **k: None
        try:
            body = self.client.post("/api/assistant", json={"budget_amount": 200000}).json()
        finally:
            assistant_mod.load_dotenv = real_loader
            if saved is not None:
                os.environ[assistant_mod.KEY_ENV_VAR] = saved
        self.assertEqual(body["mode"], "demo")
        self.assertFalse(body["validated"])
        self.assertIsNone(body["raw_response"])

    def test_assistant_with_no_matches(self):
        body = self.client.post("/api/assistant", json={"budget_amount": 1000}).json()
        self.assertEqual(body["mode"], "none")
        self.assertEqual(body["explanations"], [])


if __name__ == "__main__":
    unittest.main()