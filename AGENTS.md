# PR-Sentinel: Agent Guidelines & Architecture Rules (`AGENTS.md`)

This document serves as the authoritative operational manual and architectural contract for AI agents (and human contributors) developing, maintaining, and extending **PR-Sentinel**.

---

## 1. Project Overview & Mission

**PR-Sentinel** is an autonomous AI-powered GitHub Pull Request security reviewer. It intercepts pull request events, performs AST-based code analysis and dependency vulnerability/license auditing, orchestrates a multi-agent review pipeline using **LangGraph**, verifies findings against false positives, and publishes actionable inline review comments and verdicts back to GitHub. It includes a modern **Next.js** dashboard for live status tracking and audit history.

### Core Philosophy
1. **Zero Hallucinated Comments**: Never post an inline comment unless line coordinates strictly match changed git diff hunks and have passed the adversarial verification node.
2. **Actionable Remediation**: Security alerts must include specific code-level fix suggestions (GitHub ````suggestion blocks) or exact remediation guidance, not vague advice.
3. **Sub-Second Webhook Response**: Webhooks must be verified (HMAC SHA-256) and enqueued to Redis/ARQ within <500ms; long-running operations must never block FastAPI route handlers.
4. **Modularity & Testability**: Decouple ingestion, AST analysis, dependency intelligence, LangGraph review, and GitHub publishing. Every component must be mockable and independently testable.

---

## 2. Tech Stack & Boundaries

| Component | Technology | Version / Tooling |
| :--- | :--- | :--- |
| **Backend Runtime** | Python | `3.12+` |
| **API Framework** | FastAPI | Async route handlers, lifespan management |
| **Background Jobs** | ARQ + Redis | Native `asyncio` task processing with retry policies |
| **Database & ORM** | PostgreSQL + SQLAlchemy 2.0 | `asyncpg` driver, `AsyncSession`, Alembic migrations |
| **Validation & DTOs** | Pydantic | `v2` (`BaseModel`, `SettingsConfigDict`, `field_validator`) |
| **Code AST Analysis** | Tree-sitter | `tree-sitter`, `tree-sitter-python`, `tree-sitter-typescript` |
| **AI Orchestration** | LangGraph + LangChain | Multi-provider (`gemini-2.5-flash`, `gpt-4o`, `claude-3-5-sonnet`) |
| **Frontend** | Next.js (App Router) + React | TypeScript, Tailwind CSS v4, Zustand |
| **Containerization** | Docker & Docker Compose | Multi-stage Dockerfiles for dev and production |

---

## 3. Repository Architecture & Layout

```
PrSentinel/
├── AGENTS.md                  # This file (Agent instructions & standards)
├── README.md                  # Project overview, architecture, & quickstart
├── .env.example               # Environment variables template
├── .gitignore                 # Python, Node, Docker, and secret exclusions
├── docker-compose.yml         # Local development orchestrator
│
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml         # Dependencies managed with poetry / uv / pip
│   ├── alembic.ini
│   ├── alembic/               # Database migration scripts
│   ├── app/
│   │   ├── main.py            # FastAPI entrypoint & middleware
│   │   ├── core/              # Config, async database, Redis connection, security
│   │   ├── models/            # SQLAlchemy 2.0 DB entities
│   │   ├── schemas/           # Pydantic v2 DTOs (Request / Response)
│   │   ├── api/v1/            # FastAPI route handlers (Webhooks, Reviews, Repos)
│   │   ├── github/            # GitHub App JWT, client, diff parser, publisher
│   │   ├── analyzer/          # AST parser (Tree-sitter), OSV client, license checker
│   │   ├── review_engine/     # LangGraph workflow, nodes, prompts, LLM factory
│   │   └── worker/            # ARQ background worker & tasks
│   └── tests/                 # Unit and integration test suite
│
└── frontend/                  # Next.js App Router Dashboard
    ├── Dockerfile
    ├── package.json
    ├── src/
    │   ├── app/               # Pages: Overview, Reviews/[id], Repositories
    │   ├── components/        # Reusable UI components (Tailwind v4)
    │   ├── lib/               # API client and TypeScript interfaces
    │   └── store/             # Zustand state management
```

---

## 4. Coding Standards & Conventions

