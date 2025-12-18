from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Sequence, Tuple

from app.agents.base import AgentFinding, ReviewAgent
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
