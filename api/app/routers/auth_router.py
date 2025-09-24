"""Router para autenticación."""

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import HTTPBearer

from ..core.security import get_current_user, User
from ..core.logging import get_logger
from ..models.auth import LoginRequest, LoginResponse, RefreshRequest, RefreshResponse, LogoutResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/v1/auth", tags=["autenticación"])
security = HTTPBearer(auto_error=False)


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    response: Response
) -> LoginResponse:
    """
    Inicia sesión de usuario.
    
    Crea cookies HttpOnly con access_token y refresh_token.
    """
    try:
        # En producción, esto autenticaría con Supabase
        # Por ahora retornamos tokens mock
        
        logger.info("Intento de login", email=request.email)
        
        # Simular autenticación exitosa
        access_token = "mock_access_token"
        refresh_token = "mock_refresh_token"
        
        # Establecer cookies HttpOnly
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,  # Solo HTTPS en producción
            samesite="strict",
            max_age=1800  # 30 minutos
        )
        
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=604800  # 7 días
        )
        
        logger.info("Login exitoso", email=request.email)
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=1800
        )
        
    except Exception as e:
        logger.error("Error en login", email=request.email, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas"
        )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    request: RefreshRequest,
    response: Response
) -> RefreshResponse:
    """
    Renueva el access token usando el refresh token.
    """
    try:
        logger.info("Intento de refresh token")
        
        # En producción, esto verificaría y renovaría el token con Supabase
        # Por ahora retornamos un nuevo token mock
        
        new_access_token = "mock_new_access_token"
        
        # Actualizar cookie del access token
        response.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=1800
        )
        
        logger.info("Refresh token exitoso")
        
        return RefreshResponse(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=1800
        )
        
    except Exception as e:
        logger.error("Error en refresh token", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido"
        )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    response: Response,
    user: User = Depends(get_current_user)
) -> LogoutResponse:
    """
    Cierra la sesión del usuario.
    
    Elimina las cookies de autenticación.
    """
    try:
        logger.info("Logout", user_id=str(user.id))
        
        # Eliminar cookies
        response.delete_cookie(key="access_token")
        response.delete_cookie(key="refresh_token")
        
        logger.info("Logout exitoso", user_id=str(user.id))
        
        return LogoutResponse()
        
    except Exception as e:
        logger.error("Error en logout", user_id=str(user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error cerrando sesión"
        )