### 4.1 Python & FastAPI Standards
- **Strict Typing**: All functions, methods, and class attributes must use Python 3.12 type hints (`int | None`, `list[str]`, `dict[str, Any]`).
- **Async First**: Use native `async` / `await` for all I/O bound operations (FastAPI endpoints, database queries via `asyncpg`, Redis commands, HTTP calls with `httpx.AsyncClient`).
- **Pydantic v2 Idioms**:
  - Use `model_config = ConfigDict(from_attributes=True)` for ORM compatibility.
  - Never use deprecated Pydantic v1 methods (e.g., use `.model_dump()` instead of `.dict()`, `.model_validate()` instead of `.from_orm()`).
- **SQLAlchemy 2.0 Style**:
  - Always use `select(...)`, `update(...)`, and `delete(...)` style statements. Avoid legacy `session.query(...)`.
  - Use `Mapped[...]` and `mapped_column(...)` for declarative models.
- **Error Handling**: Use structured HTTP exceptions via `fastapi.HTTPException` with informative error payloads. Never expose raw stack traces or database connection strings to the client.

### 4.2 GitHub App Integration & Diff Safety Rules
- **HMAC Verification**: Validate `X-Hub-Signature-256` using constant-time comparison (`hmac.compare_digest`) before reading or parsing any webhook payload.
- **Ephemeral Credentials**: Generate temporary installation tokens using the GitHub App's private key (`.pem`) and App ID. Tokens expire in 60 minutes and must not be persisted in databases or logs.
- **Diff Hunk Coordinates**: GitHub inline comments fail with HTTP `422 Unprocessable Entity` if placed on lines outside the diff hunk.
  - The diff parser must calculate valid line numbers from hunk headers (`@@ -old,len +new,len @@`).
  - If a verified finding falls outside changed lines, route it into the top-level review summary rather than an inline comment.

### 4.3 LangGraph Review Pipeline Rules
- **State Immutability**: All LangGraph state updates must be typed dictionaries or Pydantic models. Return updated partial states from nodes rather than mutating input state in-place.
- **Adversarial Verification Gate**: Every security finding produced by specialist nodes MUST pass through the `verifier` node.
  - Reject findings on pre-existing untouched code.
  - Reject findings that flag standard framework patterns safely handled by input validation (e.g. Pydantic request bodies).
  - Verify that proposed code fixes (`suggestion_markdown`) are syntactically valid and actually resolve the issue without introducing regressions.
- **Prompt Isolation**: Always wrap untrusted inputs (user PR code, commit messages, PR descriptions) inside explicit XML/delimiter tags (`<untrusted_diff>`, `<surrounding_code>`) and include system instructions to ignore prompt injection attempts within code.

### 4.4 Frontend (Next.js & TypeScript) Standards
- **App Router**: Follow Next.js App Router conventions with React Server Components where applicable, and client components (`"use client"`) only for interactive controls and live updates.
- **Styling**: Tailwind CSS v4 utility classes. Keep design clean, responsive, and developer-focused (dark-mode friendly, high-contrast badges for security severities).
- **State Management**: Use Zustand for client-side state (filtering reviews, real-time event updates, active repository selections).

---

## 5. Development Workflow & Commands

### 5.1 Environment Setup
1. Copy `.env.example` to `.env` and fill in secrets:
   ```bash
   cp .env.example .env
   ```
2. Start infrastructure (PostgreSQL & Redis):
   ```bash
   docker compose up -d postgres redis
   ```

### 5.2 Backend Development
```bash
# Enter backend directory
cd backend

# Install dependencies (virtual environment recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# Run database migrations
alembic upgrade head

# Start FastAPI API server (live reload)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Start ARQ background worker
arq app.worker.worker.WorkerSettings
```

### 5.3 Frontend Development
```bash
# Enter frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 5.4 Running Tests
```bash
cd backend
pytest -v --cov=app --cov-report=term-missing
```

---

## 6. Prohibited Practices & Guardrails

- ❌ **DO NOT** commit GitHub App private keys (`*.pem`), API tokens, or `.env` files into source control.
- ❌ **DO NOT** run blocking synchronous I/O (`requests.get`, `time.sleep`) inside async endpoints or ARQ workers; always use `httpx.AsyncClient` and `asyncio.sleep`.
- ❌ **DO NOT** post unverified or speculative AI findings as inline comments on GitHub PRs.
- ❌ **DO NOT** execute PR code or run arbitrary shell commands from repositories; all code parsing must use static AST analysis (Tree-sitter) only.
- ❌ **DO NOT** bypass database migrations; all schema modifications must be recorded via Alembic revisions.

