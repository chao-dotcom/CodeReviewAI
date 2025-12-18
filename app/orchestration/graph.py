from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple
from uuid import UUID

try:
    from langgraph.graph import END, StateGraph
except Exception:  # pragma: no cover
    StateGraph = None
    END = None

from app.agents.orchestrator import AgentOrchestrator
from app.models import AgentTrace, Comment
from app.pipeline.diff_parser import parse_diff
from app.rag.service import RagService


@dataclass
class GraphState:
    review_id: UUID
    diff_text: str
    rag_context: str
    comments: List[Comment]
    traces: List[AgentTrace]


def build_graph() -> StateGraph:
    if StateGraph is None:
        raise RuntimeError("LangGraph not available")

    graph = StateGraph(GraphState)

    def parse_step(state: GraphState) -> GraphState:
        return state

    def rag_step(state: GraphState) -> GraphState:
        rag = RagService()
        retrieved = rag.query(state.diff_text, limit=5)
        state.rag_context = "\n".join(chunk.content for chunk in retrieved)
        return state

    def agent_step(state: GraphState) -> GraphState:
        orchestrator = AgentOrchestrator()
        changes = parse_diff(state.diff_text)
        result = orchestrator.run(changes, state.rag_context)
        state.traces.extend(result.traces)
        state.comments.extend(
            [
                Comment(
                    review_id=state.review_id,
                    agent_id=agent_id,
                    file_path=finding.file_path,
                    line_number=finding.line_number,
                    severity=finding.severity,
                    content=finding.description,
                    metadata={"category": finding.category, "suggestion": finding.suggestion},
                )
                for agent_id, finding in result.findings
            ]
        )
        return state

    graph.add_node("parse", parse_step)
    graph.add_node("rag", rag_step)
    graph.add_node("agent", agent_step)
    graph.add_edge("parse", "rag")
    graph.add_edge("rag", "agent")
    graph.add_edge("agent", END)
    graph.set_entry_point("parse")
    return graph


def run_graph(diff_text: str, review_id) -> Tuple[List[Comment], List[AgentTrace]]:
    if StateGraph is None:
        raise RuntimeError("LangGraph not available")
    state = GraphState(review_id=review_id, diff_text=diff_text, rag_context="", comments=[], traces=[])
    graph = build_graph()
    result = graph.compile().invoke(state)
    return result.comments, result.traces
