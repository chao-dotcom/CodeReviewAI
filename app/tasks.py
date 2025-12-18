from __future__ import annotations

from uuid import UUID

from app.celery_app import celery_app
from app.config import settings
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
        comments, traces = run_review_pipeline(review_uuid, diff_text, rag_index=rag_index)
        store.add_comments(review_uuid, comments)
        store.add_traces(review_uuid, traces)
        store.complete_review(review_uuid)
    except Exception as exc:
        store.mark_failed(review_uuid, str(exc))
