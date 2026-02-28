from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings

app = FastAPI(
    title="ClearView News Dashboard API",
    description=(
        "Backend API for ClearView — trending news stories grouped by political lean "
        "with transparent bias labels and fact-check links."
    ),
    version="0.1.0",
)

# Allow the React dev server to call the API during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=settings.API_PREFIX)


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}
