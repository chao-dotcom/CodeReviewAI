from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from app.pipeline.chunker import chunk_python_code
from app.rag.index import RagChunk


def _iter_files(root: Path, patterns: Iterable[str]) -> List[Path]:
    files: List[Path] = []
    for pattern in patterns:
        files.extend(root.glob(pattern))
    return [path for path in files if path.is_file()]


def build_chunks(repo_path: str, include_globs: Iterable[str]) -> List[RagChunk]:
    root = Path(repo_path).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Repo path not found: {root}")

    files = _iter_files(root, include_globs)
    chunks: List[RagChunk] = []
    for file_path in files:
        code = file_path.read_text(encoding="utf-8", errors="ignore")
        for chunk in chunk_python_code(code):
            chunk_id = f"{file_path}:{chunk.start_line}:{chunk.end_line}:{chunk.name}"
            chunks.append(
                RagChunk(
                    chunk_id=chunk_id,
                    content=chunk.code,
                    metadata={
                        "file": str(file_path.relative_to(root)),
                        "name": chunk.name,
                        "type": chunk.chunk_type,
                    },
                )
            )

    return chunks
