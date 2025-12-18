from __future__ import annotations

from datetime import datetime
from typing import Dict, List
from uuid import UUID, uuid4

from app.crypto import TokenCipher
from app.models import AgentMessage, AgentTrace, Comment, FeedbackEntry, OAuthToken, ReviewResult, ReviewStatus


class InMemoryStore:
    def __init__(self) -> None:
        self.reviews: Dict[UUID, ReviewStatus] = {}
        self.comments: Dict[UUID, List[Comment]] = {}
        self.traces: Dict[UUID, List[AgentTrace]] = {}
        self.messages: Dict[UUID, List[AgentMessage]] = {}
        self.feedback: Dict[UUID, List[FeedbackEntry]] = {}
        self.tokens: List[OAuthToken] = []
        self._cipher = TokenCipher()

    def create_review(self, metadata: dict | None = None) -> ReviewStatus:
        now = datetime.utcnow()
        review = ReviewStatus(
            id=uuid4(),
            status="pending",
            created_at=now,
            updated_at=now,
            metadata=metadata or {},
        )
        self.reviews[review.id] = review
        self.comments[review.id] = []
        self.traces[review.id] = []
        self.messages[review.id] = []
        self.feedback[review.id] = []
        return review

    def complete_review(self, review_id: UUID) -> ReviewStatus:
        review = self.reviews[review_id]
        review.status = "completed"
        review.updated_at = datetime.utcnow()
        self.reviews[review_id] = review
        return review

    def mark_in_progress(self, review_id: UUID) -> ReviewStatus:
        review = self.reviews[review_id]
        review.status = "in_progress"
        review.updated_at = datetime.utcnow()
        self.reviews[review_id] = review
        return review

    def mark_failed(self, review_id: UUID, reason: str) -> ReviewStatus:
        review = self.reviews[review_id]
        review.status = "failed"
        review.updated_at = datetime.utcnow()
        review.metadata["error"] = reason
        self.reviews[review_id] = review
        return review

    def add_comments(self, review_id: UUID, new_comments: List[Comment]) -> None:
        self.comments.setdefault(review_id, [])
        self.comments[review_id].extend(new_comments)

    def add_traces(self, review_id: UUID, new_traces: List[AgentTrace]) -> None:
        self.traces.setdefault(review_id, [])
        self.traces[review_id].extend(new_traces)

    def add_messages(self, review_id: UUID, new_messages: List[AgentMessage]) -> None:
        self.messages.setdefault(review_id, [])
        self.messages[review_id].extend(new_messages)

    def get_result(self, review_id: UUID) -> ReviewResult:
        return ReviewResult(
            review=self.reviews[review_id],
            comments=self.comments.get(review_id, []),
        )

    def get_review(self, review_id: UUID) -> ReviewStatus:
        return self.reviews[review_id]

    def list_reviews(self) -> List[ReviewStatus]:
        return list(self.reviews.values())

    def add_feedback(self, entry: FeedbackEntry) -> None:
        self.feedback.setdefault(entry.review_id, [])
        self.feedback[entry.review_id].append(entry)

    def list_feedback(self, review_id: UUID) -> List[FeedbackEntry]:
        return self.feedback.get(review_id, [])

    def feedback_summary(self, review_id: UUID) -> dict:
        entries = self.feedback.get(review_id, [])
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
        return self.comments.get(review_id, [])

    def get_traces(self, review_id: UUID) -> List[AgentTrace]:
        return self.traces.get(review_id, [])

    def get_messages(self, review_id: UUID) -> List[AgentMessage]:
        return self.messages.get(review_id, [])

    def list_traces_by_agent(self, agent_id: str) -> List[AgentTrace]:
        traces: List[AgentTrace] = []
        for review_traces in self.traces.values():
            traces.extend([trace for trace in review_traces if trace.agent_id == agent_id])
        return traces

    def list_messages_by_agent(self, agent_id: str) -> List[AgentMessage]:
        messages: List[AgentMessage] = []
        for review_messages in self.messages.values():
            messages.extend([msg for msg in review_messages if msg.agent_id == agent_id])
        return messages

    def add_oauth_token(self, token: OAuthToken) -> None:
        encrypted = OAuthToken(
            provider=token.provider,
            user_id=token.user_id,
            access_token=self._cipher.encrypt(token.access_token),
            created_at=token.created_at,
        )
        self.tokens.append(encrypted)

    def list_oauth_tokens(self, provider: str, user_id: str) -> List[OAuthToken]:
        result = []
        for token in self.tokens:
            if token.provider != provider or token.user_id != user_id:
                continue
            result.append(
                OAuthToken(
                    provider=token.provider,
                    user_id=token.user_id,
                    access_token=self._cipher.decrypt(token.access_token),
                    created_at=token.created_at,
                )
            )
        return result
