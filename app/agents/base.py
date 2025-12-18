from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from app.pipeline.diff_parser import DiffChange
from app.llm import LLMClient, parse_findings, parse_json_block
from app.prompts import base_prompt


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

    def analyze_with_llm(self, diff_text: str, context: str, role: str) -> List[AgentFinding]:
        client = LLMClient()
        prompt = base_prompt(role, diff_text, context)
        output = client.generate(prompt)
        payload = parse_json_block(output)
        if not payload:
            return []
        findings = []
        for item in parse_findings(payload):
            findings.append(
                AgentFinding(
                    file_path=item.get("file_path", ""),
                    line_number=item.get("line_number"),
                    severity=item.get("severity", "low"),
                    category=item.get("category", "general"),
                    description=item.get("description", ""),
                    suggestion=item.get("suggestion", ""),
                )
            )
        return findings
