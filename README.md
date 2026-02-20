# ClearView News Dashboard

> Understand what happened, how it's framed, and what's verified — fast.

A web application that shows trending news stories grouped by political lean (Left / Center / Right),
with transparent bias labels and professional fact-check links.

**Team:** Priyansh Vaghela · Daniel Martinez · Morya Odak  
**Course:** CSC 436 – Software Engineering, Spring 2026

---

## Current Sprint Status (Sprint 1 — as of 03/20/2026)

| Layer | Status |
|---|---|
| PostgreSQL schema (5 tables) | ✅ Done |
| Article ingestion (8 outlets via NewsAPI) | ✅ Done (manual trigger; cron pending) |
| TF-IDF story clustering | ✅ Done (~78% accuracy) |
| AllSides lean labeling (127 outlets) | ✅ Done |
| GET /stories endpoint | ✅ Done |
| GET /story/:id endpoint | ✅ Done |
| React dashboard UI | ✅ Done (mock data) |
| React story page UI | ✅ Done (mock data) |
| API ↔ Frontend wiring | 🔄 In Progress |
| Automated tests | 🔄 In Progress (scaffolded) |
| GET /story/:id/factchecks | ⏳ Sprint 2 |
| Fact-check panel UI | ⏳ Sprint 2 |

---

## Setup

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- A [NewsAPI](https://newsapi.org/) free API key

### 1. Clone & configure environment

```bash
git clone https://github.com/YOUR_USERNAME/clearview-news-dashboard.git
cd clearview-news-dashboard
cp backend/.env.example backend/.env
# Edit backend/.env — add your NEWSAPI_KEY and DATABASE_URL
```

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create the database
createdb clearview              # or use psql

# Run migrations
alembic upgrade head

# Seed AllSides outlet data
python scripts/seed_outlets.py

# Ingest articles (manual trigger)
python scripts/ingest.py

# Run clustering + labeling
python scripts/cluster_and_label.py

# Start the API server
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173

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
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── api/
│   │   │   ├── routes.py        # All API routes
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
│   │       ├── clustering.py    # TF-IDF story clustering
│   │       └── labeling.py      # AllSides lean labeling
│   ├── scripts/
│   │   ├── ingest.py            # Article ingestion (NewsAPI + RSS)
│   │   ├── cluster_and_label.py # Run clustering + labeling pipeline
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
│   │   │   ├── StoryCard.jsx    # Dashboard story card
│   │   │   ├── LeanBadge.jsx    # Left/Center/Right badge
│   │   │   └── LeanTooltip.jsx  # "Why this label?" tooltip
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx    # Main trending stories page
│   │   │   └── StoryPage.jsx    # Story detail + L/C/R columns
│   │   ├── hooks/
│   │   │   └── useApi.js        # Fetch wrapper with loading/error
│   │   └── services/
│   │       └── api.js           # API base URL + endpoints
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
  (TF-IDF)           ──────►│
                            ├── lean_labels
  [Labeling script]  ◄──────┤  outlets (AllSides)
  (AllSides CSV)     ──────►│
                            └── fact_checks (Sprint 2)
                                    │
                            [FastAPI /api/v1]
                                    │
                             [React Frontend]
```
