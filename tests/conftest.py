"""Configuración de tests para FinApp API."""

import pytest
import asyncio
from typing import Generator, AsyncGenerator
from unittest.mock import Mock, AsyncMock
from uuid import uuid4
from fastapi.testclient import TestClient
from httpx import AsyncClient

from api.app.main import app
from api.app.core.config import Settings
from api.app.core.security import User
from api.app.db.supabase_client import SupabaseClient


# Configuración de tests
@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Crear event loop para tests asíncronos."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> Settings:
    """Configuración para tests."""
    return Settings(
        supabase_url="https://test.supabase.co",
        supabase_anon_key="test-anon-key",
        supabase_service_role_key="test-service-key",
        project_env="test",
        log_level="DEBUG",
        cors_origins=["http://localhost:3000"],
        rate_limit_requests=100,  # Más permisivo para tests
        rate_limit_burst=200,
        default_page_size=20,
        max_page_size=100,
        jwt_algorithm="HS256",
        access_token_expire_minutes=30,
        refresh_token_expire_days=7
    )


@pytest.fixture
def mock_user() -> User:
    """Usuario mock para tests."""
    return User(
        id=uuid4(),
        email="test@example.com",
        roles={}
    )


@pytest.fixture
def mock_household_id() -> str:
    """ID de hogar mock para tests."""
    return str(uuid4())


@pytest.fixture
def mock_supabase_client() -> Mock:
    """Cliente Supabase mock."""
    client = Mock(spec=SupabaseClient)
    client.client = Mock()
    client.service_client = Mock()
    client.with_user_token = Mock(return_value=Mock())
    return client


@pytest.fixture
def test_client(test_settings: Settings) -> TestClient:
    """Cliente de test para FastAPI."""
    # Mockear configuración
    app.dependency_overrides[Settings] = lambda: test_settings
    
    return TestClient(app)


