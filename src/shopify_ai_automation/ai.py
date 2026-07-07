from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
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


@dataclass
class SarvamAIEngine(AIEngine):
    """Small Sarvam chat-completions adapter using only the Python standard library."""

    api_key: str
    model: str = "sarvam-105b"
    endpoint: str = "https://api.sarvam.ai/v1/chat/completions"
    timeout_seconds: int = 30

    def complete_json(self, system: str, prompt: str) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        f"{system}\n"
                        "Return only valid JSON with these keys when relevant: "
                        "summary_style, risk, confidence, draft_reply, review_note, rationale. "
                        "Use confidence as a number from 0 to 1."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        }
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Sarvam API returned HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Sarvam API request failed: {exc.reason}") from exc

        content = response_payload["choices"][0]["message"]["content"]
        parsed = parse_json_object(content)
        parsed.setdefault("confidence", 0.75)
        parsed.setdefault("summary_style", "empathetic")
        parsed.setdefault("risk", "normal")
        return parsed


def parse_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, flags=re.DOTALL)
    if fenced:
        cleaned = fenced.group(1)
    else:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start : end + 1]
    parsed = json.loads(cleaned)
    if not isinstance(parsed, dict):
        raise ValueError("Expected a JSON object from the AI provider.")
    return parsed


def build_ai_engine(provider: str = "mock") -> AIEngine:
    normalized = provider.strip().lower()
    if normalized in {"", "mock", "offline"}:
        return MockAIEngine()
    if normalized == "sarvam":
        api_key = os.getenv("SARVAM_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("SARVAM_API_KEY is required when AI_PROVIDER or --provider is 'sarvam'.")
        return SarvamAIEngine(api_key=api_key, model=os.getenv("SARVAM_MODEL", "sarvam-105b"))
    return DisabledExternalAI(normalized)


def dumps_pretty(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, sort_keys=True)
