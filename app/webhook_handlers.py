from __future__ import annotations

import json
from typing import Any, Awaitable, Callable
from uuid import UUID

import requests

from app.config import settings


def _fetch_github_diff(diff_url: str) -> str:
    headers = {"Accept": "application/vnd.github.v3.diff"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    response = requests.get(diff_url, headers=headers, timeout=15)
    response.raise_for_status()
    return response.text


async def handle_github_webhook(
    payload: bytes, enqueue: Callable[[str, str, dict], Awaitable[UUID]]
) -> dict:
    data = json.loads(payload.decode("utf-8"))
    action = data.get("action")
    if action not in {"opened", "reopened", "synchronize"}:
        return {"status": "ignored", "action": action}

    pr = data.get("pull_request", {})
    diff_url = pr.get("diff_url")
    metadata = {
        "source": "github",
        "action": action,
        "repo": data.get("repository", {}).get("full_name"),
        "pr_url": pr.get("html_url"),
        "commit_id": pr.get("head", {}).get("sha"),
    }

    diff_text = ""
    if diff_url:
        try:
            diff_text = _fetch_github_diff(diff_url)
        except Exception as exc:
            metadata["diff_error"] = str(exc)

    review_id = await enqueue(diff_text, metadata)
    return {"status": "accepted", "review_id": str(review_id)}


async def handle_gitlab_webhook(
    payload: bytes, enqueue: Callable[[str, str, dict], Awaitable[UUID]]
) -> dict:
    data = json.loads(payload.decode("utf-8"))
    if data.get("object_kind") != "merge_request":
        return {"status": "ignored", "object_kind": data.get("object_kind")}

    metadata = {
        "source": "gitlab",
        "action": data.get("object_attributes", {}).get("action"),
        "repo": data.get("project", {}).get("path_with_namespace"),
        "pr_url": data.get("object_attributes", {}).get("url"),
        "commit_id": data.get("object_attributes", {}).get("last_commit", {}).get("id"),
    }
    review_id = await enqueue("", metadata)
    return {"status": "accepted", "review_id": str(review_id)}
