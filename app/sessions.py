from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional


class SessionStore:
    def __init__(self, ttl_hours: int = 24) -> None:
        self._sessions: Dict[str, dict] = {}
        self._ttl = timedelta(hours=ttl_hours)

    def create(self, user_id: str, provider: str) -> str:
        token = secrets.token_urlsafe(32)
        self._sessions[token] = {
            "user_id": user_id,
            "provider": provider,
            "expires_at": datetime.utcnow() + self._ttl,
        }
        return token

    def get(self, token: str) -> Optional[dict]:
        session = self._sessions.get(token)
        if not session:
            return None
        if session["expires_at"] < datetime.utcnow():
            self._sessions.pop(token, None)
            return None
        return session

    def revoke(self, token: str) -> None:
        self._sessions.pop(token, None)
