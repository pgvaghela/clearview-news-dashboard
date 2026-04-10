# ClearView News Dashboard

> Understand what happened, how it's framed, and what's verified — fast.

A web application that shows trending news stories grouped by political lean (Left / Center / Right),
with transparent bias labels and professional fact-check links.

**Team:** Priyansh Vaghela · Daniel Martinez · Morya Odak  
**Course:** CSC 436 – Software Engineering, Spring 2026

---

## Current Sprint Status (Sprint 2 — as of 03/31/2026)

| Layer | Status |
|---|---|
| PostgreSQL schema (5 tables) | ✅ Done |
| Article ingestion (8 outlets via NewsAPI) | ✅ Done (manual trigger; cron pending) |
| TF-IDF + entity-overlap clustering | ✅ Done (~86% accuracy) |
| AllSides lean labeling | ✅ Done |
| GET /api/v1/stories & GET /api/v1/stories/:id | ✅ Done |
| API ↔ Frontend wiring (dashboard + story page) | ✅ Done |
| Google Fact Check Tools API + `fact_checks` cache | ✅ Done (`services/factchecks.py`) |
| GET /api/v1/stories/:id/factchecks | ✅ Done |
| Fact-check panel UI (`FactCheckPanel`) | ✅ Done |
| Pipeline script `run_factchecks.py` | ✅ Done (cron after ingest + cluster) |
| Backend tests (pytest) | ✅ Done (7 API tests) |
| Frontend tests (Vitest) | ✅ Done (14 component tests) |

---

## Setup

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (recommended — gives everyone the same Postgres with **no personal password**)
- Python 3.11+
- Node.js 20+
- Optional: [NewsAPI](https://newsapi.org/) and [Google Fact Check Tools](https://developers.google.com/fact-check/tools/api) keys in `backend/.env` for ingestion and fact-check scripts (placeholders are fine to boot the API)

### 1. Clone, database, and environment

```bash
git clone https://github.com/YOUR_USERNAME/clearview-news-dashboard.git
cd clearview-news-dashboard

# Start Postgres (fixed dev user/password — see docker-compose.yml; nothing to type)
docker compose up -d

cp backend/.env.example backend/.env
# Optional: edit backend/.env and replace NEWSAPI_KEY / GOOGLE_FACTCHECK_API_KEY when you run ingest / fact checks
```

The default **`DATABASE_URL`** in `.env.example` matches the Compose service (`clearview` / `clearview`). You do **not** need your own macOS Postgres password.

If port **5432** is already in use, stop your other Postgres or change the host port in `docker-compose.yml` and set `DATABASE_URL` accordingly.

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run migrations (database "clearview" is created by Docker)
alembic upgrade head

# Seed AllSides outlet data
python scripts/seed_outlets.py

# Ingest articles (manual trigger)
python scripts/ingest.py

# Run clustering + labeling
python scripts/cluster_and_label.py

# Fetch and cache fact checks for stories (manual; add to cron after clustering)
python scripts/run_factchecks.py

# Start the API server (--reload-dir avoids watching .venv if it lives under backend/)
uvicorn app.main:app --reload --port 8000 --reload-dir app
```

API docs: http://localhost:8000/docs

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173 — the Vite dev server proxies `/api` to `http://localhost:8000`, so run the backend at the same time for live data.

### Without Docker

If you use your own PostgreSQL, set **`DATABASE_URL`** in `backend/.env` to a URL your server accepts (for example your OS user over a Unix socket, or `user:password@localhost:5432/clearview`). The repo default is tuned for `docker compose`.

### 4. Run tests

```bash
# Backend
cd backend && pytest -v

# Frontend
cd frontend && npm run test
```

---

## Project Structure

```
clearview/
├── docker-compose.yml          # Local Postgres (dev credentials; see file)
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── api/
│   │   │   └── routes.py        # All API routes
│   │   ├── core/
│   │   │   └── config.py        # Settings (env vars)
│   │   ├── db/
│   │   │   ├── database.py      # SQLAlchemy engine + session
│   │   │   └── migrations/      # Alembic migrations
│   │   ├── models/
│   │   │   └── models.py        # SQLAlchemy ORM models
│   │   ├── schemas/
│   │   │   └── schemas.py       # Pydantic response schemas
│   │   └── services/
│   │       ├── clustering.py    # TF-IDF + entity overlap clustering
│   │       ├── labeling.py      # AllSides lean labeling
│   │       └── factchecks.py    # Google Fact Check API + DB cache
│   ├── scripts/
│   │   ├── ingest.py            # Article ingestion (NewsAPI + RSS)
│   │   ├── cluster_and_label.py # Clustering + labeling pipeline
│   │   ├── run_factchecks.py    # Fact-check fetch for active stories
│   │   └── seed_outlets.py      # Load AllSides CSV into DB
│   ├── tests/
│   │   └── test_api.py          # API endpoint tests
│   ├── data/
│   │   └── allsides_outlets.csv # AllSides bias dataset
│   ├── alembic.ini
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── StoryCard.jsx
│   │   │   ├── LeanBadge.jsx
│   │   │   ├── LeanTooltip.jsx
│   │   │   └── FactCheckPanel.jsx
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   └── StoryPage.jsx
│   │   ├── hooks/
│   │   │   └── useApi.js
│   │   └── services/
│   │       └── api.js
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
└── README.md
```

---

## Architecture

```
NewsAPI / RSS feeds
        │
        ▼
  [Ingestion script]  ──►  PostgreSQL
  (every 60 min)            │
                            ├── articles
  [Clustering script] ◄─────┤  stories
  (TF-IDF + entities)──────►│
                            ├── lean_labels
  [Labeling script]  ◄──────┤  outlets (AllSides)
  (AllSides CSV)     ──────►│
                            └── fact_checks
                                    ▲
  [run_factchecks.py] ─ Google Fact Check Tools API
                                    │
                            [FastAPI /api/v1]
                                    │
                             [React Frontend]
```
