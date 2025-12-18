from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from app.pipeline.diff_parser import DiffChange


@dataclass(frozen=True)
class AgentFinding:
    file_path: str
    line_number: Optional[int]
    severity: str
    category: str
    description: str
    suggestion: str


class ReviewAgent:
    id: str
    name: str
    description: str

    def analyze(self, changes: List[DiffChange], context: str) -> List[AgentFinding]:
        raise NotImplementedError
