from __future__ import annotations

from typing import List

from app.agents.base import AgentFinding, ReviewAgent
from app.pipeline.diff_parser import DiffChange
from app.prompts import critic_prompt
from app.llm import LLMClient, parse_findings, parse_json_block


class CriticAgent(ReviewAgent):
    id = "critic"
    name = "Critic"
    description = "Ranks feedback for preference learning."

    def analyze(self, changes: List[DiffChange], context: str) -> List[AgentFinding]:
        if not changes:
            return []
        if context:
            client = LLMClient()
            prompt = critic_prompt("\n".join(change.content for change in changes), context)
            output = client.generate(prompt)
            payload = parse_json_block(output)
            if payload:
                findings = []
                for item in parse_findings(payload):
                    findings.append(
                        AgentFinding(
                            file_path=item.get("file_path", ""),
                            line_number=item.get("line_number"),
                            severity=item.get("severity", "info"),
                            category=item.get("category", "preference"),
                            description=item.get("description", ""),
                            suggestion=item.get("suggestion", ""),
                        )
                    )
                if findings:
                    return findings
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
