from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple
from uuid import UUID

from app.agents.orchestrator import AgentOrchestrator
from app.config import settings
from app.models import AgentMessage, AgentTrace, Comment
from app.pipeline.diff_parser import parse_diff
from app.rag.index import RagChunk


AGENTS = [
    {
        "id": "code_reviewer",
        "name": "Code Reviewer",
        "description": "High-level review for logic and maintainability.",
    },
    {
        "id": "security_reviewer",
        "name": "Security Reviewer",
        "description": "Looks for security and safety issues.",
    },
    {
        "id": "style_reviewer",
        "name": "Style Reviewer",
        "description": "Checks conventions and formatting.",
    },
    {
        "id": "critic",
        "name": "Critic",
        "description": "Ranks feedback for preference learning.",
    },
]


def _aggregate_findings(
    findings: List[Tuple[str, object]]
) -> List[Tuple[str, object, List[str]]]:
    grouped: Dict[Tuple[str, int | None, str], dict] = defaultdict(dict)
    for agent_id, finding in findings:
        key = (finding.file_path, finding.line_number, finding.description)
        if key not in grouped:
            grouped[key] = {"finding": finding, "agents": [agent_id]}
        else:
            grouped[key]["agents"].append(agent_id)
            existing = grouped[key]["finding"]
            severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
            if severity_order.get(finding.severity, 0) > severity_order.get(
                existing.severity, 0
            ):
                grouped[key]["finding"] = finding
    return [(group["agents"][0], group["finding"], group["agents"]) for group in grouped.values()]


def run_review_pipeline(
    review_id: UUID, diff_text: str, rag_index: object | None = None
) -> Tuple[List[Comment], List[AgentTrace], List[AgentMessage]]:
    if settings.use_langgraph:
        try:
            from app.orchestration.graph import run_graph

            comments, traces, messages = run_graph(diff_text, review_id)
            return comments, traces, messages
        except Exception:
            pass
    changes = parse_diff(diff_text)
    orchestrator = AgentOrchestrator()
    rag_context = ""
    if rag_index is not None:
        retrieved = rag_index.query(diff_text, limit=5)
        if isinstance(retrieved, list) and retrieved and isinstance(retrieved[0], RagChunk):
            rag_context = "\n".join(chunk.content for chunk in retrieved)

    result = orchestrator.run(changes, rag_context)
    comments: List[Comment] = []
    messages: List[AgentMessage] = []
    aggregated = _aggregate_findings(result.findings)
    for agent_id, finding, agents in aggregated:
        comments.append(
            Comment(
                review_id=review_id,
                agent_id=agent_id,
                file_path=finding.file_path,
                line_number=finding.line_number,
                severity=finding.severity,
                content=finding.description,
                metadata={
                    "category": finding.category,
                    "suggestion": finding.suggestion,
                    "agents": agents,
                },
            )
        )

    if not result.traces:
        result.traces.append(
            AgentTrace(
                agent_id="orchestrator",
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                input_summary=f"{len(changes)} diff changes parsed",
                output_summary=f"{len(comments)} comments generated",
            )
        )

    for trace in result.traces:
        messages.append(
            AgentMessage(
                agent_id=trace.agent_id,
                message_type="trace",
                timestamp=datetime.utcnow(),
                payload={
                    "input": trace.input_summary,
                    "output": trace.output_summary,
                },
            )
        )

    return comments, result.traces, messages
