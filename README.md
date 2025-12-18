Agentic AI Code Review Platform (MVP)

Quick start (dev)
1) Backend: `uvicorn app.main:app --reload`
2) Frontend: `cd frontend && npm install && npm run dev`

Docker compose
`docker-compose up --build`

Health check
- `GET /health`

Celery mode
- Set `USE_CELERY=1` and run worker: `celery -A app.celery_app.celery_app worker -Q reviews --loglevel=info`

RAG (Chroma)
- Set `USE_CHROMA=1` and `CHROMA_PATH=./chroma_db`

Training
- LoRA: `python training/lora_train.py`
- DPO: `python training/dpo_train.py`

OAuth (optional)
- GitHub: set `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `GITHUB_REDIRECT_URI`
- GitLab: set `GITLAB_CLIENT_ID`, `GITLAB_CLIENT_SECRET`, `GITLAB_REDIRECT_URI`
- Optional token encryption: set `TOKEN_ENCRYPTION_KEY` (Fernet key).
- Session: OAuth callbacks return `session_token` for `GET /api/auth/session`.

GitHub PR comments (optional)
- Set `GITHUB_TOKEN` to enable posting review summaries back to PRs.
- Inline comments require PR `commit_id` available from webhook metadata.
- Check runs are posted when `commit_id` is available.

GitLab MR comments (optional)
- Set `GITLAB_TOKEN` to enable posting summary + inline comments.
- Commit status is set when `commit_id` is available.

LLM inference
- Set `LLM_BACKEND=local` and `LLM_MODEL` to a local HF model.
- Optional adapter: `LLM_ADAPTER_PATH` (LoRA checkpoint) and `LLM_ADAPTER_TYPE=lora`.
- Optional quantization: `LLM_QUANTIZATION=8bit` (requires bitsandbytes).
- Optional cache: `LLM_CACHE_REDIS_URL=redis://...` for shared caching.

Preferences
- `GET /api/reviews/{id}/preferences` exports feedback-based pairs.
- `GET /api/reviews/{id}/preferences/auto` exports heuristic agent-based pairs.
- `GET /api/preferences/auto` exports heuristic pairs across reviews.

Rate limiting (optional)
- Set `RATE_LIMIT_PER_HOUR` to enable basic in-memory throttling.
