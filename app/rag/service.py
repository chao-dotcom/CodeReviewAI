from __future__ import annotations

from typing import Iterable, List

from app.config import settings
from app.rag.chroma_store import ChromaStore
from app.rag.embeddings import SentenceTransformerEmbedder
from app.rag.index import RagChunk, RagIndex


class RagService:
    def __init__(self) -> None:
        self.use_chroma = settings.use_chroma
        if self.use_chroma:
            self.embedder = SentenceTransformerEmbedder(settings.embedding_model)
            self.store = ChromaStore(settings.chroma_path, settings.chroma_collection)
        else:
            self.embedder = None
            self.store = RagIndex()

    def add_chunks(self, chunks: List[RagChunk]) -> None:
        if not chunks:
            return
        if self.use_chroma and self.embedder is not None:
            embeddings = self.embedder.embed([chunk.content for chunk in chunks])
            self.store.add_chunks(chunks, embeddings)
        else:
            self.store.add_chunks(chunks)

    def query(self, query_text: str, limit: int = 5) -> List[RagChunk]:
        if self.use_chroma and self.embedder is not None:
            embedding = self.embedder.embed([query_text])[0]
            return self.store.query(embedding, limit)
        return self.store.query(query_text, limit)

    def build_chunks(
        self, repo_path: str, include_globs: Iterable[str]
    ) -> List[RagChunk]:
        from app.rag.builder import build_chunks

        return build_chunks(repo_path, include_globs)
