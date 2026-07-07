from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol

from .ai import AIEngine
from .models import AutomationAction, EcommerceEvent, KnowledgeSnippet


class Agent(Protocol):
    name: str

    def run(self, event: EcommerceEvent, context: list[KnowledgeSnippet]) -> list[AutomationAction]:
        ...


@dataclass
class SupportAgent:
    ai: AIEngine
    name: str = "support-agent"

    def run(self, event: EcommerceEvent, context: list[KnowledgeSnippet]) -> list[AutomationAction]:
        note = event.note.lower()
        if not any(word in note for word in ["refund", "return", "late", "delay", "damaged"]):
            return []

        support_prompt = json.dumps(
            {
                "customer_name": event.customer.name,
                "customer_email": event.customer.email,
                "topic": event.topic,
                "order_total": event.total_price,
                "currency": event.currency,
                "customer_note": event.note,
                "line_items": [item.title for item in event.line_items],
                "policy_context": [{"title": item.title, "text": item.text} for item in context],
                "task": (
                    "Draft a concise, ready-to-send support reply. Acknowledge the issue, "
                    "ask for any required evidence, explain the next step, and do not approve "
                    "refunds automatically."
                ),
            },
            sort_keys=True,
        )
        model_view = self.ai.complete_json("Create a Shopify customer support action.", support_prompt)
        policy_titles = [item.title for item in context]
        body = (
            f"Draft reply for {event.customer.name}: acknowledge the issue, reference "
            f"{', '.join(policy_titles) or 'store policy'}, and offer a clear next step."
        )
        body = str(model_view.get("draft_reply") or body)
        return [
            AutomationAction(
                action_type="draft_reply",
                title="Customer support draft",
                body=body,
                priority="high" if "refund" in note or "damaged" in note else "medium",
                confidence=float(model_view["confidence"]),
                owner=self.name,
                evidence=policy_titles,
                metadata={"tone": model_view["summary_style"], "rationale": model_view.get("rationale", "")},
            )
        ]


@dataclass
class InventoryAgent:
    catalog: dict[str, dict[str, int | str]]
    name: str = "inventory-agent"

    def run(self, event: EcommerceEvent, context: list[KnowledgeSnippet]) -> list[AutomationAction]:
        actions: list[AutomationAction] = []
        for item in event.line_items:
            record = self.catalog.get(item.sku, {})
            current_stock = int(record.get("stock", 999))
            reorder_point = int(record.get("reorder_point", 0))
            projected_stock = current_stock - item.quantity
            if projected_stock <= reorder_point:
                actions.append(
                    AutomationAction(
                        action_type="inventory_alert",
                        title=f"Reorder {item.sku}",
                        body=(
                            f"{item.title} will drop to {projected_stock} units after this order. "
                            f"Reorder point is {reorder_point}."
                        ),
                        priority="urgent" if projected_stock <= 0 else "high",
                        confidence=0.98,
                        owner=self.name,
                        evidence=[f"stock={current_stock}", f"reorder_point={reorder_point}"],
                        metadata={"sku": item.sku, "projected_stock": projected_stock},
                    )
                )
        return actions


@dataclass
class MarketingAgent:
    name: str = "marketing-agent"

    def run(self, event: EcommerceEvent, context: list[KnowledgeSnippet]) -> list[AutomationAction]:
        if event.customer.total_orders < 3 or event.total_price < 75:
            return []

        purchased_titles = ", ".join(item.title for item in event.line_items)
        return [
            AutomationAction(
                action_type="marketing_offer",
                title="Post-purchase retention offer",
                body=(
                    f"Send a loyalty email to {event.customer.email} with care tips for "
                    f"{purchased_titles} and a 10 percent accessory offer."
                ),
                priority="medium",
                confidence=0.82,
                owner=self.name,
                evidence=["repeat_customer", "order_value_threshold"],
                metadata={"customer_orders": event.customer.total_orders},
            )
        ]


@dataclass
class RiskAgent:
    ai: AIEngine
    name: str = "risk-agent"

    def run(self, event: EcommerceEvent, context: list[KnowledgeSnippet]) -> list[AutomationAction]:
        signals = []
        note = event.note.lower()
        if "chargeback" in note or "fraud" in note:
            signals.append("customer note mentions fraud or chargeback")
        if event.total_price >= 500 and event.customer.total_orders == 0:
            signals.append("high value first order")

        if not signals:
            return []

        model_view = self.ai.complete_json(
            "Assess ecommerce operational risk.",
            json.dumps(
                {
                    "customer_note": event.note,
                    "total_price": event.total_price,
                    "customer_total_orders": event.customer.total_orders,
                    "signals": signals,
                },
                sort_keys=True,
            ),
        )
        return [
            AutomationAction(
                action_type="fraud_review",
                title="Manual review recommended",
                body=str(
                    model_view.get("review_note")
                    or "Hold fulfillment until payment, address, and customer history are reviewed."
                ),
                priority="urgent" if model_view["risk"] == "high" else "high",
                confidence=float(model_view["confidence"]),
                owner=self.name,
                evidence=signals,
                metadata={"risk": model_view["risk"]},
            )
        ]
