from __future__ import annotations

from typing import List

from app.agents.base import AgentFinding, ReviewAgent
from app.pipeline.diff_parser import DiffChange


class CodeReviewerAgent(ReviewAgent):
    id = "code_reviewer"
    name = "Code Reviewer"
    description = "High-level review for logic and maintainability."

    def analyze(self, changes: List[DiffChange], context: str) -> List[AgentFinding]:
        if hasattr(self, "analyze_with_llm"):
            llm_findings = self.analyze_with_llm(
                "\n".join(change.content for change in changes),
                context,
                "code reviewer",
            )
            if llm_findings:
                return llm_findings
        findings: List[AgentFinding] = []
        for change in changes:
            content = change.content.strip()
            if "TODO" in content or "FIXME" in content:
                findings.append(
                    AgentFinding(
                        file_path=change.file_path,
                        line_number=change.line_number,
                        severity="medium",
                        category="maintainability",
                        description="TODO/FIXME left in changed code.",
                        suggestion="Resolve the TODO or add a follow-up issue link.",
                    )
                )
            elif "print(" in content or "console.log" in content:
                findings.append(
                    AgentFinding(
                        file_path=change.file_path,
                        line_number=change.line_number,
                        severity="low",
                        category="logging",
                        description="Debug output introduced in diff.",
                        suggestion="Remove debug logging or gate it behind a flag.",
                    )
                )
        return findings
