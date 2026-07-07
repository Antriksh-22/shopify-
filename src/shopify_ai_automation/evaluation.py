from __future__ import annotations

from dataclasses import dataclass

from .models import AutomationAction, AutomationResult


@dataclass(frozen=True)
class QualityScore:
    provider: str
    score: int
    action_count: int
    support_specificity: int
    evidence_count: int
    has_actionable_support_reply: bool

    def to_dict(self) -> dict[str, int | str | bool]:
        return {
            "provider": self.provider,
            "score": self.score,
            "action_count": self.action_count,
            "support_specificity": self.support_specificity,
            "evidence_count": self.evidence_count,
            "has_actionable_support_reply": self.has_actionable_support_reply,
        }


def score_result(provider: str, result: AutomationResult) -> QualityScore:
    support_actions = [action for action in result.actions if action.action_type == "draft_reply"]
    support_specificity = max((score_support_action(action) for action in support_actions), default=0)
    evidence_count = sum(len(action.evidence) for action in result.actions)
    has_actionable_support_reply = support_specificity >= 4
    score = (
        len(result.actions) * 2
        + min(evidence_count, 8)
        + support_specificity * 2
        + (4 if has_actionable_support_reply else 0)
    )
    return QualityScore(
        provider=provider,
        score=score,
        action_count=len(result.actions),
        support_specificity=support_specificity,
        evidence_count=evidence_count,
        has_actionable_support_reply=has_actionable_support_reply,
    )


def score_support_action(action: AutomationAction) -> int:
    body = action.body.lower()
    checks = [
        "riya" in body,
        "damaged" in body,
        "photo" in body or "evidence" in body,
        "refund" in body or "replacement" in body,
        "order" in body,
        "next" in body or "step" in body,
    ]
    return sum(1 for check in checks if check)
