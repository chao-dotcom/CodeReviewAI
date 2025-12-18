from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
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
