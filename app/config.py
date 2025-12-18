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
        self.github_token = os.getenv("GITHUB_TOKEN", "")
        self.gitlab_token = os.getenv("GITLAB_TOKEN", "")
        self.github_client_id = os.getenv("GITHUB_CLIENT_ID", "")
        self.github_client_secret = os.getenv("GITHUB_CLIENT_SECRET", "")
        self.github_redirect_uri = os.getenv("GITHUB_REDIRECT_URI", "")
        self.gitlab_client_id = os.getenv("GITLAB_CLIENT_ID", "")
        self.gitlab_client_secret = os.getenv("GITLAB_CLIENT_SECRET", "")
        self.gitlab_redirect_uri = os.getenv("GITLAB_REDIRECT_URI", "")
        self.llm_backend = os.getenv("LLM_BACKEND", "local")
        self.llm_model = os.getenv("LLM_MODEL", "gpt2")
        self.llm_max_tokens = int(os.getenv("LLM_MAX_TOKENS", "256"))
        self.llm_temperature = float(os.getenv("LLM_TEMPERATURE", "0.2"))
        self.use_langgraph = os.getenv("USE_LANGGRAPH", "0") == "1"
        self.llm_device = os.getenv("LLM_DEVICE", "cpu")
        self.llm_adapter_path = os.getenv("LLM_ADAPTER_PATH", "")
        self.llm_adapter_type = os.getenv("LLM_ADAPTER_TYPE", "lora")
        self.llm_cache_size = int(os.getenv("LLM_CACHE_SIZE", "256"))
        self.token_encryption_key = os.getenv("TOKEN_ENCRYPTION_KEY", "")
        self.rate_limit_per_hour = int(os.getenv("RATE_LIMIT_PER_HOUR", "0"))
        self.llm_quantization = os.getenv("LLM_QUANTIZATION", "none")
        self.llm_batch_size = int(os.getenv("LLM_BATCH_SIZE", "4"))
        self.llm_cache_redis_url = os.getenv("LLM_CACHE_REDIS_URL", "")
        self.session_cookie_name = os.getenv("SESSION_COOKIE_NAME", "cr_session")
        self.session_ttl_hours = int(os.getenv("SESSION_TTL_HOURS", "24"))


settings = Settings()
