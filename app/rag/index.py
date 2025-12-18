from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class RagChunk:
    chunk_id: str
    content: str
    metadata: Dict[str, str]


class RagIndex:
    def __init__(self) -> None:
        self._chunks: List[RagChunk] = []

    def add_chunks(self, chunks: List[RagChunk]) -> None:
        self._chunks.extend(chunks)

    def query(self, query_text: str, limit: int = 5) -> List[RagChunk]:
        if not self._chunks:
            return []
        query_tokens = {token.lower() for token in query_text.split() if token.strip()}
        scored: List[tuple[int, RagChunk]] = []
        for chunk in self._chunks:
            content_tokens = {token.lower() for token in chunk.content.split() if token.strip()}
            score = len(query_tokens.intersection(content_tokens))
            scored.append((score, chunk))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [chunk for score, chunk in scored[:limit] if score > 0]
