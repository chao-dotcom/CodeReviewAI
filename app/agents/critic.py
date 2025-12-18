from __future__ import annotations

from typing import List

from app.agents.base import AgentFinding, ReviewAgent
from app.pipeline.diff_parser import DiffChange


class CriticAgent(ReviewAgent):
    id = "critic"
    name = "Critic"
    description = "Ranks feedback for preference learning."

    def analyze(self, changes: List[DiffChange], context: str) -> List[AgentFinding]:
        if not changes:
            return []
        return [
            AgentFinding(
                file_path=changes[0].file_path,
                line_number=changes[0].line_number,
                severity="info",
                category="preference",
                description="Generated placeholder preference record for DPO.",
                suggestion="Use human feedback to create preferred/rejected pairs.",
            )
        ]
