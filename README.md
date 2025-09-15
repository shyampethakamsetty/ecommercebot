# Ecomm Orchestrator — Extended Scaffold
This repository is an extended, modular, and scalable scaffold for the Automated E-Commerce Workflow Orchestrator.
It includes:
- FastAPI backend with modular routers and task endpoints
- Celery worker with Playwright automation (robust runner, stealth / proxy hooks)
- Worker posts results back to backend for persistence
- SQLAlchemy models and Alembic skeleton
- Dockerfiles + docker-compose for local development (includes postgres, redis, backend, worker, flower)
- Frontend React skeleton (chat UI + dashboard)
- LangChain/OpenAI integration points (adapter & prompt examples)
- Debugging helpers: screenshot artifact volume `./worker-data` mounted to container `/tmp/worker-data`

Notes:
- This is a scaffold with working pieces — you will still need to provide real OpenAI API key and optionally proxy credentials.
- For Cloudflare evasion, see `workers/worker/playwright_runner.py` stealth hooks and `workers/worker/botasaurus_adapter.py` placeholder.


## LangChain Chat Integration

POST /api/chat/query with JSON `{ "query": "...", "user_id": 1 }` to parse and enqueue workflows. Set `OPENAI_API_KEY` in `.env` to enable LLM parsing.


## OpenAI LangChain Integration
Set `OPENAI_API_KEY` in your `.env` to enable LLM parsing for chat.
\n\n## Proxy & Stealth\nTo use proxies set `PROXY_LIST` environment variable as comma-separated proxy URLs or mount a file at `./proxies.txt` and the worker will consume them. The Playwright runner uses `ProxyManager` to rotate proxies.\n

## Container hardening
Images create a non-root user (`backenduser`, `workeruser`, `frontenduser`) and switch to it at build time. CI skeleton available under `.github/workflows/ci.yml`.


## Additional integrations implemented
- Optional Botasaurus integration shim (install the package to enable stronger stealth).
- Proxy health probe script in `workers/worker/proxy_health.py`.
- Frontend chat UI enhanced to show artifact thumbnails and lightbox.
- CI workflow builds Docker images and runs a simple smoke curl against backend health endpoint.
