from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

import logging
from time import perf_counter

import requests
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    AgentInfo,
    AgentMessage,
    AgentTrace,
    Comment,
    FeedbackEntry,
    FeedbackSummary,
    FeedbackRequest,
    OAuthToken,
    PreferencePair,
    RagIndexRequest,
    RagRepoIndexRequest,
    RagSearchRequest,
    RagUpdateRequest,
    ReviewRequest,
    ReviewResult,
    ReviewStatus,
)
from app.preference import generate_preference_pairs
from app.auth import require_api_key
from app.config import settings
from app.pipeline.review import AGENTS, run_review_pipeline
from app.queue import ReviewJob, ReviewQueue
from app.rag.index import RagChunk
from app.rag.service import RagService
from app.rag.builder import build_chunks
from app.storage import InMemoryStore
from app.storage_sql import SqlStore
from app.integrations.github import build_summary, create_check_run, post_pr_comment, post_review_comments
from app.integrations.gitlab import post_mr_comment, post_mr_inline_comments, set_commit_status
from app.webhook_handlers import handle_github_webhook, handle_gitlab_webhook
from app.rate_limit import RateLimiter
from app.sessions import SessionStore
from app.webhooks import verify_github_signature, verify_gitlab_token


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("codereview")

app = FastAPI(title="Agentic Code Review API", version="0.1.0")
store = SqlStore(settings.database_url) if settings.use_database else InMemoryStore()
rate_limiter = RateLimiter(settings.rate_limit_per_hour) if settings.rate_limit_per_hour > 0 else None
sessions = SessionStore(settings.session_ttl_hours)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    if rate_limiter is not None:
        key = request.headers.get("x-api-key") or request.client.host or "anonymous"
        if not rate_limiter.allow(key):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
    start = perf_counter()
    response = await call_next(request)
    duration_ms = int((perf_counter() - start) * 1000)
    logger.info("%s %s %s %sms", request.method, request.url.path, response.status_code, duration_ms)
    return response


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


@app.on_event("startup")
async def start_workers() -> None:
    app.state.queue = ReviewQueue()
    app.state.rag_index = RagService()

    if not settings.use_celery:
        async def handle_job(job: ReviewJob) -> None:
            store.mark_in_progress(job.review_id)
            try:
                comments, traces, messages = run_review_pipeline(
                    job.review_id, job.diff_text, rag_index=app.state.rag_index
                )
                store.add_comments(job.review_id, comments)
                store.add_traces(job.review_id, traces)
                store.add_messages(job.review_id, messages)
                store.complete_review(job.review_id)
                review = store.get_review(job.review_id)
                pr_url = review.metadata.get("pr_url")
                if pr_url and settings.github_token:
                    commit_id = review.metadata.get("commit_id")
                    post_pr_comment(pr_url, build_summary(comments), settings.github_token)
                    post_review_comments(
                        pr_url,
                        "Inline review comments",
                        comments,
                        settings.github_token,
                        commit_id=commit_id,
                    )
                    if commit_id:
                        create_check_run(
                            pr_url,
                            commit_id,
                            "AI Code Review",
                            build_summary(comments),
                            settings.github_token,
                        )
                if pr_url and settings.gitlab_token:
                    commit_id = review.metadata.get("commit_id")
                    post_mr_comment(pr_url, build_summary(comments), settings.gitlab_token)
                    post_mr_inline_comments(pr_url, comments, settings.gitlab_token, commit_id=commit_id)
                    if commit_id:
                        set_commit_status(
                            pr_url,
                            commit_id,
                            "success",
                            "AI review completed",
                            settings.gitlab_token,
                        )
            except Exception as exc:
                store.mark_failed(job.review_id, str(exc))

        await app.state.queue.start(handle_job)


async def enqueue_review(diff_text: str, metadata: dict) -> UUID:
    review = store.create_review(metadata=metadata)
    if settings.use_celery:
        from app.tasks import process_review

        process_review.delay(str(review.id), diff_text)
    else:
        await app.state.queue.enqueue(ReviewJob(review_id=review.id, diff_text=diff_text))
    return review.id


