from __future__ import annotations

import hmac
import hashlib


def verify_github_signature(secret: str, payload: bytes, signature: str | None) -> bool:
    if not secret:
        return True
    if not signature or not signature.startswith("sha256="):
        return False
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, f"sha256={digest}")


def verify_gitlab_token(secret: str, token: str | None) -> bool:
    if not secret:
        return True
    return token == secret
