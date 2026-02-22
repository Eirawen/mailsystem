import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_mailsystem.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("WEBHOOK_SECRET_MOCK", "test-secret")
os.environ.setdefault("WEBHOOK_SECRET_SMTP", "test-secret")

from app.api.deps import db_session_dep, redis_dep
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_engine
from app.domain.models import Template, Tenant
from app.main import app


class DummyRedis:
    def __init__(self):
        self.store = {}

    def incr(self, key):
        self.store[key] = self.store.get(key, 0) + 1
        return self.store[key]

    def expire(self, key, ttl):
        return True

    def ping(self):
        return True


@pytest.fixture()
def client(tmp_path):
    db_path = tmp_path / "test.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    get_settings.cache_clear()
    get_engine.cache_clear()

    engine = create_engine(os.environ["DATABASE_URL"], future=True)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as session:
        session.add(Tenant(id="tenant-1", name="Tenant 1", status="active"))
        session.add(
            Template(
                id="tpl-1",
                tenant_id="tenant-1",
                name="welcome",
                version=1,
                subject_template="Hello {{ name }}",
                html_template="<p>Hi {{ name }}</p>",
                text_template=None,
                is_active=True,
            )
        )
        session.commit()

    def override_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[db_session_dep] = override_db
    app.dependency_overrides[redis_dep] = lambda: DummyRedis()

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
