# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

```bash
# Backend
cd backend && uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
cd backend && pytest tests/ -v                          # Run all tests
cd backend && pytest tests/test_articles.py -v          # Single test file
cd backend && alembic upgrade head                      # Run migrations
cd backend && alembic revision --autogenerate -m "..."  # Create migration

# Frontend
cd frontend && npm run dev          # Vite dev server (port 5173)
cd frontend && npm run build        # tsc + vite build

# Docker
docker compose up -d                # All 3 services (backend:8000, frontend:5173, db:5433)
docker compose down                 # Stop all
docker compose logs -f backend      # Follow backend logs

# Quick health check
curl localhost:8000/api/v1/health   # {database, llm_service, wordpress} status
```

## Architecture

### State Machine (14 States)

The article state machine at `backend/app/services/article_service.py:20-33` defines ALL valid transitions in `VALID_TRANSITIONS`. Every state change MUST go through `validate_transition()` / `update_status()`. Key rule: **generating → ready** (LLM completes), **ready → approved** (user confirms), **approved → next generating** (auto-triggered by the router handler). `failed` is recoverable from any generating state; `cancelled` and `published` are terminal.

### Four-Stage Pipeline

Each stage follows the same pattern in the router (`backend/app/routers/articles.py`):
1. **Outline** (`outline_service.generate_outline`): LLM generates JSON outline → `outline_ready`
2. **Content** (`content_service.generate_content`): LLM generates each section as HTML → `content_ready`
3. **Images** (`image_service.search_and_insert_images`): LLM generates keywords → Unsplash API → `images_ready`
4. **Publish** (inline in router): WP REST API create post → `published`

Each service function updates the article status AND broadcasts SSE events via `stream_manager`. The router handlers orchestrate the transition: they call the service, check if the next transition should auto-fire (auto mode), and commit.

### Auto-Publish Mode

When `article.mode == "auto"`, each service function auto-transitions past the `_ready` state at the end of its work. For example, `generate_outline()` ends with `outline_ready` then immediately transitions to `outline_approved` if auto mode. The frontend polls/SSEs for progress but shows no approval buttons.

### Backend Service Layer

All business logic is in `backend/app/services/`:
- `article_service.py` — CRUD + state transitions + ORM-to-schema mapping
- `llm_service.py` — OpenAI-compatible API wrapper with tenacity retry (3 attempts, exponential backoff)
- `outline_service.py` — outline generation orchestration
- `content_service.py` — section-by-section content generation + SSE per section
- `image_service.py` — LLM keyword gen → Unsplash search
- `wordpress_service.py` — WP REST API with Basic Auth, tenacity retry (3 attempts)
- `stream_service.py` — asyncio.Queue per article ID for SSE broadcasting

### Database

PostgreSQL 16 with asyncpg. Two tables:
- `articles` — JSONB columns for `outline`, `content`, `images`, `progress` (see schema in plan file)
- `generation_events` — audit trail for every LLM call

The JSONB schemas are defined Pydantic-side in `schemas/article.py` (OutlineSchema, ArticleContentSchema, ArticleImageSchema) but the DB layer stores raw dicts — no JSONB validation at the DB level.

### Schema CamelCase Convention

All Pydantic request/response schemas use `CamelModel` (`backend/app/schemas/article.py:9`) which auto-converts Python snake_case to camelCase in JSON. The API speaks camelCase. The DB models use snake_case column names. `article_to_detail()` / `article_to_list_item()` in `article_service.py` handle mapping ORM objects to Pydantic schemas.

### Frontend Data Flow

React Query (`@tanstack/react-query`) manages all server state:
- `useArticle(id)` polls every 3s when status is a generating state
- `useArticles()` polls every 10s for the sidebar list
- Mutations (`useApproveOutline`, `usePublishArticle`, etc.) invalidate `['article', id]` and `['articles']` on success
- SSE streaming is used for real-time progress but NOT for state changes (those come from polling)

### Security / Sanitization Pipeline

Three layers:
1. Pydantic v2 validates all input at the API boundary (field lengths, types, enums)
2. `bleach` sanitizes LLM-generated HTML before DB storage (`utils/sanitizer.py`, called in `content_service.py:72`)
3. `DOMPurify` sanitizes HTML before `dangerouslySetInnerHTML` in the frontend (`ContentRenderer.tsx`)

WordPress credentials use `SecretStr` — `__str__()` returns `**********`. The `.env` file is in `.gitignore`. WP auth is backend-only; the frontend never sees the application password.

### Error Handling Pattern

- Router handlers use try/except with `mark_failed()` + rollback
- External services use tenacity `@retry` with `retry_if_exception(_is_retryable)`
- WP 401 → HALT immediately (no retries, as defined in `wordpress_service.py:_is_retryable`)
- Custom `AppException` hierarchy in `core/exceptions.py` with `AppExceptionHandler` in `main.py`
- API response envelope: `{success: bool, data: T, error?: string, detail?: string, meta?: {total, page, limit}}`

## Planning Conventions

All project planning documents MUST be saved to `.claude/plan/` at the project root. Use the naming format `{scope}-v{version}-{summary}.md`:

- `blog-v1.3.2-bugfixes.md` — bug fix plans
- `blog-v1.3-improvements.md` — feature/improvement plans
- `image-pipeline-ux-improvements.md` — subsystem-specific plans

Never save plans to `~/.claude/plans/` — that is for global/user-level plans only.
