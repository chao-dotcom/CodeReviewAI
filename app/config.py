from __future__ import annotations

import os


class Settings:
    def __init__(self) -> None:
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./codereview.db")
        self.use_database = os.getenv("USE_DATABASE", "0") == "1"
        self.use_celery = os.getenv("USE_CELERY", "0") == "1"
        self.celery_broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
        self.celery_result_backend = os.getenv(
            "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
        )
        self.use_chroma = os.getenv("USE_CHROMA", "0") == "1"
        self.chroma_path = os.getenv("CHROMA_PATH", "./chroma_db")
        self.chroma_collection = os.getenv("CHROMA_COLLECTION", "code_review_kb")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.api_key = os.getenv("API_KEY", "")
        self.github_webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
        self.gitlab_webhook_secret = os.getenv("GITLAB_WEBHOOK_SECRET", "")


settings = Settings()
