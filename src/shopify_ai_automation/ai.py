from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


class AIEngine(ABC):
    @abstractmethod
    def complete_json(self, system: str, prompt: str) -> dict[str, Any]:
        """Return a structured model response."""


@dataclass
class MockAIEngine(AIEngine):
    """Deterministic offline stand-in for a real LLM."""

    def complete_json(self, system: str, prompt: str) -> dict[str, Any]:
        text = f"{system}\n{prompt}".lower()
        tone = "empathetic" if any(word in text for word in ["refund", "late", "delay"]) else "concise"
        risk = "high" if any(word in text for word in ["chargeback", "fraud", "mismatch"]) else "normal"
        return {
            "summary_style": tone,
            "risk": risk,
            "confidence": 0.86 if risk == "normal" else 0.78,
            "rationale": "Offline mock response generated from rules for repeatable tests.",
        }


class DisabledExternalAI(AIEngine):
    """Explicit placeholder so accidental network calls never happen in the demo."""

    def __init__(self, provider_name: str) -> None:
        self.provider_name = provider_name

    def complete_json(self, system: str, prompt: str) -> dict[str, Any]:
        raise RuntimeError(
            f"{self.provider_name} is disabled in this offline POC. "
            "Set AI_PROVIDER=mock or implement the adapter intentionally."
        )


def build_ai_engine(provider: str = "mock") -> AIEngine:
    normalized = provider.strip().lower()
    if normalized in {"", "mock", "offline"}:
        return MockAIEngine()
    return DisabledExternalAI(normalized)


def dumps_pretty(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, sort_keys=True)
