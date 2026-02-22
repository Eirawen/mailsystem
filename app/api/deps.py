from fastapi import Depends
from redis import Redis
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db_session, get_redis


def db_session_dep(db: Session = Depends(get_db_session)) -> Session:
    return db


def settings_dep(settings: Settings = Depends(get_settings)) -> Settings:
    return settings


def redis_dep(redis_client: Redis = Depends(get_redis)) -> Redis:
    return redis_client
