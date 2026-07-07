from __future__ import annotations

import base64
import hashlib
import hmac
from typing import Any

from .models import Customer, EcommerceEvent, LineItem


def verify_shopify_hmac(raw_body: bytes, provided_hmac: str, secret: str) -> bool:
    digest = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).digest()
    expected = base64.b64encode(digest).decode("utf-8")
    return hmac.compare_digest(expected, provided_hmac)


def event_from_shopify_order(payload: dict[str, Any], topic: str, shop_domain: str) -> EcommerceEvent:
    customer_payload = payload.get("customer") or {}
    line_items = [
        LineItem(
            sku=str(item.get("sku") or item.get("variant_id") or "UNKNOWN"),
            title=str(item.get("title") or "Untitled product"),
            quantity=int(item.get("quantity") or 0),
            price=float(item.get("price") or 0),
        )
        for item in payload.get("line_items", [])
    ]
    customer = Customer(
        email=str(customer_payload.get("email") or payload.get("email") or "unknown@example.com"),
        name=" ".join(
            part
            for part in [
                str(customer_payload.get("first_name") or "").strip(),
                str(customer_payload.get("last_name") or "").strip(),
            ]
            if part
        )
        or "Customer",
        total_orders=int(customer_payload.get("orders_count") or 0),
        tags=[tag.strip() for tag in str(customer_payload.get("tags") or "").split(",") if tag.strip()],
    )
    return EcommerceEvent(
        event_id=str(payload.get("id") or payload.get("admin_graphql_api_id") or "local-event"),
        topic=topic,
        shop_domain=shop_domain,
        customer=customer,
        line_items=line_items,
        total_price=float(payload.get("total_price") or 0),
        currency=str(payload.get("currency") or "USD"),
        note=str(payload.get("note") or ""),
        raw=payload,
    )
