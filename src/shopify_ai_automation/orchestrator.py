from __future__ import annotations

import json
from pathlib import Path

from .agents import InventoryAgent, MarketingAgent, RiskAgent, SupportAgent
from .ai import AIEngine, build_ai_engine
from .models import AutomationAction, AutomationResult, EcommerceEvent
from .rag import LocalKnowledgeBase
from .shopify import event_from_shopify_order


class AutomationOrchestrator:
    def __init__(self, knowledge_base: LocalKnowledgeBase, catalog: dict[str, dict], ai: AIEngine) -> None:
        self.knowledge_base = knowledge_base
        self.agents = [
            SupportAgent(ai),
            InventoryAgent(catalog),
            MarketingAgent(),
            RiskAgent(ai),
        ]

    def run(self, event: EcommerceEvent) -> AutomationResult:
        query = " ".join(
            [
                event.topic,
                event.note,
                " ".join(item.title for item in event.line_items),
                " ".join(event.customer.tags),
            ]
        )
        context = self.knowledge_base.search(query, limit=4)
        actions: list[AutomationAction] = []
        for agent in self.agents:
            actions.extend(agent.run(event, context))

        actions.sort(key=lambda action: priority_rank(action.priority), reverse=True)
        summary = summarize_event(event, actions)
        return AutomationResult(
            event_id=event.event_id,
            topic=event.topic,
            summary=summary,
            actions=actions,
            retrieved_context=context,
            estimated_savings_minutes=estimate_savings(actions),
        )


def priority_rank(priority: str) -> int:
    return {"low": 1, "medium": 2, "high": 3, "urgent": 4}.get(priority, 0)


def estimate_savings(actions: list[AutomationAction]) -> int:
    minutes_by_type = {
        "draft_reply": 8,
        "inventory_alert": 5,
        "marketing_offer": 6,
        "fraud_review": 10,
        "analytics_note": 4,
    }
    return sum(minutes_by_type.get(action.action_type, 4) for action in actions)


def summarize_event(event: EcommerceEvent, actions: list[AutomationAction]) -> str:
    item_count = sum(item.quantity for item in event.line_items)
    return (
        f"{event.topic} for {event.customer.name}: {item_count} items, "
        f"{event.currency} {event.total_price:.2f}, {len(actions)} recommended actions."
    )


def load_catalog(path: Path) -> dict[str, dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_default_orchestrator(samples_dir: Path, provider: str = "mock") -> AutomationOrchestrator:
    knowledge_base = LocalKnowledgeBase.from_markdown(samples_dir / "policies.md")
    catalog = load_catalog(samples_dir / "catalog.json")
    return AutomationOrchestrator(knowledge_base, catalog, build_ai_engine(provider))


def run_sample_order(samples_dir: Path, provider: str = "mock") -> AutomationResult:
    payload = json.loads((samples_dir / "order_created.json").read_text(encoding="utf-8"))
    event = event_from_shopify_order(payload, topic="orders/create", shop_domain="demo-store.myshopify.com")
    return build_default_orchestrator(samples_dir, provider).run(event)
