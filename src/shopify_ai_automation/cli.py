from __future__ import annotations

import argparse
import json
from pathlib import Path

from .ai import dumps_pretty
from .orchestrator import build_default_orchestrator
from .shopify import event_from_shopify_order


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the offline Shopify AI automation POC.")
    parser.add_argument("--samples-dir", type=Path, default=Path("samples"))
    parser.add_argument("--order", type=Path, default=Path("samples/order_created.json"))
    parser.add_argument("--provider", default="mock", help="Use mock/offline unless you intentionally add an adapter.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    payload = json.loads(args.order.read_text(encoding="utf-8"))
    event = event_from_shopify_order(payload, topic="orders/create", shop_domain="demo-store.myshopify.com")
    result = build_default_orchestrator(args.samples_dir, provider=args.provider).run(event)
    print(dumps_pretty(result.to_dict()))


if __name__ == "__main__":
    main()
