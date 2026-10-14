"""FastAPI application exposing the existing deterministic ``aba`` logic.

This is a thin transport layer. It contains **no** constraint logic, **no**
scoring logic and **no** product data of its own — every answer is produced by
the existing M1–M4 modules (see :mod:`aba.api.service`).

Routes
------
``GET  /api/health``          liveness + which optional capabilities are present
``GET  /api/dataset``         dataset provenance and the demo-data notice
``GET  /api/products``        discovery: query, budget, condition, filters, sort
``GET  /api/products/{id}``   product detail
``POST /api/compare``         side-by-side comparison
``POST /api/assistant``       grounded explanation (live Gemini or labelled demo)
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from aba.api import assistant as assistant_mod
from aba.api import service

app = FastAPI(
    title="AI Buying Decision Assistant API",
    description=(
        "Read-only API over the project's deterministic M1-M4 logic. "
        "All catalog data served here is synthetic demo data."
    ),
    version="1.0.0",
)

# The Vite dev server runs on a different origin. This is a local dev allowance,
# not a production deployment decision.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class CompareRequest(BaseModel):
    product_ids: List[str] = Field(default_factory=list, max_length=4)


class AssistantRequest(BaseModel):
    query: Optional[str] = None
    budget_amount: Optional[float] = None
    budget_currency: str = "PKR"
    product_ids: List[str] = Field(default_factory=list)
    sort: str = "relevance"


@app.get("/api/health")
def health() -> Dict[str, Any]:
    """Report process health and whether the optional AI path is usable."""
    assistant_mod.load_dotenv()
    has_key = bool(assistant_mod.os.environ.get(assistant_mod.KEY_ENV_VAR))
    return {
        "status": "ok",
        "service": "aba-api",
        "llm": {
            "api_key_present": has_key,
            "model": assistant_mod._selected_model() if has_key else None,
            "mode_if_used": "live" if has_key else "demo",
        },
    }


@app.get("/api/dataset")
def dataset() -> Dict[str, Any]:
    """Dataset provenance plus the mandatory demo-data notice."""
    products, offers, meta = service.build_catalog()
    return {
        "meta": meta,
        "product_count": len(products),
        "offer_count": len(offers),
    }


@app.get("/api/products")
def products(
    q: Optional[str] = None,
    budget: Optional[float] = None,
    currency: str = "PKR",
    condition: Optional[str] = None,
    # NOTE: in FastAPI 0.143 a bare `Optional[List[str]] = None` silently fails to
    # bind repeated query params (it arrives as None). `Query(None)` is required.
    must_have: Optional[List[str]] = Query(None),
    nice_to_have: Optional[List[str]] = Query(None),
    min_ram: Optional[float] = None,
    min_storage: Optional[float] = None,
    max_weight: Optional[float] = None,
    min_screen: Optional[float] = None,
    sort: str = "relevance",
) -> Dict[str, Any]:
    """Discovery endpoint backed by the real M3 constraint checks."""
    if condition and condition not in service.VALID_CONDITIONS:
        raise HTTPException(
            status_code=400,
            detail=f"condition must be one of {list(service.VALID_CONDITIONS)}",
        )
    if sort not in service.SORT_OPTIONS:
        raise HTTPException(
            status_code=400, detail=f"sort must be one of {list(service.SORT_OPTIONS)}"
        )
    if budget is not None and budget <= 0:
        raise HTTPException(status_code=400, detail="budget must be greater than zero")

    return service.discover(
        query=q,
        budget_amount=budget,
        budget_currency=currency,
        condition=condition,
        must_haves=must_have,
        nice_to_haves=nice_to_have,
        min_ram=min_ram,
        min_storage=min_storage,
        max_weight=max_weight,
        min_screen=min_screen,
        sort=sort,
    )


@app.get("/api/products/{product_id}")
def product_detail(product_id: str) -> Dict[str, Any]:
    detail = service.get_product(product_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Product not found in the demo dataset")
    return detail


@app.post("/api/compare")
def compare(request: CompareRequest) -> Dict[str, Any]:
    ids = [pid for pid in request.product_ids if pid]
    if not ids:
        raise HTTPException(status_code=400, detail="product_ids must contain at least one id")
    if len(ids) > 4:
        raise HTTPException(status_code=400, detail="A maximum of 4 products can be compared")
    result = service.compare(ids)
    if not result["products"]:
        raise HTTPException(status_code=404, detail="None of the supplied ids exist")
    return result


@app.post("/api/assistant")
def assistant(request: AssistantRequest) -> Dict[str, Any]:
    """Grounded explanation of the current shortlist.

    Runs the same deterministic discovery first, so the assistant can only ever
    explain candidates that actually passed the hard constraints.
    """
    if request.product_ids:
        chosen = [service.get_product(pid) for pid in request.product_ids]
        results = [
            {
                "product": c["product"],
                "offer": c["offers"][0] if c["offers"] else None,
                "matches": {
                    "budget": True,
                    "condition": True,
                    "must_haves": True,
                    "nice_to_haves_score": 0,
                    "nice_to_haves_total": 0,
                },
                "reasons": {"filters": []},
            }
            for c in chosen
            if c
        ]
    else:
        discovery = service.discover(
            query=request.query,
            budget_amount=request.budget_amount,
            budget_currency=request.budget_currency,
            sort=request.sort,
        )
        results = discovery["results"]

    payload = assistant_mod.explain(
        results,
        query=request.query,
        budget_amount=request.budget_amount,
        budget_currency=request.budget_currency,
    )
    payload["shortlist_size"] = len(results)
    return payload