from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ReviewRequest(BaseModel):
    diff: str = Field(..., description="Unified diff text for the PR.")
    repo: Optional[str] = Field(default=None, description="Repository name or URL.")
    commit: Optional[str] = Field(default=None, description="Commit or PR identifier.")


class ReviewStatus(BaseModel):
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Comment(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    review_id: UUID
    agent_id: str
    file_path: str
    line_number: Optional[int]
    severity: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReviewResult(BaseModel):
    review: ReviewStatus
    comments: List[Comment]


class FeedbackRequest(BaseModel):
    comment_id: UUID
    rating: int = Field(..., description="-1, 0, or 1")
    user_id: Optional[str] = None


class FeedbackEntry(BaseModel):
    id: UUID
    review_id: UUID
    comment_id: UUID
    rating: int
    user_id: Optional[str]
    created_at: datetime


class FeedbackSummary(BaseModel):
    review_id: UUID
    up: int
    down: int
    neutral: int


class PreferencePair(BaseModel):
    review_id: UUID
    prompt: str
    chosen: str
    rejected: str


class OAuthToken(BaseModel):
    provider: str
    user_id: str
    access_token: str
    created_at: datetime


class AgentMessage(BaseModel):
    agent_id: str
    message_type: str
    timestamp: datetime
    payload: Dict[str, Any]


class AgentInfo(BaseModel):
    id: str
    name: str
    description: str


class AgentTrace(BaseModel):
    agent_id: str
    started_at: datetime
    completed_at: datetime
    input_summary: str
    output_summary: str


class RagChunkRequest(BaseModel):
    chunk_id: str
    content: str
    metadata: Dict[str, str] = Field(default_factory=dict)


class RagIndexRequest(BaseModel):
    chunks: List[RagChunkRequest]


class RagSearchRequest(BaseModel):
    query: str
    limit: int = 5


class RagRepoIndexRequest(BaseModel):
    repo_path: str
    include_globs: List[str] = Field(default_factory=lambda: ["**/*.py"])
