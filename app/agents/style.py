from __future__ import annotations

from typing import List

from app.agents.base import AgentFinding, ReviewAgent
from app.pipeline.diff_parser import DiffChange


class StyleAgent(ReviewAgent):
    id = "style_reviewer"
    name = "Style Reviewer"
    description = "Checks conventions and formatting."

    def analyze(self, changes: List[DiffChange], context: str) -> List[AgentFinding]:
        if hasattr(self, "analyze_with_llm"):
            llm_findings = self.analyze_with_llm(
                "\n".join(change.content for change in changes),
                context,
                "style reviewer",
            )
            if llm_findings:
                return llm_findings
        findings: List[AgentFinding] = []
        for change in changes:
            if "\t" in change.content:
                findings.append(
                    AgentFinding(
                        file_path=change.file_path,
                        line_number=change.line_number,
                        severity="low",
                        category="style",
                        description="Tab character found in change.",
                        suggestion="Use spaces to match the project formatting.",
                    )
                )
            if len(change.content) > 120:
                findings.append(
                    AgentFinding(
                        file_path=change.file_path,
                        line_number=change.line_number,
                        severity="low",
                        category="style",
                        description="Line exceeds 120 characters.",
                        suggestion="Consider wrapping the line for readability.",
                    )
                )
        return findings
