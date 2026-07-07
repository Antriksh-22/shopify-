from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from .evaluation import score_result
from .orchestrator import build_default_orchestrator
from .shopify import event_from_shopify_order, verify_shopify_hmac


def find_project_root() -> Path:
    candidates = [Path.cwd(), Path(__file__).resolve().parents[2]]
    for candidate in candidates:
        if (candidate / "web" / "index.html").exists() and (candidate / "samples" / "order_created.json").exists():
            return candidate
    return Path(__file__).resolve().parents[2]


PROJECT_ROOT = find_project_root()
SAMPLES_DIR = PROJECT_ROOT / "samples"
WEB_DIR = PROJECT_ROOT / "web"


async def website(request: Request) -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


async def sample_order(request: Request) -> JSONResponse:
    return JSONResponse(load_sample_order())


async def run_demo(request: Request) -> JSONResponse:
    body = await request.json()
    provider = str(body.get("provider") or "mock").strip().lower()
    payload = body.get("order") or load_sample_order()
    return JSONResponse(
        run_order(payload=payload, provider=provider, topic="orders/create", shop_domain="demo-store.myshopify.com")
    )


async def compare_providers(request: Request) -> JSONResponse:
    body = await request.json()
    payload = body.get("order") or load_sample_order()
    comparison: dict[str, Any] = {
        "mock": run_order(payload=payload, provider="mock", topic="orders/create", shop_domain="demo-store.myshopify.com")
    }
    if os.getenv("SARVAM_API_KEY"):
        try:
            comparison["sarvam"] = run_order(
                payload=payload,
                provider="sarvam",
                topic="orders/create",
                shop_domain="demo-store.myshopify.com",
            )
        except RuntimeError as exc:
            comparison["sarvam"] = {"status": "error", "message": str(exc)}
    else:
        comparison["sarvam"] = {
            "status": "not_configured",
            "message": "Set SARVAM_API_KEY in Render environment variables to enable live Sarvam comparison.",
        }
    return JSONResponse(comparison)


async def handle_order_create(request: Request) -> JSONResponse:
    raw_body = await request.body()
    secret = os.getenv("SHOPIFY_WEBHOOK_SECRET")
    provided_hmac = request.headers.get("x-shopify-hmac-sha256", "")
    if secret and not verify_shopify_hmac(raw_body, provided_hmac, secret):
        raise HTTPException(status_code=401, detail="Invalid Shopify webhook signature.")

    payload = json.loads(raw_body.decode("utf-8"))
    shop_domain = request.headers.get("x-shopify-shop-domain", "unknown")
    event = event_from_shopify_order(payload, topic="orders/create", shop_domain=shop_domain)
    provider = os.getenv("AI_PROVIDER", "mock")
    result = build_default_orchestrator(SAMPLES_DIR, provider=provider).run(event)
    response = result.to_dict()
    response["quality_score"] = score_result(provider, result).to_dict()
    return JSONResponse(response)


def load_sample_order() -> dict[str, Any]:
    return json.loads((SAMPLES_DIR / "order_created.json").read_text(encoding="utf-8"))


def run_order(payload: dict[str, Any], provider: str, topic: str, shop_domain: str) -> dict[str, Any]:
    if provider not in {"mock", "offline", "sarvam"}:
        raise HTTPException(status_code=400, detail="Provider must be 'mock' or 'sarvam'.")

    event = event_from_shopify_order(payload, topic=topic, shop_domain=shop_domain)
    result = build_default_orchestrator(SAMPLES_DIR, provider=provider).run(event)
    response = result.to_dict()
    response["provider"] = provider
    response["quality_score"] = score_result(provider, result).to_dict()
    return response


app = Starlette(
    debug=False,
    routes=[
        Route("/", website, methods=["GET"]),
        Route("/health", health, methods=["GET"]),
        Route("/api/sample-order", sample_order, methods=["GET"]),
        Route("/api/run-demo", run_demo, methods=["POST"]),
        Route("/api/compare", compare_providers, methods=["POST"]),
        Route("/webhooks/shopify/orders-create", handle_order_create, methods=["POST"]),
        Mount("/static", app=StaticFiles(directory=WEB_DIR), name="static"),
    ],
)