@pytest.fixture
async def async_client(test_settings: Settings) -> AsyncGenerator[AsyncClient, None]:
    """Cliente asíncrono para tests."""
    # Mockear configuración
    app.dependency_overrides[Settings] = lambda: test_settings
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_transaction_data() -> dict:
    """Datos de transacción mock."""
    return {
        "id": str(uuid4()),
        "household_id": str(uuid4()),
        "kind": "income",
        "amount": "100.00",
        "account_id": str(uuid4()),
        "category_id": str(uuid4()),
        "occurred_at": "2024-01-01T00:00:00Z",
        "description": "Test transaction",
        "counterparty": "Test Counterparty",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def mock_goal_data() -> dict:
    """Datos de meta mock."""
    return {
        "id": str(uuid4()),
        "household_id": str(uuid4()),
        "name": "Test Goal",
        "target_amount": "1000.00",
        "current_amount": "100.00",
        "target_date": "2024-12-31",
        "description": "Test goal description",
        "priority": "medium",
        "is_recurring": False,
        "recurrence_pattern": None,
        "status": "active",
        "completed_at": None,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def mock_obligation_data() -> dict:
    """Datos de obligación mock."""
    return {
        "id": str(uuid4()),
        "household_id": str(uuid4()),
        "name": "Test Obligation",
        "total_amount": "500.00",
        "outstanding_amount": "500.00",
        "due_date": "2024-06-30",
        "description": "Test obligation description",
        "priority": "medium",
        "creditor": "Test Creditor",
        "is_recurring": False,
        "recurrence_pattern": None,
        "status": "active",
        "completed_at": None,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def mock_account_data() -> dict:
    """Datos de cuenta mock."""
    return {
        "id": str(uuid4()),
        "household_id": str(uuid4()),
        "name": "Test Account",
        "account_type": "checking",
        "currency": "USD",
        "balance": "1000.00",
        "description": "Test account description",
        "color": "#FF0000",
        "icon": "bank",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def mock_category_data() -> dict:
    """Datos de categoría mock."""
    return {
        "id": str(uuid4()),
        "household_id": str(uuid4()),
        "name": "Test Category",
        "kind": "income",
        "description": "Test category description",
        "color": "#00FF00",
        "icon": "money",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def mock_household_data() -> dict:
    """Datos de hogar mock."""
    return {
        "id": str(uuid4()),
        "name": "Test Household",
        "description": "Test household description",
        "owner_id": str(uuid4()),
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def mock_idempotency_data() -> dict:
    """Datos de idempotencia mock."""
    return {
        "id": str(uuid4()),
        "key": "test-idempotency-key",
        "user_id": str(uuid4()),
        "household_id": str(uuid4()),
        "request_hash": "test-hash",
        "response_status": 201,
        "response_body": {"success": True},
        "created_at": "2024-01-01T00:00:00Z"
    }


# Fixtures para mockear dependencias
@pytest.fixture
def mock_get_current_user(mock_user: User):
    """Mock para get_current_user."""
    return Mock(return_value=mock_user)


@pytest.fixture
def mock_verify_household_membership(mock_household_id: str, mock_user: User):
    """Mock para verify_household_membership."""
    return Mock(return_value=(mock_household_id, mock_user))


@pytest.fixture
def mock_verify_household_admin(mock_household_id: str, mock_user: User):
    """Mock para verify_household_admin."""
    return Mock(return_value=(mock_household_id, mock_user))


@pytest.fixture
def mock_verify_household_owner(mock_household_id: str, mock_user: User):
    """Mock para verify_household_owner."""
    return Mock(return_value=(mock_household_id, mock_user))


# Fixtures para datos de test específicos
@pytest.fixture
def sample_transaction_create_data() -> dict:
    """Datos para crear transacción."""
    return {
        "kind": "income",
        "amount": "100.00",
        "account_id": str(uuid4()),
        "category_id": str(uuid4()),
        "occurred_at": "2024-01-01T00:00:00Z",
        "description": "Test income transaction",
        "counterparty": "Test Counterparty"
    }


@pytest.fixture
def sample_goal_create_data() -> dict:
    """Datos para crear meta."""
    return {
        "name": "Test Goal",
        "target_amount": "1000.00",
        "current_amount": "0.00",
        "target_date": "2024-12-31",
        "description": "Test goal description",
        "priority": "medium",
        "is_recurring": False
    }


@pytest.fixture
def sample_obligation_create_data() -> dict:
    """Datos para crear obligación."""
    return {
        "name": "Test Obligation",
        "total_amount": "500.00",
        "outstanding_amount": "500.00",
        "due_date": "2024-06-30",
        "description": "Test obligation description",
        "priority": "medium",
        "creditor": "Test Creditor",
        "is_recurring": False
    }


@pytest.fixture
def sample_contribution_data() -> dict:
    """Datos para crear aporte."""
    return {
        "amount": "50.00",
        "source_account_id": str(uuid4()),
        "occurred_at": "2024-01-01T00:00:00Z",
        "description": "Test contribution"
    }


@pytest.fixture
def sample_payment_data() -> dict:
    """Datos para crear pago."""
    return {
        "amount": "25.00",
        "from_account_id": str(uuid4()),
        "occurred_at": "2024-01-01T00:00:00Z",
        "description": "Test payment"
    }


# Configuración de pytest
def pytest_configure(config):
    """Configuración de pytest."""
    config.addinivalue_line(
        "markers", "unit: marca tests unitarios"
    )
    config.addinivalue_line(
        "markers", "e2e: marca tests end-to-end"
    )
    config.addinivalue_line(
        "markers", "integration: marca tests de integración"
    )
    config.addinivalue_line(
        "markers", "slow: marca tests lentos"
    )


def pytest_collection_modifyitems(config, items):
    """Modificar items de colección de tests."""
    for item in items:
        # Marcar tests lentos
        if "slow" in item.keywords:
            item.add_marker(pytest.mark.slow)
        
        # Marcar tests unitarios por ubicación
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        
        # Marcar tests e2e por ubicación
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
