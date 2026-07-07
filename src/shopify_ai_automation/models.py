from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


Priority = Literal["low", "medium", "high", "urgent"]
ActionType = Literal[
    "draft_reply",
    "inventory_alert",
    "marketing_offer",
    "fraud_review",
    "analytics_note",
]


@dataclass(frozen=True)
class Customer:
    email: str
    name: str = "Customer"
    total_orders: int = 0
    tags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class LineItem:
    sku: str
    title: str
    quantity: int
    price: float


@dataclass(frozen=True)
class EcommerceEvent:
    event_id: str
    topic: str
    shop_domain: str
    customer: Customer
    line_items: list[LineItem]
    total_price: float
    currency: str = "USD"
    note: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgeSnippet:
    title: str
    text: str
    score: float


@dataclass(frozen=True)
class AutomationAction:
    action_type: ActionType
    title: str
    body: str
    priority: Priority
    confidence: float
    owner: str
    evidence: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AutomationResult:
    event_id: str
    topic: str
    summary: str
    actions: list[AutomationAction]
    retrieved_context: list[KnowledgeSnippet]
    estimated_savings_minutes: int

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["actions"] = [action.to_dict() for action in self.actions]
        return data
