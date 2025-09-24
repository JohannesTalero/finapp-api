"""Tests unitarios para módulo de seguridad."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from jose import jwt
from fastapi import HTTPException

from api.app.core.security import (
    verify_supabase_token,
    get_current_user,
    TokenData,
    User
)
from api.app.core.config import Settings


class TestVerifySupabaseToken:
    """Tests para verificación de tokens de Supabase."""
    
    def test_verify_valid_token(self):
        """Test con token válido."""
        # Crear token válido
        now = datetime.utcnow()
        exp = now + timedelta(hours=1)
        
        payload = {
            "sub": "user123",
            "email": "test@example.com",
            "aud": "authenticated",
            "iss": "supabase",
            "exp": exp.timestamp()
        }
        
        token = jwt.encode(payload, "secret", algorithm="HS256")
        
        # Verificar token
        token_data = verify_supabase_token(token)
        
        assert token_data.user_id == "user123"
        assert token_data.email == "test@example.com"
        assert token_data.aud == "authenticated"
        assert token_data.iss == "supabase"
    
    def test_verify_expired_token(self):
        """Test con token expirado."""
        # Crear token expirado
        exp = datetime.utcnow() - timedelta(hours=1)
        
        payload = {
            "sub": "user123",
            "email": "test@example.com",
            "aud": "authenticated",
            "iss": "supabase",
            "exp": exp.timestamp()
        }
        
        token = jwt.encode(payload, "secret", algorithm="HS256")
        
        # Verificar que lanza excepción
        with pytest.raises(HTTPException) as exc_info:
            verify_supabase_token(token)
        
        assert exc_info.value.status_code == 401
        assert "expirado" in exc_info.value.detail
    
    def test_verify_invalid_token(self):
        """Test con token inválido."""
        # Token malformado
        invalid_token = "invalid.token.here"
        
        with pytest.raises(HTTPException) as exc_info:
            verify_supabase_token(invalid_token)
        
        assert exc_info.value.status_code == 401
        assert "inválido" in exc_info.value.detail
    
    def test_verify_token_missing_fields(self):
        """Test con token faltando campos requeridos."""
        # Token sin campos requeridos
        payload = {
            "sub": "user123",
            # Falta email, aud, iss, exp
        }
        
        token = jwt.encode(payload, "secret", algorithm="HS256")
        
        with pytest.raises(HTTPException) as exc_info:
            verify_supabase_token(token)
        
        assert exc_info.value.status_code == 401
        assert "campos requeridos faltantes" in exc_info.value.detail


class TestGetCurrentUser:
    """Tests para obtener usuario actual."""
    
    @pytest.fixture
    def mock_request(self):
        """Request mock."""
        request = Mock()
        request.cookies = {}
        request.headers = {}
        return request
    
    @pytest.fixture
    def mock_credentials(self):
        """Credentials mock."""
        credentials = Mock()
        credentials.credentials = "valid_token"
        return credentials
    
    @patch('api.app.core.security.verify_supabase_token')
    def test_get_current_user_with_authorization_header(
        self, 
        mock_verify_token, 
        mock_request, 
        mock_credentials
    ):
        """Test con header Authorization."""
        # Configurar mock
        mock_verify_token.return_value = TokenData(
            user_id="user123",
            email="test@example.com",
            aud="authenticated",
            iss="supabase",
            exp=1234567890
        )
        
        # Llamar función
        user = get_current_user(mock_request, mock_credentials)
        
        # Verificar
        assert user.id == "user123"
        assert user.email == "test@example.com"
        mock_verify_token.assert_called_once_with("valid_token")
    
    @patch('api.app.core.security.verify_supabase_token')
    def test_get_current_user_with_cookie(
        self, 
        mock_verify_token, 
        mock_request
    ):
        """Test con cookie access_token."""
        # Configurar mock
        mock_request.cookies = {"access_token": "cookie_token"}
        mock_verify_token.return_value = TokenData(
            user_id="user123",
            email="test@example.com",
            aud="authenticated",
            iss="supabase",
            exp=1234567890
        )
        
        # Llamar función
        user = get_current_user(mock_request, None)
        
        # Verificar
        assert user.id == "user123"
        assert user.email == "test@example.com"
        mock_verify_token.assert_called_once_with("cookie_token")
    
    def test_get_current_user_no_token(self, mock_request):
        """Test sin token."""
        # Sin token en header ni cookie
        mock_request.cookies = {}
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(mock_request, None)
        
        assert exc_info.value.status_code == 401
        assert "Token de acceso requerido" in exc_info.value.detail


class TestUserModel:
    """Tests para modelo User."""
    
    def test_user_creation(self):
        """Test creación de usuario."""
        user = User(
            id="user123",
            email="test@example.com",
            roles={"household1": "owner", "household2": "member"}
        )
        
        assert user.id == "user123"
        assert user.email == "test@example.com"
        assert user.roles["household1"] == "owner"
        assert user.roles["household2"] == "member"
    
    def test_user_default_roles(self):
        """Test usuario con roles por defecto."""
        user = User(
            id="user123",
            email="test@example.com"
        )
        
        assert user.roles == {}


class TestTokenDataModel:
    """Tests para modelo TokenData."""
    
    def test_token_data_creation(self):
        """Test creación de TokenData."""
        token_data = TokenData(
            user_id="user123",
            email="test@example.com",
            aud="authenticated",
            iss="supabase",
            exp=1234567890
        )
        
        assert token_data.user_id == "user123"
        assert token_data.email == "test@example.com"
        assert token_data.aud == "authenticated"
        assert token_data.iss == "supabase"
        assert token_data.exp == 1234567890
