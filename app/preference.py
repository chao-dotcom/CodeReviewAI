from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from app.agents.code_reviewer import CodeReviewerAgent
from app.agents.security import SecurityAgent
from app.agents.style import StyleAgent
from app.pipeline.diff_parser import parse_diff


@dataclass(frozen=True)
class ReviewCandidate:
    agent_id: str
    text: str
    score: int


def _severity_score(severity: str) -> int:
    return {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}.get(severity, 0)


def _render_findings(findings) -> str:
    lines = []
    for item in findings:
        lines.append(f"- [{item.severity}] {item.file_path}:{item.line_number or '?'} {item.description}")
    return "\n".join(lines)


def generate_preference_pairs(diff_text: str) -> List[Tuple[str, str]]:
    changes = parse_diff(diff_text)
    agents = [CodeReviewerAgent(), SecurityAgent(), StyleAgent()]
    candidates: List[ReviewCandidate] = []

    for agent in agents:
        findings = agent.analyze(changes, context="")
        if not findings:
            continue
        score = sum(_severity_score(item.severity) for item in findings)
        candidates.append(
            ReviewCandidate(agent_id=agent.id, text=_render_findings(findings), score=score)
        )

    if len(candidates) < 2:
        return []

    candidates.sort(key=lambda item: item.score, reverse=True)
    best = candidates[0]
    worst = candidates[-1]
    return [(best.text, worst.text)]


def generate_pairs_with_critic(diff_text: str) -> List[Tuple[str, str]]:
    changes = parse_diff(diff_text)
    agents = [CodeReviewerAgent(), SecurityAgent(), StyleAgent()]
    candidates: List[ReviewCandidate] = []
    for agent in agents:
        findings = agent.analyze(changes, context="")
        if not findings:
            continue
        candidates.append(
            ReviewCandidate(
                agent_id=agent.id,
                text=_render_findings(findings),
                score=sum(_severity_score(item.severity) for item in findings),
            )
        )
    if len(candidates) < 2:
        return []

    review_text = "\n".join(f"{c.agent_id}: {c.text}" for c in candidates)
    from app.llm import LLMClient, parse_findings, parse_json_block
    from app.prompts import critic_prompt

    client = LLMClient()
    output = client.generate(critic_prompt(diff_text, review_text))
    payload = parse_json_block(output) or {}
    preferred_agent = payload.get("preferred_agent")
    rejected_agent = payload.get("rejected_agent")
    if preferred_agent and rejected_agent:
        preferred = next((c for c in candidates if c.agent_id == preferred_agent), None)
        rejected = next((c for c in candidates if c.agent_id == rejected_agent), None)
        if preferred and rejected:
            return [(preferred.text, rejected.text)]
    findings = parse_findings(payload)
    if findings:
        candidates.sort(key=lambda item: item.score, reverse=True)
        return [(candidates[0].text, candidates[-1].text)]
    candidates.sort(key=lambda item: item.score, reverse=True)
    return [(candidates[0].text, candidates[-1].text)]
