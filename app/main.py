from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routes_analytics import router as analytics_router
from app.api.routes_bulk import router as bulk_router
from app.api.routes_emails import router as emails_router
from app.api.routes_send import router as send_router
from app.api.routes_webhooks import router as webhooks_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.base import Base
from app.db.session import get_engine, get_redis

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=get_engine())


@app.get("/health/live")
def health_live():
    return {"status": "ok"}


@app.get("/health/ready")
def health_ready():
    db_ok = False
    redis_ok = False
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    try:
        redis_ok = bool(get_redis().ping())
    except Exception:
        redis_ok = False

    return {"status": "ok" if db_ok and redis_ok else "degraded", "db": db_ok, "redis": redis_ok}


app.include_router(send_router)
app.include_router(bulk_router)
app.include_router(webhooks_router)
app.include_router(emails_router)
app.include_router(analytics_router)
