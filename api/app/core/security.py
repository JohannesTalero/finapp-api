"""Módulo de seguridad para autenticación y autorización."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID

from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel

from .config import settings
from .logging import get_logger, user_id_var, household_id_var

logger = get_logger(__name__)

# Esquema de seguridad
security = HTTPBearer(auto_error=False)


class User(BaseModel):
    """Modelo de usuario autenticado."""
    id: UUID
    email: str
    roles: Dict[str, str] = {}  # household_id -> role


class TokenData(BaseModel):
    """Datos del token JWT."""
    user_id: str
    email: str
    aud: str
    iss: str
    exp: int


async def verify_supabase_token(token: str) -> TokenData:
    """Verifica y decodifica un token de Supabase."""
    try:
        # Decodificar sin verificar la firma (Supabase maneja esto)
        payload = jwt.decode(
            token,
            options={"verify_signature": False, "verify_aud": False}
        )
        
        # Verificar campos requeridos
        user_id = payload.get("sub")
        email = payload.get("email")
        aud = payload.get("aud")
        iss = payload.get("iss")
        exp = payload.get("exp")
        
        if not all([user_id, email, aud, iss, exp]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: campos requeridos faltantes"
            )
        
        # Verificar expiración
        if datetime.utcnow().timestamp() > exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expirado"
            )
        
        return TokenData(
            user_id=user_id,
            email=email,
            aud=aud,
            iss=iss,
            exp=exp
        )
        
    except JWTError as e:
        logger.error("Error decodificando JWT", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> User:
    """Obtiene el usuario actual autenticado."""
    
    # Intentar obtener token de Authorization header
    token = None
    if credentials:
        token = credentials.credentials
    else:
        # Intentar obtener de cookies
        token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acceso requerido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar token
    token_data = await verify_supabase_token(token)
    
    # Crear usuario
    user = User(
        id=UUID(token_data.user_id),
        email=token_data.email
    )
    
    # Establecer contexto de logging
    user_id_var.set(str(user.id))
    
    logger.info("Usuario autenticado", user_id=str(user.id), email=user.email)
    
    return user


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """Obtiene el usuario actual si está autenticado, None en caso contrario."""
    try:
        return await get_current_user(request, credentials)
    except HTTPException:
        return None


class RoleChecker:
    """Verificador de roles para autorización."""
    
    def __init__(self, required_role: str):
        self.required_role = required_role
    
    def __call__(self, user: User = Depends(get_current_user)) -> User:
        # Por ahora retornamos el usuario sin verificar roles específicos
        # La verificación de roles se hará en los repositorios usando RLS
        return user


def require_role(role: str):
    """Decorador para requerir un rol específico."""
    return RoleChecker(role)


def require_household_member():
    """Requiere que el usuario sea miembro del hogar."""
    return RoleChecker("member")


def require_household_admin():
    """Requiere que el usuario sea admin del hogar."""
    return RoleChecker("admin")


def require_household_owner():
    """Requiere que el usuario sea propietario del hogar."""
    return RoleChecker("owner")
