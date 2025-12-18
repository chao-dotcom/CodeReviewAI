from __future__ import annotations

from uuid import UUID

from app.celery_app import celery_app
from app.config import settings
from app.integrations.github import build_summary, create_check_run, post_pr_comment, post_review_comments
from app.integrations.gitlab import post_mr_comment, post_mr_inline_comments, set_commit_status
from app.pipeline.review import run_review_pipeline
from app.rag.service import RagService
from app.storage_sql import SqlStore


@celery_app.task(name="app.tasks.process_review")
def process_review(review_id: str, diff_text: str) -> None:
    store = SqlStore(settings.database_url)
    rag_index = RagService()
    review_uuid = UUID(review_id)
    store.mark_in_progress(review_uuid)
    try:
        comments, traces, messages = run_review_pipeline(review_uuid, diff_text, rag_index=rag_index)
        store.add_comments(review_uuid, comments)
        store.add_traces(review_uuid, traces)
        store.add_messages(review_uuid, messages)
        store.complete_review(review_uuid)
        review = store.get_review(review_uuid)
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
        store.mark_failed(review_uuid, str(exc))
