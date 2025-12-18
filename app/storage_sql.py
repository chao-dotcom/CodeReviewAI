from __future__ import annotations

from datetime import datetime
from typing import List
from uuid import UUID, uuid4

from sqlalchemy import select

from app.db import build_engine, get_session, init_db
from app.db_models import CommentModel, FeedbackModel, ReviewModel, TraceModel
from app.models import AgentTrace, Comment, FeedbackEntry, ReviewResult, ReviewStatus


class SqlStore:
    def __init__(self, database_url: str) -> None:
        self.engine = build_engine(database_url)
        init_db(self.engine)

    def create_review(self, metadata: dict | None = None) -> ReviewStatus:
        now = datetime.utcnow()
        review_id = str(uuid4())
        review = ReviewModel(
            id=review_id,
            status="pending",
            created_at=now,
            updated_at=now,
            meta=metadata or {},
        )
        with get_session(self.engine) as session:
            session.add(review)
            session.commit()
            return ReviewStatus(
                id=UUID(review_id),
                status=review.status,
                created_at=review.created_at,
                updated_at=review.updated_at,
                metadata=review.meta or {},
            )

    def mark_in_progress(self, review_id: UUID) -> ReviewStatus:
        return self._update_status(review_id, "in_progress")

    def complete_review(self, review_id: UUID) -> ReviewStatus:
        return self._update_status(review_id, "completed")

    def mark_failed(self, review_id: UUID, reason: str) -> ReviewStatus:
        review = self._update_status(review_id, "failed")
        with get_session(self.engine) as session:
            row = session.get(ReviewModel, str(review_id))
            row.meta = {**(row.meta or {}), "error": reason}
            session.commit()
        review.metadata["error"] = reason
        return review

    def _update_status(self, review_id: UUID, status: str) -> ReviewStatus:
        with get_session(self.engine) as session:
            row = session.get(ReviewModel, str(review_id))
            row.status = status
            row.updated_at = datetime.utcnow()
            session.commit()
            return ReviewStatus(
                id=UUID(row.id),
                status=row.status,
                created_at=row.created_at,
                updated_at=row.updated_at,
                metadata=row.meta or {},
            )

    def add_comments(self, review_id: UUID, new_comments: List[Comment]) -> None:
        with get_session(self.engine) as session:
            for comment in new_comments:
                session.add(
                    CommentModel(
                        id=str(comment.id),
                        review_id=str(review_id),
                        agent_id=comment.agent_id,
                        file_path=comment.file_path,
                        line_number=comment.line_number,
                        severity=comment.severity,
                        content=comment.content,
                        meta=comment.metadata,
                    )
                )
            session.commit()

    def add_traces(self, review_id: UUID, new_traces: List[AgentTrace]) -> None:
        with get_session(self.engine) as session:
            for trace in new_traces:
                session.add(
                    TraceModel(
                        review_id=str(review_id),
                        agent_id=trace.agent_id,
                        started_at=trace.started_at,
                        completed_at=trace.completed_at,
                        input_summary=trace.input_summary,
                        output_summary=trace.output_summary,
                    )
                )
            session.commit()

    def get_result(self, review_id: UUID) -> ReviewResult:
        return ReviewResult(review=self.get_review(review_id), comments=self.get_comments(review_id))

    def get_review(self, review_id: UUID) -> ReviewStatus:
        with get_session(self.engine) as session:
            row = session.get(ReviewModel, str(review_id))
            return ReviewStatus(
                id=UUID(row.id),
                status=row.status,
                created_at=row.created_at,
                updated_at=row.updated_at,
                metadata=row.meta or {},
            )

    def list_reviews(self) -> List[ReviewStatus]:
        with get_session(self.engine) as session:
            rows = session.execute(select(ReviewModel)).scalars().all()
            return [
                ReviewStatus(
                    id=UUID(row.id),
                    status=row.status,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    metadata=row.meta or {},
                )
                for row in rows
            ]

    def add_feedback(self, entry: FeedbackEntry) -> None:
        with get_session(self.engine) as session:
            session.add(
                FeedbackModel(
                    id=str(entry.id),
                    review_id=str(entry.review_id),
                    comment_id=str(entry.comment_id),
                    rating=entry.rating,
                    user_id=entry.user_id,
                    created_at=entry.created_at,
                )
            )
            session.commit()

    def list_feedback(self, review_id: UUID) -> List[FeedbackEntry]:
        with get_session(self.engine) as session:
            rows = (
                session.execute(select(FeedbackModel).where(FeedbackModel.review_id == str(review_id)))
                .scalars()
                .all()
            )
            return [
                FeedbackEntry(
                    id=UUID(row.id),
                    review_id=UUID(row.review_id),
                    comment_id=UUID(row.comment_id),
                    rating=row.rating,
                    user_id=row.user_id,
                    created_at=row.created_at,
                )
                for row in rows
            ]

    def feedback_summary(self, review_id: UUID) -> dict:
        entries = self.list_feedback(review_id)
        summary = {"up": 0, "down": 0, "neutral": 0}
        for entry in entries:
            if entry.rating > 0:
                summary["up"] += 1
            elif entry.rating < 0:
                summary["down"] += 1
            else:
                summary["neutral"] += 1
        return summary

    def get_comments(self, review_id: UUID) -> List[Comment]:
        with get_session(self.engine) as session:
            rows = (
                session.execute(select(CommentModel).where(CommentModel.review_id == str(review_id)))
                .scalars()
                .all()
            )
            return [
                Comment(
                    id=UUID(row.id),
                    review_id=UUID(row.review_id),
                    agent_id=row.agent_id,
                    file_path=row.file_path,
                    line_number=row.line_number,
                    severity=row.severity,
                    content=row.content,
                    metadata=row.meta or {},
                )
                for row in rows
            ]

    def get_traces(self, review_id: UUID) -> List[AgentTrace]:
        with get_session(self.engine) as session:
            rows = (
                session.execute(select(TraceModel).where(TraceModel.review_id == str(review_id)))
                .scalars()
                .all()
            )
            return [
                AgentTrace(
                    agent_id=row.agent_id,
                    started_at=row.started_at,
                    completed_at=row.completed_at,
                    input_summary=row.input_summary,
                    output_summary=row.output_summary,
                )
                for row in rows
            ]

    def list_traces_by_agent(self, agent_id: str) -> List[AgentTrace]:
        with get_session(self.engine) as session:
            rows = (
                session.execute(select(TraceModel).where(TraceModel.agent_id == agent_id))
                .scalars()
                .all()
            )
            return [
                AgentTrace(
                    agent_id=row.agent_id,
                    started_at=row.started_at,
                    completed_at=row.completed_at,
                    input_summary=row.input_summary,
                    output_summary=row.output_summary,
                )
                for row in rows
            ]
