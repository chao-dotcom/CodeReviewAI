from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Sequence, Tuple

from app.agents.base import AgentFinding, ReviewAgent
from app.config import settings
from app.llm import LLMClient, parse_findings, parse_json_block
from app.prompts import base_prompt, critic_prompt
from app.agents.code_reviewer import CodeReviewerAgent
from app.agents.critic import CriticAgent
from app.agents.security import SecurityAgent
from app.agents.style import StyleAgent
from app.models import AgentTrace
from app.pipeline.diff_parser import DiffChange


@dataclass(frozen=True)
class OrchestratorResult:
    findings: List[Tuple[str, AgentFinding]]
    traces: List[AgentTrace]


class AgentOrchestrator:
    def __init__(self, agents: Sequence[ReviewAgent] | None = None) -> None:
        self.agents: List[ReviewAgent] = list(
            agents
            if agents is not None
            else [CodeReviewerAgent(), SecurityAgent(), StyleAgent(), CriticAgent()]
        )

    def run(self, changes: List[DiffChange], context: str) -> OrchestratorResult:
        findings: List[Tuple[str, AgentFinding]] = []
        traces: List[AgentTrace] = []

        if settings.llm_backend != "disabled" and changes:
            client = LLMClient()
            diff_text = "\n".join(change.content for change in changes)
            prompts = []
            agent_map: List[ReviewAgent] = []
            for agent in self.agents:
                if agent.id == "critic":
                    prompts.append(critic_prompt(diff_text, context))
                else:
                    prompts.append(base_prompt(agent.name, diff_text, context))
                agent_map.append(agent)

            outputs = client.batch_generate(prompts)
            for agent, output in zip(agent_map, outputs):
                start = datetime.utcnow()
                payload = parse_json_block(output) or {}
                parsed = parse_findings(payload)
                agent_findings = [
                    AgentFinding(
                        file_path=item.get("file_path", ""),
                        line_number=item.get("line_number"),
                        severity=item.get("severity", "low"),
                        category=item.get("category", "general"),
                        description=item.get("description", ""),
                        suggestion=item.get("suggestion", ""),
                    )
                    for item in parsed
                ]
                if not agent_findings:
                    agent_findings = agent.analyze(changes, context)
                end = datetime.utcnow()
                findings.extend([(agent.id, finding) for finding in agent_findings])
                traces.append(
                    AgentTrace(
                        agent_id=agent.id,
                        started_at=start,
                        completed_at=end,
                        input_summary=f"{len(changes)} diff changes",
                        output_summary=f"{len(agent_findings)} findings",
                    )
                )
        else:
            for agent in self.agents:
                start = datetime.utcnow()
                agent_findings = agent.analyze(changes, context)
                end = datetime.utcnow()
                findings.extend([(agent.id, finding) for finding in agent_findings])
                traces.append(
                    AgentTrace(
                        agent_id=agent.id,
                        started_at=start,
                        completed_at=end,
                        input_summary=f"{len(changes)} diff changes",
                        output_summary=f"{len(agent_findings)} findings",
                    )
                )

        return OrchestratorResult(findings=findings, traces=traces)
