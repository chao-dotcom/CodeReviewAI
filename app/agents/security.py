from __future__ import annotations

from typing import List

from app.agents.base import AgentFinding, ReviewAgent
from app.pipeline.diff_parser import DiffChange


class SecurityAgent(ReviewAgent):
    id = "security_reviewer"
    name = "Security Reviewer"
    description = "Looks for security and safety issues."

    def analyze(self, changes: List[DiffChange], context: str) -> List[AgentFinding]:
        findings: List[AgentFinding] = []
        for change in changes:
            content_upper = change.content.upper()
            if "PASSWORD" in content_upper or "SECRET" in content_upper or "TOKEN" in content_upper:
                findings.append(
                    AgentFinding(
                        file_path=change.file_path,
                        line_number=change.line_number,
                        severity="high",
                        category="secrets",
                        description="Potential secret material introduced.",
                        suggestion="Move secrets to environment variables or a secret manager.",
                    )
                )
            if "EVAL(" in content_upper or "EXEC(" in content_upper:
                findings.append(
                    AgentFinding(
                        file_path=change.file_path,
                        line_number=change.line_number,
                        severity="high",
                        category="code_injection",
                        description="Dynamic code execution detected.",
                        suggestion="Avoid dynamic execution or sanitize input thoroughly.",
                    )
                )
        return findings
