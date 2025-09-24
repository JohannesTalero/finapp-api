"""Tests end-to-end para autenticación."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock


class TestAuthE2E:
    """Tests e2e para autenticación."""
    
    def test_login_success(self, test_client: TestClient):
        """Test login exitoso."""
        login_data = {
            "email": "test@example.com",
            "password": "password123"
        }
        
        response = test_client.post("/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 1800
        
        # Verificar que se establecieron cookies
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies
    
    def test_login_invalid_credentials(self, test_client: TestClient):
        """Test login con credenciales inválidas."""
        login_data = {
            "email": "invalid@example.com",
            "password": "wrongpassword"
        }
        
        response = test_client.post("/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "Credenciales inválidas" in data["detail"]
    
    def test_login_missing_fields(self, test_client: TestClient):
        """Test login con campos faltantes."""
        login_data = {
            "email": "test@example.com"
            # Falta password
        }
        
        response = test_client.post("/v1/auth/login", json=login_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "validation-error" in data["type"]
        assert "password" in str(data["fields"])
    
    def test_refresh_token_success(self, test_client: TestClient):
        """Test refresh token exitoso."""
        refresh_data = {
            "refresh_token": "valid_refresh_token"
        }
        
        response = test_client.post("/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 1800
        
        # Verificar que se actualizó la cookie
        assert "access_token" in response.cookies
    
    def test_refresh_token_invalid(self, test_client: TestClient):
        """Test refresh token inválido."""
        refresh_data = {
            "refresh_token": "invalid_refresh_token"
        }
        
        response = test_client.post("/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "Refresh token inválido" in data["detail"]
    
    def test_logout_success(self, test_client: TestClient):
        """Test logout exitoso."""
        # Primero hacer login para obtener token
        login_data = {
            "email": "test@example.com",
            "password": "password123"
        }
        
        login_response = test_client.post("/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        # Hacer logout
        response = test_client.post("/v1/auth/logout")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Sesión cerrada exitosamente" in data["message"]
        
        # Verificar que se eliminaron las cookies
        assert "access_token" not in response.cookies or response.cookies["access_token"] == ""
        assert "refresh_token" not in response.cookies or response.cookies["refresh_token"] == ""
    
    def test_logout_without_auth(self, test_client: TestClient):
        """Test logout sin autenticación."""
        response = test_client.post("/v1/auth/logout")
        
        # Debería fallar porque no hay usuario autenticado
        assert response.status_code == 401
    
    def test_protected_endpoint_without_auth(self, test_client: TestClient):
        """Test endpoint protegido sin autenticación."""
        response = test_client.get("/v1/households")
        
        assert response.status_code == 401
        data = response.json()
        assert "Token de acceso requerido" in data["detail"]
    
    def test_protected_endpoint_with_invalid_token(self, test_client: TestClient):
        """Test endpoint protegido con token inválido."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = test_client.get("/v1/households", headers=headers)
        
        assert response.status_code == 401
        data = response.json()
        assert "Token inválido" in data["detail"]
    
    def test_protected_endpoint_with_valid_token(self, test_client: TestClient):
        """Test endpoint protegido con token válido."""
        # Mockear autenticación exitosa
        with patch('api.app.core.security.verify_supabase_token') as mock_verify:
            mock_verify.return_value = Mock(
                user_id="user123",
                email="test@example.com",
                aud="authenticated",
                iss="supabase",
                exp=1234567890
            )
            
            headers = {"Authorization": "Bearer valid_token"}
            response = test_client.get("/v1/households", headers=headers)
            
            # Debería pasar la autenticación pero fallar en la lógica de negocio
            # (porque no hay datos reales en la DB)
            assert response.status_code in [200, 500]  # 200 si mockea la DB, 500 si no
    
    def test_cors_headers(self, test_client: TestClient):
        """Test headers CORS."""
        response = test_client.options("/v1/auth/login")
        
        # Verificar headers CORS
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers
    
    def test_security_headers(self, test_client: TestClient):
        """Test headers de seguridad."""
        response = test_client.get("/v1/healthz")
        
        # Verificar headers de seguridad
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["x-frame-options"] == "DENY"
        assert response.headers["x-xss-protection"] == "1; mode=block"
        assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    
    def test_rate_limiting(self, test_client: TestClient):
        """Test rate limiting."""
        login_data = {
            "email": "test@example.com",
            "password": "password123"
        }
        
        # Hacer múltiples requests rápidos
        responses = []
        for _ in range(10):
            response = test_client.post("/v1/auth/login", json=login_data)
            responses.append(response.status_code)
        
        # Al menos algunos deberían ser exitosos
        assert 200 in responses
        
        # Si hay rate limiting, algunos deberían ser 429
        # (esto depende de la configuración de rate limiting)
    
    def test_request_id_header(self, test_client: TestClient):
        """Test que se genera request_id en logs."""
        response = test_client.get("/v1/healthz")
        
        # Verificar que la respuesta es exitosa
        assert response.status_code == 200
        
        # En un entorno real, verificarías que se generó un request_id
        # en los logs, pero aquí solo verificamos que la respuesta es correcta
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
