from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional
from urllib.parse import urlparse

import requests


@dataclass(frozen=True)
class GitHubPR:
    owner: str
    repo: str
    number: str


def parse_pr_url(pr_url: str) -> GitHubPR | None:
    parsed = urlparse(pr_url)
    if parsed.netloc != "github.com":
        return None
    parts = parsed.path.strip("/").split("/")
    if len(parts) < 4 or parts[2] != "pull":
        return None
    return GitHubPR(owner=parts[0], repo=parts[1], number=parts[3])


def build_summary(comments: Iterable[object]) -> str:
    lines = ["Automated review summary:"]
    for comment in comments:
        line = getattr(comment, "content", "")
        file_path = getattr(comment, "file_path", "")
        severity = getattr(comment, "severity", "info")
        if line:
            lines.append(f"- [{severity}] {file_path}: {line}")
    return "\n".join(lines)


def post_pr_comment(pr_url: str, body: str, token: str) -> bool:
    pr = parse_pr_url(pr_url)
    if pr is None:
        return False
    url = f"https://api.github.com/repos/{pr.owner}/{pr.repo}/issues/{pr.number}/comments"
    response = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        json={"body": body},
        timeout=15,
    )
    return response.status_code in {200, 201}


def post_review_comments(
    pr_url: str,
    body: str,
    comments: Iterable[object],
    token: str,
    commit_id: Optional[str] = None,
) -> bool:
    pr = parse_pr_url(pr_url)
    if pr is None:
        return False
    url = f"https://api.github.com/repos/{pr.owner}/{pr.repo}/pulls/{pr.number}/comments"
    response = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        json={"body": body, "commit_id": commit_id} if commit_id else {"body": body},
        timeout=15,
    )
    if response.status_code not in {200, 201}:
        return False
    review_id = response.json().get("id")
    if not review_id:
        return True

    for comment in comments:
        file_path = getattr(comment, "file_path", None)
        line_number = getattr(comment, "line_number", None)
        content = getattr(comment, "content", None)
        if not file_path or not line_number or not content:
            continue
        payload = {
            "body": content,
            "path": file_path,
            "line": line_number,
            "side": "RIGHT",
            "commit_id": commit_id,
        }
        requests.post(
            f"https://api.github.com/repos/{pr.owner}/{pr.repo}/pulls/{pr.number}/comments",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
            json=payload,
            timeout=15,
        )
    return True


def create_check_run(
    pr_url: str,
    commit_id: str,
    title: str,
    summary: str,
    token: str,
) -> bool:
    pr = parse_pr_url(pr_url)
    if pr is None:
        return False
    url = f"https://api.github.com/repos/{pr.owner}/{pr.repo}/check-runs"
    payload = {
        "name": title,
        "head_sha": commit_id,
        "status": "completed",
        "conclusion": "neutral",
        "output": {"title": title, "summary": summary[:65535]},
    }
    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        },
        json=payload,
        timeout=15,
    )
    return response.status_code in {200, 201}
