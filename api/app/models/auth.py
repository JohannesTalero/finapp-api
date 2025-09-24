"""Modelos para autenticación."""

from typing import Optional
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Request de login."""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Response de login."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    """Request de refresh token."""
    refresh_token: str


class RefreshResponse(BaseModel):
    """Response de refresh token."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class LogoutResponse(BaseModel):
    """Response de logout."""
    success: bool = True
    message: str = "Sesión cerrada exitosamente"