@app.post("/api/reviews", response_model=ReviewResult)
async def create_review(request: ReviewRequest) -> ReviewResult:
    metadata = {"repo": request.repo, "commit": request.commit, "diff": request.diff}
    review_id = await enqueue_review(request.diff, metadata)
    return store.get_result(review_id)


@app.get("/api/reviews/{review_id}", response_model=ReviewStatus)
def get_review_status(review_id: UUID) -> ReviewStatus:
    try:
        return store.get_review(review_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Review not found")


@app.get("/api/reviews", response_model=list[ReviewStatus])
def list_reviews() -> list[ReviewStatus]:
    return store.list_reviews()


@app.get("/api/reviews/{review_id}/comments", response_model=list[Comment])
def get_review_comments(review_id: UUID) -> list[Comment]:
    try:
        return store.get_comments(review_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Review not found")


@app.get("/api/reviews/{review_id}/messages", response_model=list[AgentMessage])
def get_review_messages(review_id: UUID) -> list[AgentMessage]:
    try:
        return store.get_messages(review_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Review not found")


@app.post("/api/reviews/{review_id}/feedback")
def submit_feedback(review_id: UUID, feedback: FeedbackRequest) -> dict:
    try:
        store.get_review(review_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Review not found")
    entry = FeedbackEntry(
        id=uuid4(),
        review_id=review_id,
        comment_id=feedback.comment_id,
        rating=feedback.rating,
        user_id=feedback.user_id,
        created_at=datetime.utcnow(),
    )
    store.add_feedback(entry)
    return {"status": "received", "comment_id": str(feedback.comment_id), "rating": feedback.rating}


@app.get("/api/reviews/{review_id}/feedback", response_model=list[FeedbackEntry])
def list_feedback(review_id: UUID) -> list[FeedbackEntry]:
    try:
        store.get_review(review_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Review not found")
    return store.list_feedback(review_id)


@app.get("/api/reviews/{review_id}/feedback/summary", response_model=FeedbackSummary)
def feedback_summary(review_id: UUID) -> FeedbackSummary:
    try:
        store.get_review(review_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Review not found")
    summary = store.feedback_summary(review_id)
    return FeedbackSummary(review_id=review_id, **summary)


def _build_preferences(review_id: UUID, limit: int) -> list[PreferencePair]:
    feedback = store.list_feedback(review_id)
    if not feedback:
        return []

    latest_by_comment: dict[UUID, FeedbackEntry] = {}
    for entry in sorted(feedback, key=lambda item: item.created_at):
        latest_by_comment[entry.comment_id] = entry

    comments_by_id = {comment.id: comment for comment in store.get_comments(review_id)}
    positive = [comments_by_id[cid] for cid, entry in latest_by_comment.items() if entry.rating > 0 and cid in comments_by_id]
    negative = [comments_by_id[cid] for cid, entry in latest_by_comment.items() if entry.rating < 0 and cid in comments_by_id]

    if not positive or not negative:
        return []

    diff_text = store.get_review(review_id).metadata.get("diff", "")
    prompt = f"Review this code diff:\n\n{diff_text}".strip()

    pairs: list[PreferencePair] = []
    for pos in positive:
        for neg in negative:
            pairs.append(
                PreferencePair(
                    review_id=review_id,
                    prompt=prompt,
                    chosen=pos.content,
                    rejected=neg.content,
                )
            )
            if len(pairs) >= limit:
                return pairs

    return pairs


@app.get("/api/reviews/{review_id}/preferences", response_model=list[PreferencePair])
def export_preferences(review_id: UUID, limit: int = 20) -> list[PreferencePair]:
    try:
        store.get_review(review_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Review not found")
    return _build_preferences(review_id, limit)


@app.get("/api/reviews/{review_id}/preferences/auto", response_model=list[PreferencePair])
def export_auto_preferences(review_id: UUID) -> list[PreferencePair]:
    try:
        review = store.get_review(review_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Review not found")
    diff_text = review.metadata.get("diff", "")
    pairs = generate_preference_pairs(diff_text)
    prompt = f"Review this code diff:\n\n{diff_text}".strip()
    return [
        PreferencePair(
            review_id=review_id,
            prompt=prompt,
            chosen=chosen,
            rejected=rejected,
        )
        for chosen, rejected in pairs
    ]


@app.get("/api/preferences/auto", response_model=list[PreferencePair])
def export_all_auto_preferences(limit: int = 200) -> list[PreferencePair]:
    pairs: list[PreferencePair] = []
    for review in store.list_reviews():
        diff_text = review.metadata.get("diff", "")
        prompt = f"Review this code diff:\n\n{diff_text}".strip()
        for chosen, rejected in generate_preference_pairs(diff_text):
            pairs.append(
                PreferencePair(
                    review_id=review.id,
                    prompt=prompt,
                    chosen=chosen,
                    rejected=rejected,
                )
            )
            if len(pairs) >= limit:
                return pairs
    return pairs


@app.get("/api/preferences", response_model=list[PreferencePair])
def export_all_preferences(limit: int = 200) -> list[PreferencePair]:
    pairs: list[PreferencePair] = []
    for review in store.list_reviews():
        pairs.extend(_build_preferences(review.id, limit))
        if len(pairs) >= limit:
            return pairs[:limit]
    return pairs


@app.delete("/api/reset")
def reset_store(_user: str = Depends(require_api_key)) -> dict:
    if isinstance(store, InMemoryStore):
        store.reviews.clear()
        store.comments.clear()
        store.traces.clear()
        store.messages.clear()
        store.feedback.clear()
        app.state.rag_index = RagService()
        return {"status": "reset"}
    raise HTTPException(status_code=400, detail="Reset only supported for in-memory store")


@app.get("/api/agents", response_model=list[AgentInfo])
def list_agents() -> list[AgentInfo]:
    return [AgentInfo(**agent) for agent in AGENTS]


@app.get("/api/auth/tokens")
def list_oauth_tokens(provider: str, user_id: str) -> list[OAuthToken]:
    return store.list_oauth_tokens(provider, user_id)


@app.get("/api/agents/{agent_id}/trace", response_model=list[AgentTrace])
def get_agent_trace(agent_id: str) -> list[AgentTrace]:
    return store.list_traces_by_agent(agent_id)


@app.get("/api/agents/{agent_id}/messages", response_model=list[AgentMessage])
def get_agent_messages(agent_id: str) -> list[AgentMessage]:
    return store.list_messages_by_agent(agent_id)


@app.post("/api/rag/index")
def index_rag(request: RagIndexRequest) -> dict:
    chunks = [RagChunk(chunk_id=chunk.chunk_id, content=chunk.content, metadata=chunk.metadata) for chunk in request.chunks]
    app.state.rag_index.add_chunks(chunks)
    return {"status": "indexed", "count": len(chunks)}


@app.post("/api/rag/index/repo")
def index_rag_repo(request: RagRepoIndexRequest) -> dict:
    try:
        chunks = build_chunks(request.repo_path, request.include_globs)
        app.state.rag_index.add_chunks(chunks)
        count = len(chunks)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": "indexed", "count": count}


@app.post("/api/rag/search")
def search_rag(request: RagSearchRequest) -> list[dict]:
    results = app.state.rag_index.query(request.query, limit=request.limit)
    return [{"chunk_id": chunk.chunk_id, "content": chunk.content, "metadata": chunk.metadata} for chunk in results]


@app.post("/api/rag/update")
def update_rag(request: RagUpdateRequest) -> dict:
    try:
        count = app.state.rag_index.update_files(request.repo_path, request.files)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": "updated", "count": count}


@app.get("/api/auth/github/login")
def github_login() -> dict:
    params = {
        "client_id": settings.github_client_id,
        "redirect_uri": settings.github_redirect_uri,
        "scope": "repo",
        "state": "demo_state",
    }
    query = "&".join(f"{key}={value}" for key, value in params.items() if value)
    return {"url": f"https://github.com/login/oauth/authorize?{query}", "state": "demo_state"}


@app.get("/api/auth/github/callback")
def github_callback(code: str, state: str) -> dict:
    if not settings.github_client_id or not settings.github_client_secret:
        raise HTTPException(status_code=400, detail="GitHub OAuth not configured")
    token_response = requests.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "client_id": settings.github_client_id,
            "client_secret": settings.github_client_secret,
            "code": code,
            "redirect_uri": settings.github_redirect_uri,
            "state": state,
        },
        timeout=15,
    )
    token_response.raise_for_status()
    token_payload = token_response.json()
    access_token = token_payload.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Failed to exchange token")

    user_response = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    user_response.raise_for_status()
    user = user_response.json()
    store.add_oauth_token(
        OAuthToken(
            provider="github",
            user_id=str(user.get("id")),
            access_token=access_token,
            created_at=datetime.utcnow(),
        )
    )
    session_token = sessions.create(str(user.get("id")), "github")
    return {
        "status": "connected",
        "user": {"id": user.get("id"), "login": user.get("login")},
        "session_token": session_token,
    }


@app.get("/api/auth/gitlab/login")
def gitlab_login() -> dict:
    params = {
        "client_id": settings.gitlab_client_id,
        "redirect_uri": settings.gitlab_redirect_uri,
        "response_type": "code",
        "scope": "read_api",
        "state": "demo_state",
    }
    query = "&".join(f"{key}={value}" for key, value in params.items() if value)
    return {"url": f"https://gitlab.com/oauth/authorize?{query}", "state": "demo_state"}


@app.get("/api/auth/gitlab/callback")
def gitlab_callback(code: str, state: str) -> dict:
    if not settings.gitlab_client_id or not settings.gitlab_client_secret:
        raise HTTPException(status_code=400, detail="GitLab OAuth not configured")
    token_response = requests.post(
        "https://gitlab.com/oauth/token",
        data={
            "client_id": settings.gitlab_client_id,
            "client_secret": settings.gitlab_client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.gitlab_redirect_uri,
        },
        timeout=15,
    )
    token_response.raise_for_status()
    token_payload = token_response.json()
    access_token = token_payload.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Failed to exchange token")

    user_response = requests.get(
        "https://gitlab.com/api/v4/user",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    user_response.raise_for_status()
    user = user_response.json()
    store.add_oauth_token(
        OAuthToken(
            provider="gitlab",
            user_id=str(user.get("id")),
            access_token=access_token,
            created_at=datetime.utcnow(),
        )
    )
    session_token = sessions.create(str(user.get("id")), "gitlab")
    return {
        "status": "connected",
        "user": {"id": user.get("id"), "username": user.get("username")},
        "session_token": session_token,
    }


@app.get("/api/auth/session")
def get_session(x_session_token: str | None = Header(default=None)) -> dict:
    if not x_session_token:
        raise HTTPException(status_code=401, detail="Missing session token")
    session = sessions.get(x_session_token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    return session


@app.post("/api/webhooks/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
) -> dict:
    payload = await request.body()
    if not verify_github_signature(settings.github_webhook_secret, payload, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")
    return await handle_github_webhook(payload, enqueue_review)


@app.post("/api/webhooks/gitlab")
async def gitlab_webhook(
    request: Request,
    x_gitlab_token: str | None = Header(default=None),
) -> dict:
    payload = await request.body()
    if not verify_gitlab_token(settings.gitlab_webhook_secret, x_gitlab_token):
        raise HTTPException(status_code=401, detail="Invalid token")
    return await handle_gitlab_webhook(payload, enqueue_review)
