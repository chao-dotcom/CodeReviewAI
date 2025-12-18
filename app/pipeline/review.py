from __future__ import annotations

from datetime import datetime
from typing import List, Tuple
from uuid import UUID

from app.agents.orchestrator import AgentOrchestrator
from app.config import settings
from app.models import AgentTrace, Comment
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


def run_review_pipeline(
    review_id: UUID, diff_text: str, rag_index: object | None = None
) -> Tuple[List[Comment], List[AgentTrace]]:
    if settings.use_langgraph:
        try:
            from app.orchestration.graph import run_graph

            return run_graph(diff_text, review_id)
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
    for agent_id, finding in result.findings:
        comments.append(
            Comment(
                review_id=review_id,
                agent_id=agent_id,
                file_path=finding.file_path,
                line_number=finding.line_number,
                severity=finding.severity,
                content=finding.description,
                metadata={"category": finding.category, "suggestion": finding.suggestion},
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

    return comments, result.traces
