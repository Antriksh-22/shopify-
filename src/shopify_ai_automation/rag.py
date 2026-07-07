from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .models import KnowledgeSnippet

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> set[str]:
    return set(TOKEN_PATTERN.findall(text.lower()))


@dataclass(frozen=True)
class DocumentChunk:
    title: str
    text: str
    tokens: set[str]


class LocalKnowledgeBase:
    """Tiny lexical RAG index for policies, FAQs, and merchandising rules."""

    def __init__(self, chunks: list[DocumentChunk]) -> None:
        self._chunks = chunks

    @classmethod
    def from_markdown(cls, path: Path) -> "LocalKnowledgeBase":
        text = path.read_text(encoding="utf-8")
        chunks: list[DocumentChunk] = []
        current_title = "General"
        current_lines: list[str] = []

        def flush() -> None:
            body = "\n".join(line.strip() for line in current_lines).strip()
            if body:
                chunks.append(DocumentChunk(current_title, body, tokenize(body + " " + current_title)))

        for line in text.splitlines():
            if line.startswith("## "):
                flush()
                current_title = line.removeprefix("## ").strip()
                current_lines = []
            else:
                current_lines.append(line)
        flush()
        return cls(chunks)

    def search(self, query: str, limit: int = 3) -> list[KnowledgeSnippet]:
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scored: list[KnowledgeSnippet] = []
        for chunk in self._chunks:
            overlap = query_tokens & chunk.tokens
            if not overlap:
                continue
            score = len(overlap) / max(len(query_tokens), 1)
            scored.append(KnowledgeSnippet(chunk.title, chunk.text, round(score, 3)))

        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:limit]
