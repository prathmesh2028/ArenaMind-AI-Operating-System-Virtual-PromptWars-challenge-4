import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid

from app.database import Base, get_db
from app.main import app
from app.models import Role, User, Incident, Task, Prediction, Recommendation, CrowdMetric, Transport, Parking, Energy, Carbon

# Create in-memory SQLite database engine for test isolation
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    # Create all tables in memory
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        # Seed essential roles
        roles = {
            "ADMIN": Role(id=1, name="ADMIN", description="System administrator"),
            "OPERATIONS": Role(id=2, name="OPERATIONS", description="Operations Chief"),
            "VOLUNTEER": Role(id=3, name="VOLUNTEER", description="Field volunteer"),
            "FAN": Role(id=6, name="FAN", description="Spectator")
        }
        for r in roles.values():
            db.add(r)
        db.commit()

        # Seed test users
        users = [
            User(id="11111111-1111-1111-1111-111111111111", email="manager@fifa.com", display_name="Sarah Jenkins", role_id=2),
            User(id="22222222-2222-2222-2222-222222222222", email="volunteer1@fifa.com", display_name="Juan Alvarez", role_id=3),
            User(id="33333333-3333-3333-3333-333333333333", email="fan1@gmail.com", display_name="Alex Smith", role_id=6),
        ]
        for u in users:
            db.add(u)
        db.commit()
    finally:
        db.close()
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db():
    # Yield dynamic test session
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db):
    # Override get_db dependency injection in FastAPI routers
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
