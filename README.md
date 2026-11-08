# 🛡️ PR-Sentinel

> **Autonomous AI-Powered GitHub Pull Request Security Reviewer**

PR-Sentinel is an autonomous, context-aware security code reviewer that intercepts GitHub pull requests, performs AST-based code analysis and dependency vulnerability/license auditing, orchestrates multi-agent security evaluation using **LangGraph**, verifies findings against false positives, and publishes actionable inline review comments and verdicts back to GitHub.

---

## 🚀 Key Capabilities

- **⚡ Sub-Second Webhook Processing**: Verifies GitHub HMAC-SHA256 signatures and offloads analysis to an asynchronous worker queue in <500ms.
- **🌳 AST-Aware Code Context**: Leverages **Tree-sitter** (Python & TypeScript/JavaScript) to parse enclosing functions, classes, decorators, and imports around modified diff hunks.
- **📦 OSV.dev CVE & License Auditing**: Checks changed package manifests (`requirements.txt`, `pyproject.toml`, `package.json`) against the OSV.dev vulnerability database and enforces SPDX license compliance.
- **🤖 Multi-Agent Review Pipeline (LangGraph)**:
  - **Code Security Specialist**: Evaluates OWASP Top 10 vulnerabilities, injection risks, auth bypasses, and secret leaks.
  - **Dependency & License Specialist**: Correlates CVE matches and evaluates license compatibility.
  - **Synthesis & Deduplication Node**: Unifies cross-file findings and eliminates redundant alerts.
  - **Red-Team Verifier**: Adversarially evaluates candidate findings to eliminate false positives and strictly validates git diff line coordinates to prevent GitHub 422 API errors.
- **💬 Actionable GitHub Inline Comments**: Posts line-targeted comments with formatted ````suggestion code replacements and sticky top-level review summaries.
- **📊 Modern Web Dashboard**: Next.js App Router, Tailwind CSS v4, and Zustand UI for tracking review runs, inspecting findings, and configuring repository policies.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    GH[GitHub PR Event] -->|Webhook POST /api/v1/webhooks/github| API[FastAPI Ingestion Engine]
    API -->|1. HMAC Verification| SEC[Security / Auth Guard]
    API -->|2. Enqueue Job| REDIS[(Redis Queue & Cache)]
    API -->|3. Immediate 202 Accepted| GH
    
    WORKER[ARQ Background Worker] -->|Pulls Job| REDIS
    WORKER -->|Fetch Diffs & Files| GH_CLIENT[GitHub API Client]
    
    subgraph Analysis_Engine [Code & Dependency Analysis Engine]
        GH_CLIENT --> DIFF_P[Git Diff & Hunk Parser]
        GH_CLIENT --> TS_PARSER[Tree-sitter AST Parser (Py/TS)]
        GH_CLIENT --> DEP_PARSER[Manifest & Lockfile Parser]
        DEP_PARSER --> OSV_CLIENT[OSV.dev REST Client]
    end

    subgraph LangGraph_Review [LangGraph Multi-Agent Security Engine]
        DIFF_P & TS_PARSER & OSV_CLIENT --> STATE[Review Graph State]
        STATE --> CODE_AGENT[Code Security Specialist Node]
        STATE --> DEP_AGENT[Dependency & License Specialist Node]
        CODE_AGENT & DEP_AGENT --> SYNTH[Finding Synthesis Node]
        SYNTH --> VERIFIER[Red-Team Verifier & Diff-Line Validator]
    end

    VERIFIER -->|Publish Review & Inline Comments| GH_PUB[GitHub Review Publisher]
    GH_PUB -->|POST /pulls/{id}/reviews| GH
    
    WORKER -->|Persist Results| DB[(PostgreSQL Database)]
    
    subgraph Frontend_App [Next.js Dashboard]
        DASH[Next.js + Tailwind v4 + Zustand UI] -->|REST / SSE /api/v1/reviews| API
        DB --> API
    end
```

---

## 🛠️ Tech Stack

| Layer | Technology | Details |
| :--- | :--- | :--- |
| **Backend API** | FastAPI (Python 3.12) | Async routes, Pydantic v2 schemas, lifespan management |
| **Worker Queue** | ARQ + Redis | Native async Redis queue with retry policies |
| **Database** | PostgreSQL + SQLAlchemy 2.0 | Async engine (`asyncpg`), Alembic schema migrations |
| **AST Analysis** | Tree-sitter | Python (`tree-sitter-python`) & TS (`tree-sitter-typescript`) |
| **AI Orchestration** | LangGraph | Multi-agent state graph with specialist and verifier nodes |
| **LLM Support** | Multi-Provider via LangChain | Google Gemini (default), OpenAI GPT-4o, Anthropic Claude |
| **Vulnerability DB** | OSV.dev | Batch API for PyPI and npm security advisories |
| **Frontend** | Next.js 15 + Tailwind CSS v4 | React App Router, Zustand, TypeScript |
| **Deployment** | Docker & Docker Compose | Multi-container local & production setup |

---

## 📋 Phased Roadmap

- [x] **Architecture & Agent Guidelines**: System blueprint approved, `AGENTS.md`, and configuration templates.
- [ ] **Phase 1: Project Foundation & GitHub Integration**: Docker compose, FastAPI core, SQLAlchemy 2.0 models, GitHub App JWT auth, HMAC verification, and ARQ worker queue.
- [ ] **Phase 2: Code Analysis & Repository Context Engine**: Unified diff parsing, Tree-sitter AST scope and symbol extraction for Python and TypeScript.
- [ ] **Phase 3: Security Intelligence & Dependency Analysis**: `requirements.txt`/`package.json` manifest parsing, OSV.dev batch queries, and SPDX license enforcement.
- [ ] **Phase 4: AI Review Engine & LangGraph Multi-Agent Orchestration**: Specialist agents, finding synthesis, adversarial red-team verifier, and verdict calculator.
- [ ] **Phase 5: Finding Verification & GitHub Review Publishing**: Line-accurate inline comment publishing with ````suggestion blocks and sticky review summaries.
- [ ] **Phase 6: Product Experience, Testing & Deployment**: Next.js portfolio dashboard with live review updates, comprehensive test suite, and Docker deployment.

---

## 🏃 Getting Started

### Prerequisites
- Docker and Docker Compose
- Python 3.12+
- Node.js 20+
- A GitHub App configured with Pull Request permissions (Read & Write)

### 1. Clone & Configure
```bash
git clone https://github.com/your-username/PrSentinel.git
cd PrSentinel
cp .env.example .env
# Edit .env and supply your credentials and LLM API key
```

### 2. Start with Docker Compose
```bash
docker compose up -d
```

### 3. Check System Health
```bash
curl http://localhost:8000/healthz
```

For detailed agent rules, coding standards, and developer guidelines, see [AGENTS.md](file:///d:/Projects/PrSentinel/AGENTS.md).
For the architectural design document, see the [Implementation Plan](file:///C:/Users/vedan/.gemini/antigravity/brain/15b401c6-faa2-4fc8-8770-296c04176592/pr_sentinel_implementation_plan.md).

