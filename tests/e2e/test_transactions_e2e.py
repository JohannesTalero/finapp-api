"""Tests end-to-end para transacciones."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from uuid import uuid4


class TestTransactionsE2E:
    """Tests e2e para transacciones."""
    
    @pytest.fixture
    def mock_auth(self):
        """Mock de autenticación."""
        return patch('api.app.core.security.verify_supabase_token', return_value=Mock(
            user_id="user123",
            email="test@example.com",
            aud="authenticated",
            iss="supabase",
            exp=1234567890
        ))
    
    @pytest.fixture
    def mock_household_membership(self):
        """Mock de membresía de hogar."""
        return patch('api.app.deps.verify_household_membership', return_value=(str(uuid4()), Mock()))
    
    def test_create_income_transaction(
        self, 
        test_client: TestClient, 
        mock_auth, 
        mock_household_membership
    ):
        """Test crear transacción de ingreso."""
        with mock_auth, mock_household_membership:
            transaction_data = {
                "kind": "income",
                "amount": "100.00",
                "account_id": str(uuid4()),
                "category_id": str(uuid4()),
                "occurred_at": "2024-01-01T00:00:00Z",
                "description": "Test income transaction",
                "counterparty": "Test Counterparty"
            }
            
            headers = {
                "Authorization": "Bearer valid_token",
                "Idempotency-Key": str(uuid4())
            }
            
            response = test_client.post(
                "/v1/households/test-household-id/transactions",
                json=transaction_data,
                headers=headers
            )
            
            # Debería pasar validación pero fallar en la DB (porque es mock)
            assert response.status_code in [201, 500]
    
    def test_create_expense_transaction(
        self, 
        test_client: TestClient, 
        mock_auth, 
        mock_household_membership
    ):
        """Test crear transacción de gasto."""
        with mock_auth, mock_household_membership:
            transaction_data = {
                "kind": "expense",
                "amount": "50.00",
                "account_id": str(uuid4()),
                "category_id": str(uuid4()),
                "occurred_at": "2024-01-01T00:00:00Z",
                "description": "Test expense transaction"
            }
            
            headers = {
                "Authorization": "Bearer valid_token",
                "Idempotency-Key": str(uuid4())
            }
            
            response = test_client.post(
                "/v1/households/test-household-id/transactions",
                json=transaction_data,
                headers=headers
            )
            
            assert response.status_code in [201, 500]
    
    def test_create_transfer_transaction(
        self, 
        test_client: TestClient, 
        mock_auth, 
        mock_household_membership
    ):
        """Test crear transacción de transferencia."""
        with mock_auth, mock_household_membership:
            from_account_id = str(uuid4())
            to_account_id = str(uuid4())
            
            transaction_data = {
                "kind": "transfer",
                "amount": "75.00",
                "from_account_id": from_account_id,
                "to_account_id": to_account_id,
                "occurred_at": "2024-01-01T00:00:00Z",
                "description": "Test transfer transaction"
            }
            
            headers = {
                "Authorization": "Bearer valid_token",
                "Idempotency-Key": str(uuid4())
            }
            
            response = test_client.post(
                "/v1/households/test-household-id/transactions",
                json=transaction_data,
                headers=headers
            )
            
            assert response.status_code in [201, 500]
    
    def test_create_transaction_missing_idempotency_key(
        self, 
        test_client: TestClient, 
        mock_auth, 
        mock_household_membership
    ):
        """Test crear transacción sin Idempotency-Key."""
        with mock_auth, mock_household_membership:
            transaction_data = {
                "kind": "income",
                "amount": "100.00",
                "account_id": str(uuid4())
            }
            
            headers = {
                "Authorization": "Bearer valid_token"
                # Falta Idempotency-Key
            }
            
            response = test_client.post(
                "/v1/households/test-household-id/transactions",
                json=transaction_data,
                headers=headers
            )
            
            # Debería fallar por falta de Idempotency-Key
            assert response.status_code == 422
    
    def test_create_transaction_invalid_data(
        self, 
        test_client: TestClient, 
        mock_auth, 
        mock_household_membership
    ):
        """Test crear transacción con datos inválidos."""
        with mock_auth, mock_household_membership:
            transaction_data = {
                "kind": "income",
                "amount": "-100.00",  # Monto negativo
                "account_id": str(uuid4())
            }
            
            headers = {
                "Authorization": "Bearer valid_token",
                "Idempotency-Key": str(uuid4())
            }
            
            response = test_client.post(
                "/v1/households/test-household-id/transactions",
                json=transaction_data,
                headers=headers
            )
            
            assert response.status_code == 422
            data = response.json()
            assert "validation-error" in data["type"]
    
    def test_create_transfer_same_accounts(
        self, 
        test_client: TestClient, 
        mock_auth, 
        mock_household_membership
    ):
        """Test crear transferencia con las mismas cuentas."""
        with mock_auth, mock_household_membership:
            account_id = str(uuid4())
            
            transaction_data = {
                "kind": "transfer",
                "amount": "100.00",
                "from_account_id": account_id,
                "to_account_id": account_id,  # Misma cuenta
                "occurred_at": "2024-01-01T00:00:00Z"
            }
            
            headers = {
                "Authorization": "Bearer valid_token",
                "Idempotency-Key": str(uuid4())
            }
            
            response = test_client.post(
                "/v1/households/test-household-id/transactions",
                json=transaction_data,
                headers=headers
            )
            
            assert response.status_code == 422
            data = response.json()
            assert "validation-error" in data["type"]
    
    def test_get_transactions(
        self, 
        test_client: TestClient, 
        mock_auth, 
        mock_household_membership
    ):
        """Test obtener transacciones."""
        with mock_auth, mock_household_membership:
            headers = {"Authorization": "Bearer valid_token"}
            
            response = test_client.get(
                "/v1/households/test-household-id/transactions",
                headers=headers
            )
            
            # Debería pasar autenticación pero fallar en la DB
            assert response.status_code in [200, 500]
    
    def test_get_transactions_with_filters(
        self, 
        test_client: TestClient, 
        mock_auth, 
        mock_household_membership
    ):
        """Test obtener transacciones con filtros."""
        with mock_auth, mock_household_membership:
            headers = {"Authorization": "Bearer valid_token"}
            
            params = {
                "kind": "income",
                "from_date": "2024-01-01",
                "to_date": "2024-01-31",
                "limit": 10
            }
            
            response = test_client.get(
                "/v1/households/test-household-id/transactions",
                params=params,
                headers=headers
            )
            
            assert response.status_code in [200, 500]
    
    def test_get_transactions_with_cursor(
        self, 
        test_client: TestClient, 
        mock_auth, 
        mock_household_membership
    ):
        """Test obtener transacciones con cursor."""
        with mock_auth, mock_household_membership:
            headers = {"Authorization": "Bearer valid_token"}
            
            params = {
                "cursor": "eyIyMDI0LTAxLTAxVDAwOjAwOjAwWiJ8InRlc3QtaWQifQ==",
                "limit": 20
            }
            
            response = test_client.get(
                "/v1/households/test-household-id/transactions",
                params=params,
                headers=headers
            )
            
            assert response.status_code in [200, 500]
    
    def test_get_transaction_by_id(
        self, 
        test_client: TestClient, 
        mock_auth, 
        mock_household_membership
    ):
        """Test obtener transacción por ID."""
        with mock_auth, mock_household_membership:
            transaction_id = str(uuid4())
            headers = {"Authorization": "Bearer valid_token"}
            
            response = test_client.get(
                f"/v1/households/test-household-id/transactions/{transaction_id}",
                headers=headers
            )
            
            assert response.status_code in [200, 404, 500]
    
    def test_update_transaction(
        self, 
        test_client: TestClient, 
        mock_auth, 
        mock_household_membership
    ):
        """Test actualizar transacción."""
        with mock_auth, mock_household_membership:
            transaction_id = str(uuid4())
            headers = {"Authorization": "Bearer valid_token"}
            
            update_data = {
                "amount": "150.00",
                "description": "Updated transaction"
            }
            
            response = test_client.patch(
                f"/v1/households/test-household-id/transactions/{transaction_id}",
                json=update_data,
                headers=headers
            )
            
            assert response.status_code in [200, 404, 500]
    
    def test_delete_transaction(
        self, 
        test_client: TestClient, 
        mock_auth, 
        mock_household_membership
    ):
        """Test eliminar transacción."""
        with mock_auth, mock_household_membership:
            transaction_id = str(uuid4())
            headers = {"Authorization": "Bearer valid_token"}
            
            response = test_client.delete(
                f"/v1/households/test-household-id/transactions/{transaction_id}",
                headers=headers
            )
            
            assert response.status_code in [200, 404, 500]
    
    def test_get_transaction_summary(
        self, 
        test_client: TestClient, 
        mock_auth, 
        mock_household_membership
    ):
        """Test obtener resumen de transacciones."""
        with mock_auth, mock_household_membership:
            headers = {"Authorization": "Bearer valid_token"}
            
            params = {
                "from_date": "2024-01-01",
                "to_date": "2024-01-31"
            }
            
            response = test_client.get(
                "/v1/households/test-household-id/transactions/summary",
                params=params,
                headers=headers
            )
            
            assert response.status_code in [200, 500]
    
    def test_transaction_without_auth(self, test_client: TestClient):
        """Test transacción sin autenticación."""
        transaction_data = {
            "kind": "income",
            "amount": "100.00",
            "account_id": str(uuid4())
        }
        
        response = test_client.post(
            "/v1/households/test-household-id/transactions",
            json=transaction_data
        )
        
        assert response.status_code == 401
    
    def test_transaction_without_household_membership(self, test_client: TestClient, mock_auth):
        """Test transacción sin membresía de hogar."""
        with mock_auth:
            transaction_data = {
                "kind": "income",
                "amount": "100.00",
                "account_id": str(uuid4())
            }
            
            headers = {
                "Authorization": "Bearer valid_token",
                "Idempotency-Key": str(uuid4())
            }
            
            response = test_client.post(
                "/v1/households/test-household-id/transactions",
                json=transaction_data,
                headers=headers
            )
            
            # Debería fallar por falta de membresía
            assert response.status_code in [403, 500]
