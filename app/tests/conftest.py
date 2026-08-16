import os
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.pool import NullPool

from app.main import app
from app.db.database import get_db
from app.core.config import settings

# Import Base from wherever it's defined and all models to ensure metadata is populated
from app.db.base import Base
from app.models import *

# Determine TEST_DATABASE_URL
if settings.TEST_DATABASE_URL:
    TEST_DATABASE_URL = settings.TEST_DATABASE_URL
else:
    # Safely parse the base URL and append _test to the database name
    base_url = make_url(settings.DATABASE_URL)
    test_db_name = f"{base_url.database}_test" if base_url.database else "test_db"
    TEST_DATABASE_URL = base_url.set(database=test_db_name).render_as_string(hide_password=False)

# Engine and Session factory for the test DB
engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    """
    Session-scoped fixture to create the test database (if it doesn't exist),
    create all tables before any tests run, and drop them when the test session ends.
    """
    url = make_url(TEST_DATABASE_URL)
    db_name = url.database
    
    # 1. Connect to the base server (without a specific DB) to CREATE DATABASE if needed
    server_url = url.set(database="")
    server_engine = create_async_engine(server_url, isolation_level="AUTOCOMMIT", poolclass=NullPool)
    async with server_engine.connect() as conn:
        await conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {db_name}"))
    await server_engine.dispose()

    # 2. Connect to the test DB and create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    yield  # Run all tests in the session
    
    try:
        # 3. Drop all tables after tests complete
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def db_session():
    """Yields a test database session."""
    async with TestingSessionLocal() as session:
        yield session

@pytest.fixture(autouse=True)
def override_get_db(db_session):
    """Overrides the FastAPI get_db dependency for every test."""
    async def _get_test_db():
        yield db_session
    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def client():
    """Provides an async HTTP client wrapping the FastAPI app."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest_asyncio.fixture
async def brand_client(client: AsyncClient):
    """
    Registers a dummy brand user, logs them in, and returns an AsyncClient 
    with the Authorization bearer token pre-set.
    """
    uid = uuid.uuid4().hex[:8]
    payload = {
        "email": f"brand_{uid}@example.com",
        "password": "Password123!",
        "name": f"Test Brand {uid}",
        "role": "brand"
    }
    
    # Register the user
    res = await client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201, f"Failed to register test brand: {res.text}"
    
    # Login to get access token (using OAuth2 form-data structure)
    login_data = {
        "email": payload["email"],
        "password": payload["password"]
    }
    res_login = await client.post("/api/v1/auth/login", json=login_data)
    assert res_login.status_code == 200, f"Failed to login test brand: {res_login.text}"
    token = res_login.json()["access_token"]
    
    # Return a pre-authenticated client
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"}
    ) as ac:
        yield ac

@pytest_asyncio.fixture
async def influencer_client(client: AsyncClient):
    """
    Registers a dummy influencer user, logs them in, and returns an AsyncClient 
    with the Authorization bearer token pre-set.
    """
    uid = uuid.uuid4().hex[:8]
    payload = {
        "email": f"influencer_{uid}@example.com",
        "password": "Password123!",
        "name": f"Test Influencer {uid}",
        "role": "influencer"
    }
    
    # Register the user
    res = await client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201, f"Failed to register test influencer: {res.text}"
    
    # Login to get access token
    login_data = {
        "email": payload["email"],
        "password": payload["password"]
    }
    res_login = await client.post("/api/v1/auth/login", json=login_data)
    assert res_login.status_code == 200, f"Failed to login test influencer: {res_login.text}"
    token = res_login.json()["access_token"]
    
    # Return a pre-authenticated client
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"}
    ) as ac:
        yield ac
