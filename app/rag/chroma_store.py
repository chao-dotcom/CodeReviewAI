from __future__ import annotations

from typing import List

import chromadb

from app.rag.index import RagChunk


class ChromaStore:
    def __init__(self, path: str, collection_name: str) -> None:
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add_chunks(self, chunks: List[RagChunk], embeddings: List[list[float]]) -> None:
        self.collection.add(
            documents=[chunk.content for chunk in chunks],
            embeddings=embeddings,
            metadatas=[chunk.metadata for chunk in chunks],
            ids=[chunk.chunk_id for chunk in chunks],
        )

    def query(self, query_embedding: list[float], limit: int) -> List[RagChunk]:
        results = self.collection.query(query_embeddings=[query_embedding], n_results=limit)
        chunks: List[RagChunk] = []
        for index, chunk_id in enumerate(results.get("ids", [[]])[0]):
            content = results.get("documents", [[]])[0][index]
            metadata = results.get("metadatas", [[]])[0][index]
            chunks.append(RagChunk(chunk_id=chunk_id, content=content, metadata=metadata))
        return chunks
