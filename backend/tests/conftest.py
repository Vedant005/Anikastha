import os
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["GITHUB_WEBHOOK_SECRET"] = "test_webhook_secret_key_123"
os.environ["GITHUB_APP_ID"] = "12345"

from app.api.deps import get_arq_pool, get_db
from app.core.database import Base
from app.main import app

# Test SQLite Engine
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    echo=False,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def rsa_key_pair():
    """Generate ephemeral RSA 2048-bit key pair for GitHub App JWT testing."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    pem_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_key = private_key.public_key()
    return pem_bytes, public_key


@pytest.fixture(autouse=True)
async def setup_test_db():
    """Create all tables in memory before each test and drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture
def mock_arq_pool():
    """Mock ARQ Redis connection pool."""
    pool = AsyncMock()
    pool.enqueue_job = AsyncMock(return_value=MagicMock(job_id="mock_job_123"))
    return pool


@pytest.fixture
async def client(db_session: AsyncSession, mock_arq_pool) -> AsyncGenerator[AsyncClient, None]:
    """Test HTTP client with overridden DB session and ARQ queue dependencies."""

    async def override_get_db():
        yield db_session

    async def override_get_arq_pool():
        return mock_arq_pool

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_arq_pool] = override_get_arq_pool

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()
