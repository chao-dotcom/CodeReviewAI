Agentic AI Code Review Platform (MVP)

Quick start (dev)
1) Backend: `uvicorn app.main:app --reload`
2) Frontend: `cd frontend && npm install && npm run dev`

Docker compose
`docker-compose up --build`

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

GitHub PR comments (optional)
- Set `GITHUB_TOKEN` to enable posting review summaries back to PRs.
