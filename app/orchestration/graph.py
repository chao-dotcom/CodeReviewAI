from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple
from uuid import UUID

try:
    from langgraph.graph import END, StateGraph
except Exception:  # pragma: no cover
    StateGraph = None
    END = None

from app.agents.orchestrator import AgentOrchestrator
from app.llm import LLMClient, parse_findings, parse_json_block
from app.prompts import critic_prompt
from app.models import AgentMessage, AgentTrace, Comment
from app.pipeline.diff_parser import parse_diff
from app.rag.service import RagService


@dataclass
class GraphState:
    review_id: UUID
    diff_text: str
    rag_context: str
    comments: List[Comment]
    traces: List[AgentTrace]
    messages: List[AgentMessage]


def build_graph() -> StateGraph:
    if StateGraph is None:
        raise RuntimeError("LangGraph not available")

    graph = StateGraph(GraphState)

    def parse_step(state: GraphState) -> GraphState:
        state.messages.append(
            AgentMessage(
                agent_id="parser",
                message_type="parsed",
                timestamp=datetime.utcnow(),
                payload={"diff_len": len(state.diff_text)},
            )
        )
        return state

    def rag_step(state: GraphState) -> GraphState:
        rag = RagService()
        retrieved = rag.query(state.diff_text, limit=5)
        state.rag_context = "\n".join(chunk.content for chunk in retrieved)
        state.messages.append(
            AgentMessage(
                agent_id="rag",
                message_type="context",
                timestamp=datetime.utcnow(),
                payload={"chunks": len(retrieved)},
            )
        )
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
        state.messages.append(
            AgentMessage(
                agent_id="orchestrator",
                message_type="result",
                timestamp=datetime.utcnow(),
                payload={"findings": len(result.findings)},
            )
        )
        return state

    def critic_step(state: GraphState) -> GraphState:
        if not state.comments:
            return state
        review_text = "\n".join(
            f"- [{comment.severity}] {comment.file_path}:{comment.line_number or '?'} {comment.content}"
            for comment in state.comments
        )
        client = LLMClient()
        prompt = critic_prompt(state.diff_text, review_text)
        output = client.generate(prompt)
        payload = parse_json_block(output) or {}
        preferred_agent = payload.get("preferred_agent")
        rejected_agent = payload.get("rejected_agent")
        if preferred_agent or rejected_agent:
            state.messages.append(
                AgentMessage(
                    agent_id="critic",
                    message_type="preference",
                    timestamp=datetime.utcnow(),
                    payload={
                        "preferred_agent": preferred_agent,
                        "rejected_agent": rejected_agent,
                        "notes": payload.get("notes", ""),
                    },
                )
            )
        findings = parse_findings(payload)
        for item in findings:
            state.messages.append(
                AgentMessage(
                    agent_id="critic",
                    message_type="ranking",
                    timestamp=datetime.utcnow(),
                    payload=item,
                )
            )
        return state

    def aggregate_step(state: GraphState) -> GraphState:
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
        state.comments.sort(
            key=lambda comment: severity_order.get(comment.severity, 0), reverse=True
        )
        state.messages.append(
            AgentMessage(
                agent_id="aggregator",
                message_type="sorted",
                timestamp=datetime.utcnow(),
                payload={"total": len(state.comments)},
            )
        )
        return state

    graph.add_node("parse", parse_step)
    graph.add_node("rag", rag_step)
    graph.add_node("agent", agent_step)
    graph.add_edge("parse", "rag")
    graph.add_edge("rag", "agent")
    graph.add_node("critic", critic_step)
    graph.add_node("aggregate", aggregate_step)
    graph.add_edge("agent", "critic")
    graph.add_edge("critic", "aggregate")
    graph.add_edge("aggregate", END)
    graph.set_entry_point("parse")
    return graph


def run_graph(diff_text: str, review_id) -> Tuple[List[Comment], List[AgentTrace], List[AgentMessage]]:
    if StateGraph is None:
        raise RuntimeError("LangGraph not available")
    state = GraphState(
        review_id=review_id,
        diff_text=diff_text,
        rag_context="",
        comments=[],
        traces=[],
        messages=[],
    )
    graph = build_graph()
    result = graph.compile().invoke(state)
    return result.comments, result.traces, result.messages
