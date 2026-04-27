# ClearView News Dashboard

> Understand what happened, how it's framed, and what's verified — fast.

ClearView aggregates trending news stories from across the political spectrum, groups coverage by political lean (Left / Lean Left / Center / Lean Right / Right) using AllSides bias ratings, and surfaces fact-checks and source context for each story. When no professional fact-check exists, Claude AI (Anthropic) generates an analysis as a fallback.

**Live app:** [clearview-news-dashboard.vercel.app](https://clearview-news-dashboard.vercel.app)  
**API:** [clearview-backend-production.up.railway.app](https://clearview-backend-production.up.railway.app/health)

**Team:** Priyansh Vaghela · Daniel Martinez · Morya Odak  
**Course:** CSC 436 – Software Engineering, Spring 2026

---

## Sprint 3 Status (Final)

| Feature | Status |
|---|---|
| Deployment — Railway (backend) + Vercel (frontend) | ✅ Live |
| PostgreSQL on Railway (6 tables, 4 Alembic migrations) | ✅ Done |
| Article ingestion — 13 outlets across all 5 lean categories | ✅ Done |
| TF-IDF + entity-overlap clustering (~86% accuracy) | ✅ Done |
| AllSides lean labeling + tooltip | ✅ Done |
| Google Fact Check Tools API + per-story cache | ✅ Done |
| Claude AI fact-check fallback (`is_ai_generated` flag) | ✅ Done |
| WebCite source-search panel ("Related coverage") | ✅ Done |
| AI story summary per card | ✅ Done |
| NYT-style dashboard + story page UI | ✅ Done |
| Error boundary + mobile layout | ✅ Done |
| Backend tests (pytest) | ✅ 10 passing |
| Frontend tests (Vitest) | ✅ 25 passing |
| All 5 acceptance tests (AT-1 – AT-5) | ✅ Verified |

---

## Setup (local dev)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Python 3.11+
- Node.js 20+

### 1. Clone and start the database

```bash
git clone https://github.com/pgvaghela/clearview-news-dashboard.git
cd clearview-news-dashboard

docker compose up -d
cp backend/.env.example backend/.env
# Add your API keys to backend/.env (see Keys section below)
```

The default `DATABASE_URL` in `.env.example` connects to the Docker Compose Postgres on **localhost:5433** (avoids conflict with a local Postgres on 5432).

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

alembic upgrade head            # run all 4 migrations
python scripts/seed_outlets.py  # load AllSides bias data

python scripts/ingest.py              # fetch articles from NewsAPI
python scripts/cluster_and_label.py  # cluster + label + generate summaries
python scripts/run_factchecks.py     # fetch fact-checks (Google + Claude AI fallback)

uvicorn app.main:app --reload --port 8000 --reload-dir app
```

API docs: http://localhost:8000/docs

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173 — Vite proxies `/api` to `http://localhost:8000`.

### 4. Run tests

```bash
cd backend && pytest -v          # 10 backend tests
cd frontend && npm run test      # 25 frontend tests
```

### API Keys (backend/.env)

| Variable | Source | Required for |
|---|---|---|
| `NEWSAPI_KEY` | [newsapi.org](https://newsapi.org) | `ingest.py` |
| `GOOGLE_FACTCHECK_API_KEY` | [Google Cloud Console](https://console.cloud.google.com) | fact-check lookup |
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) | AI fact-check + summaries |
| `WEBCITE_API_KEY` | WebCite | related coverage panel |

Placeholder keys are detected and skip HTTP calls with a one-time warning — the API and UI boot without them.

---

## Architecture

```
  ┌─── EXTERNAL ────────────────────────────────────────────────┐
  │  NewsAPI    Google Fact Check API    Anthropic API (Claude)  │
  │  AllSides CSV                        WebCite API             │
  └─────────────────────────────────────────────────────────────┘
          │                    │
          ▼                    ▼
  ┌─── SYSTEM (Railway + Vercel) ───────────────────────────────┐
  │                                                              │
  │  [ingest.py]       ──►  PostgreSQL (Railway)                 │
  │  [cluster_and_label.py]  ├── articles                        │
  │    Step 1: TF-IDF clustering ── stories                      │
  │    Step 2: AllSides labeling ── lean_labels / outlets        │
  │    Step 3: AI summaries  ──────► stories.summary             │
  │  [run_factchecks.py] ────────── fact_checks                  │
  │                        └── webcite_story_cache               │
  │                                                              │
  │  FastAPI (Railway)   GET /api/v1/stories                     │
  │                      GET /api/v1/stories/:id                 │
  │                      GET /api/v1/stories/:id/factchecks      │
  │                      GET /health                             │
  │                                                              │
  │  React + Vite (Vercel)                                       │
  │    Dashboard — featured story, sidebar, story grid           │
  │    StoryPage — L/C/R columns, lean tooltip, fact-check panel │
  └─────────────────────────────────────────────────────────────┘
```

### Key design decisions

| Date | Decision | Why |
|---|---|---|
| 2026-02-20 | AllSides as sole bias source | Conflicting provider ratings |
| 2026-02-20 | No AI truth verdicts in Sprint 1 | User trust risk |
| 2026-02-25 | TF-IDF clustering | Fast, interpretable MVP |
| 2026-03-28 | Aggressive fact-check caching | 1,000/day Google quota |
| 2026-04-05 | WebCite as "Related coverage", not a verdict | Avoid conflating source search with fact-checks |
| 2026-04-26 | Claude AI fact-check fallback | Google returns no results for most breaking news |

---

## Project Structure

```
clearview/
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── api/routes.py
│   │   ├── core/config.py
│   │   ├── db/
│   │   │   ├── database.py
│   │   │   └── migrations/versions/   # 001–004
│   │   ├── models/models.py
│   │   ├── schemas/schemas.py
│   │   └── services/
│   │       ├── clustering.py
│   │       ├── labeling.py
│   │       ├── factchecks.py          # Google + Claude AI fallback
│   │       ├── summarize.py           # Claude AI story summaries
│   │       └── webcite.py
│   ├── scripts/
│   │   ├── ingest.py
│   │   ├── cluster_and_label.py       # Steps 1–3: cluster, label, summarize
│   │   ├── run_factchecks.py
│   │   └── seed_outlets.py
│   ├── tests/test_api.py              # 10 pytest tests
│   ├── data/allsides_outlets.csv
│   ├── requirements.txt
│   └── railway.toml
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ErrorBoundary.jsx
│   │   │   ├── FactCheckPanel.jsx
│   │   │   ├── LeanBadge.jsx
│   │   │   ├── LeanTooltip.jsx
│   │   │   ├── StoryCard.jsx
│   │   │   ├── StoryFactSources.jsx
│   │   │   ├── WebcitePanel.jsx
│   │   │   └── __tests__/            # 25 Vitest tests
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   └── StoryPage.jsx
│   │   ├── hooks/useApi.js
│   │   └── services/api.js
│   └── vite.config.js
└── README.md
```
