from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional
from urllib.parse import urlparse

import requests


@dataclass(frozen=True)
class GitLabMR:
    project_path: str
    iid: str


def parse_mr_url(mr_url: str) -> GitLabMR | None:
    parsed = urlparse(mr_url)
    if "gitlab" not in parsed.netloc:
        return None
    parts = parsed.path.strip("/").split("/")
    if len(parts) < 3 or parts[-2] != "merge_requests":
        return None
    project_path = "/".join(parts[:-2])
    return GitLabMR(project_path=project_path, iid=parts[-1])


def post_mr_comment(mr_url: str, body: str, token: str) -> bool:
    mr = parse_mr_url(mr_url)
    if mr is None:
        return False
    url = f"https://gitlab.com/api/v4/projects/{requests.utils.quote(mr.project_path, safe='')}/merge_requests/{mr.iid}/notes"
    response = requests.post(
        url,
        headers={"PRIVATE-TOKEN": token},
        json={"body": body},
        timeout=15,
    )
    return response.status_code in {200, 201}


def post_mr_inline_comments(
    mr_url: str,
    comments: Iterable[object],
    token: str,
    commit_id: Optional[str] = None,
) -> bool:
    mr = parse_mr_url(mr_url)
    if mr is None:
        return False
    if not commit_id:
        return False
    url = f"https://gitlab.com/api/v4/projects/{requests.utils.quote(mr.project_path, safe='')}/merge_requests/{mr.iid}/discussions"

    for comment in comments:
        file_path = getattr(comment, "file_path", None)
        line_number = getattr(comment, "line_number", None)
        content = getattr(comment, "content", None)
        if not file_path or not line_number or not content:
            continue
        payload = {
            "body": content,
            "position": {
                "position_type": "text",
                "new_path": file_path,
                "new_line": line_number,
                "head_sha": commit_id,
            },
        }
        response = requests.post(
            url,
            headers={"PRIVATE-TOKEN": token},
            json=payload,
            timeout=15,
        )
        if response.status_code not in {200, 201}:
            return False
    return True


def set_commit_status(
    mr_url: str,
    commit_id: str,
    state: str,
    description: str,
    token: str,
) -> bool:
    mr = parse_mr_url(mr_url)
    if mr is None:
        return False
    url = f"https://gitlab.com/api/v4/projects/{requests.utils.quote(mr.project_path, safe='')}/statuses/{commit_id}"
    response = requests.post(
        url,
        headers={"PRIVATE-TOKEN": token},
        data={"state": state, "description": description, "name": "ai-review"},
        timeout=15,
    )
    return response.status_code in {200, 201}
