from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class CodeChunk:
    chunk_type: str
    name: str
    code: str
    start_line: int
    end_line: int
    docstring: Optional[str]


def chunk_python_code(code: str) -> List[CodeChunk]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    chunks: List[CodeChunk] = []
    lines = code.splitlines()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start_line = node.lineno
            end_line = getattr(node, "end_lineno", node.lineno)
            segment = "\n".join(lines[start_line - 1 : end_line])
            chunks.append(
                CodeChunk(
                    chunk_type="class" if isinstance(node, ast.ClassDef) else "function",
                    name=node.name,
                    code=segment,
                    start_line=start_line,
                    end_line=end_line,
                    docstring=ast.get_docstring(node),
                )
            )

    return chunks
