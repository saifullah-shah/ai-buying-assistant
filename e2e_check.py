"""End-to-end HTTP validation against a *running* backend (not TestClient).

Run with the API already listening on 127.0.0.1:8000.
"""
import json
import sys
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"
PASS, FAIL = [], []


def call(method, path, payload=None):
    url = BASE + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"raw": raw[:200]}


def check(name, condition, detail=""):
    (PASS if condition else FAIL).append(name)
    print(("  PASS  " if condition else "  FAIL  ") + name + (f"   {detail}" if detail else ""))


print("=== 1. Health & dataset ===")
s, h = call("GET", "/api/health")
check("health 200", s == 200, str(h)[:90])
check("llm key detected", h["llm"]["api_key_present"] is True)
check("live model selected", h["llm"]["model"] == "gemini-3.8-flash")

s, d = call("GET", "/api/dataset")
check("dataset 200", s == 200)
check("dataset is demo", d["meta"]["is_demo"] is True)
check("market is PK", d["meta"]["market"] == "PK")
check("4 products / 4 offers", d["product_count"] == 4 and d["offer_count"] == 4)

print("\n=== 2. Discovery: budget as a HARD constraint ===")
s, allp = call("GET", "/api/products")
check("all products listed", allp["total_matched"] == 4)
check("every record flagged demo", all(r["product"]["is_demo"] and r["offer"]["is_demo"] for r in allp["results"]))
check("PKR unit declared", all(r["offer"]["currency_unit"] == "rupees" for r in allp["results"]))

s, b = call("GET", "/api/products?budget=150000")
check("budget 150k -> 1 match", b["total_matched"] == 1)
check("excluded 3 with reason", len(b["rejected"]) == 3 and all("budget" in x["failed_constraints"] for x in b["rejected"]))
check("matched price is 125000", b["results"][0]["offer"]["price_amount"] == 125000.0)

s, tiny = call("GET", "/api/products?budget=1000")
check("impossible budget -> 0 matches", tiny["total_matched"] == 0)

print("\n=== 3. Unknowns are never treated as satisfied ===")
s, w = call("GET", "/api/products?must_have=warranty")
check("must_have=warranty -> 0 matches", w["total_matched"] == 0, "warranty is 'Unknown' in every record")
s, r = call("GET", "/api/products?must_have=ram_gb")
check("must_have=ram_gb -> 4 matches", r["total_matched"] == 4)
s, c = call("POST", "/api/compare", {"product_ids": ["demo-laptop-001", "demo-laptop-002"]})
wrow = next(x for x in c["rows"] if x["key"] == "warranty")
check("compare marks warranty unknown", all(cell["is_unknown"] for cell in wrow["cells"]))
check("compare never renders 0 for unknown", all(cell["display"] != "0" for cell in wrow["cells"]))

print("\n=== 4. Sorting & filters ===")
s, asc = call("GET", "/api/products?sort=price_asc")
prices = [x["offer"]["price_amount"] for x in asc["results"]]
check("price_asc sorted", prices == sorted(prices), str([int(p) for p in prices]))
s, desc = call("GET", "/api/products?sort=price_desc")
check("price_desc sorted", [x["offer"]["price_amount"] for x in desc["results"]] == sorted(prices, reverse=True))
s, ram = call("GET", "/api/products?min_ram=16")
check("min_ram=16 -> 3 matches", ram["total_matched"] == 3)
s, cond = call("GET", "/api/products?condition=used")
check("condition=used -> 0 matches", cond["total_matched"] == 0)

print("\n=== 5. Query hints (suggestions, never hard filters) ===")
s, q = call("GET", "/api/products?q=laptop%20for%20machine%20learning")
check("query hints returned", len(q["hints"]["suggested_nice_to_haves"]) > 0, str(q["hints"]))
check("query alone does not filter", q["total_matched"] == 4)

print("\n=== 6. Product detail ===")
s, p = call("GET", "/api/products/demo-laptop-001")
check("detail 200", s == 200)
check("has 10 specs", len(p["product"]["specs"]) == 10)
check("unknown fields reported", set(p["unknown_field_keys"]) == {"operating_system", "warranty"})
check("availability not invented", all("availability" not in o for o in p["offers"]))
s, nf = call("GET", "/api/products/nope")
check("unknown product -> 404", nf == 404 or s == 404)

print("\n=== 7. Validation errors are real 400s ===")
for qs, label in [("condition=mint", "bad condition"), ("sort=wat", "bad sort"), ("budget=-5", "negative budget")]:
    s, body = call("GET", "/api/products?" + qs)
    check(f"{label} -> 400", s == 400, f"got {s}")

print("\n=== 8. Assistant (live Gemini, real network call) ===")
s, a = call("POST", "/api/assistant", {"query": "laptop for programming", "budget_amount": 200000})
check("assistant 200", s == 200)
check("mode reported honestly", a["mode"] in ("live", "demo"), f"mode={a['mode']}")
check("has explanations", len(a["explanations"]) > 0)
if a["explanations"]:
    e0 = a["explanations"][0]
    check("explanation has fits_because", bool(e0["fits_because"]))
    check("explanation has sacrifices", bool(e0["what_it_sacrifices"]))
    check("explanation has unknowns list", isinstance(e0["unknown_and_why"], list) and len(e0["unknown_and_why"]) > 0)
if a["mode"] == "live":
    check("live model named", a["model"] == "gemini-3.8-flash")
    check("live response section-validated", a["validated"] is True)
    print("        notice:", a["notice"][:150])
    print("        sample:", a["explanations"][0]["fits_because"][:220])
else:
    print("        notice:", a["notice"][:200])

print("\n=== 9. Assistant with no matches ===")
s, z = call("POST", "/api/assistant", {"budget_amount": 1000})
check("no matches -> mode none", z["mode"] == "none")
check("no explanations returned", z["explanations"] == [])

print("\n" + "=" * 62)
print(f"  HTTP E2E: {len(PASS)} passed, {len(FAIL)} failed")
if FAIL:
    for f in FAIL:
        print("   FAILED:", f)
print("=" * 62)
sys.exit(1 if FAIL else 0)