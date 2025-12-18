from __future__ import annotations

from app.config import settings


class TokenCipher:
    def __init__(self) -> None:
        self.key = settings.token_encryption_key
        self._fernet = None
        if self.key:
            from cryptography.fernet import Fernet

            self._fernet = Fernet(self.key)

    def encrypt(self, value: str) -> str:
        if not self._fernet:
            return value
        return self._fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def decrypt(self, value: str) -> str:
        if not self._fernet:
            return value
        return self._fernet.decrypt(value.encode("utf-8")).decode("utf-8")
