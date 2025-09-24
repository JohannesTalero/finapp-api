"""Tests unitarios para servicio de idempotencia."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
from decimal import Decimal

from api.app.services.idempotency_service import IdempotencyService
from api.app.core.errors import IdempotencyError


class TestIdempotencyService:
    """Tests para servicio de idempotencia."""
    
    @pytest.fixture
    def service(self):
        """Servicio de idempotencia."""
        service = IdempotencyService()
        service.client = Mock()
        return service
    
    @pytest.fixture
    def sample_request_body(self):
        """Cuerpo de request de ejemplo."""
        return {
            "kind": "income",
            "amount": "100.00",
            "account_id": str(uuid4()),
            "description": "Test transaction"
        }
    
    @pytest.fixture
    def sample_user_id(self):
        """ID de usuario de ejemplo."""
        return uuid4()
    
    @pytest.fixture
    def sample_household_id(self):
        """ID de hogar de ejemplo."""
        return uuid4()
    
    def test_hash_request_body(self, service, sample_request_body):
        """Test generación de hash del cuerpo del request."""
        hash1 = service._hash_request_body(sample_request_body)
        hash2 = service._hash_request_body(sample_request_body)
        
        # Hash debe ser consistente
        assert hash1 == hash2
        assert isinstance(hash1, str)
        assert len(hash1) == 64  # SHA256 hash length
    
    def test_hash_request_body_different_order(self, service):
        """Test que el hash es consistente independientemente del orden."""
        body1 = {"a": 1, "b": 2, "c": 3}
        body2 = {"c": 3, "a": 1, "b": 2}
        
        hash1 = service._hash_request_body(body1)
        hash2 = service._hash_request_body(body2)
        
        # Hash debe ser igual independientemente del orden
        assert hash1 == hash2
    
    def test_hash_request_body_different_values(self, service):
        """Test que diferentes valores generan diferentes hashes."""
        body1 = {"amount": "100.00"}
        body2 = {"amount": "200.00"}
        
        hash1 = service._hash_request_body(body1)
        hash2 = service._hash_request_body(body2)
        
        # Hash debe ser diferente
        assert hash1 != hash2
    
    @pytest.mark.asyncio
    async def test_check_idempotency_no_existing_request(
        self, 
        service, 
        sample_request_body, 
        sample_user_id, 
        sample_household_id
    ):
        """Test cuando no existe request previo."""
        # Configurar mock
        service.client.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        
        # Llamar función
        is_duplicate, cached_response = await service.check_idempotency(
            key="test-key",
            user_id=sample_user_id,
            household_id=sample_household_id,
            request_body=sample_request_body
        )
        
        # Verificar
        assert is_duplicate is False
        assert cached_response is None
    
    @pytest.mark.asyncio
    async def test_check_idempotency_matching_hash(
        self, 
        service, 
        sample_request_body, 
        sample_user_id, 
        sample_household_id
    ):
        """Test cuando existe request con hash coincidente."""
        # Configurar mock
        request_hash = service._hash_request_body(sample_request_body)
        existing_request = {
            "key": "test-key",
            "user_id": str(sample_user_id),
            "household_id": str(sample_household_id),
            "request_hash": request_hash,
            "response_status": 201,
            "response_body": {"success": True, "id": "123"}
        }
        
        service.client.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = [existing_request]
        
        # Llamar función
        is_duplicate, cached_response = await service.check_idempotency(
            key="test-key",
            user_id=sample_user_id,
            household_id=sample_household_id,
            request_body=sample_request_body
        )
        
        # Verificar
        assert is_duplicate is True
        assert cached_response == {"success": True, "id": "123"}
    
    @pytest.mark.asyncio
    async def test_check_idempotency_conflicting_hash(
        self, 
        service, 
        sample_request_body, 
        sample_user_id, 
        sample_household_id
    ):
        """Test cuando existe request con hash diferente."""
        # Configurar mock
        existing_request = {
            "key": "test-key",
            "user_id": str(sample_user_id),
            "household_id": str(sample_household_id),
            "request_hash": "different-hash",
            "response_status": 201,
            "response_body": {"success": True, "id": "123"}
        }
        
        service.client.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = [existing_request]
        
        # Llamar función
        with pytest.raises(IdempotencyError) as exc_info:
            await service.check_idempotency(
                key="test-key",
                user_id=sample_user_id,
                household_id=sample_household_id,
                request_body=sample_request_body
            )
        
        # Verificar
        assert "test-key" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_store_idempotency_result(
        self, 
        service, 
        sample_request_body, 
        sample_user_id, 
        sample_household_id
    ):
        """Test almacenar resultado de idempotencia."""
        # Configurar mock
        service.client.table.return_value.insert.return_value.execute.return_value = Mock()
        
        # Llamar función
        await service.store_idempotency_result(
            key="test-key",
            user_id=sample_user_id,
            household_id=sample_household_id,
            request_body=sample_request_body,
            response_status=201,
            response_body={"success": True, "id": "123"}
        )
        
        # Verificar que se llamó insert
        service.client.table.assert_called_with("idempotency_requests")
        service.client.table.return_value.insert.assert_called_once()
        
        # Verificar datos insertados
        insert_data = service.client.table.return_value.insert.call_args[0][0]
        assert insert_data["key"] == "test-key"
        assert insert_data["user_id"] == str(sample_user_id)
        assert insert_data["household_id"] == str(sample_household_id)
        assert insert_data["response_status"] == 201
        assert insert_data["response_body"] == {"success": True, "id": "123"}
    
    @pytest.mark.asyncio
    async def test_cleanup_old_requests(self, service):
        """Test limpieza de requests antiguos."""
        # Configurar mock
        service.client.table.return_value.delete.return_value.lt.return_value.execute.return_value.data = [
            {"id": "1"}, {"id": "2"}, {"id": "3"}
        ]
        
        # Llamar función
        deleted_count = await service.cleanup_old_requests(days=30)
        
        # Verificar
        assert deleted_count == 3
        service.client.table.assert_called_with("idempotency_requests")
        service.client.table.return_value.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_old_requests_no_data(self, service):
        """Test limpieza cuando no hay datos."""
        # Configurar mock
        service.client.table.return_value.delete.return_value.lt.return_value.execute.return_value.data = []
        
        # Llamar función
        deleted_count = await service.cleanup_old_requests(days=30)
        
        # Verificar
        assert deleted_count == 0


class TestIdempotencyIntegration:
    """Tests de integración para idempotencia."""
    
    @pytest.mark.asyncio
    async def test_full_idempotency_flow(self):
        """Test flujo completo de idempotencia."""
        service = IdempotencyService()
        service.client = Mock()
        
        user_id = uuid4()
        household_id = uuid4()
        request_body = {"amount": "100.00", "kind": "income"}
        
        # Primera llamada - no debe existir
        service.client.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        
        is_duplicate, cached_response = await service.check_idempotency(
            key="test-key",
            user_id=user_id,
            household_id=household_id,
            request_body=request_body
        )
        
        assert is_duplicate is False
        assert cached_response is None
        
        # Almacenar resultado
        service.client.table.return_value.insert.return_value.execute.return_value = Mock()
        
        await service.store_idempotency_result(
            key="test-key",
            user_id=user_id,
            household_id=household_id,
            request_body=request_body,
            response_status=201,
            response_body={"id": "123", "amount": "100.00"}
        )
        
        # Segunda llamada - debe encontrar resultado cacheado
        request_hash = service._hash_request_body(request_body)
        existing_request = {
            "key": "test-key",
            "user_id": str(user_id),
            "household_id": str(household_id),
            "request_hash": request_hash,
            "response_status": 201,
            "response_body": {"id": "123", "amount": "100.00"}
        }
        
        service.client.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = [existing_request]
        
        is_duplicate, cached_response = await service.check_idempotency(
            key="test-key",
            user_id=user_id,
            household_id=household_id,
            request_body=request_body
        )
        
        assert is_duplicate is True
        assert cached_response == {"id": "123", "amount": "100.00"}
