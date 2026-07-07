from __future__ import annotations

import json
import os
from pathlib import Path

from .orchestrator import build_default_orchestrator
from .shopify import event_from_shopify_order, verify_shopify_hmac

try:
    from fastapi import FastAPI, Header, HTTPException, Request
except ImportError as exc:  # pragma: no cover
    raise RuntimeError("Install with `pip install -e .[api]` to run the FastAPI demo.") from exc


app = FastAPI(title="Shopify AI Automation POC")


@app.post("/webhooks/shopify/orders-create")
async def handle_order_create(
    request: Request,
    x_shopify_hmac_sha256: str | None = Header(default=None),
    x_shopify_shop_domain: str | None = Header(default="demo-store.myshopify.com"),
) -> dict:
    raw_body = await request.body()
    secret = os.getenv("SHOPIFY_WEBHOOK_SECRET")
    if secret and not verify_shopify_hmac(raw_body, x_shopify_hmac_sha256 or "", secret):
        raise HTTPException(status_code=401, detail="Invalid Shopify webhook signature.")

    payload = json.loads(raw_body.decode("utf-8"))
    event = event_from_shopify_order(payload, topic="orders/create", shop_domain=x_shopify_shop_domain or "unknown")
    orchestrator = build_default_orchestrator(Path("samples"), provider=os.getenv("AI_PROVIDER", "mock"))
    return orchestrator.run(event).to_dict()
