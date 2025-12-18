from __future__ import annotations

from fastapi import Header, HTTPException

from app.config import settings


def require_api_key(x_api_key: str | None = Header(default=None)) -> str:
    if not settings.api_key:
        return "anonymous"
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return "api_key_user"
