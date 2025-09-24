"""Modelos para hogares."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field
from .base import BaseModelWithTimestamps, Role


class HouseholdCreate(BaseModel):
    """Crear hogar."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class HouseholdUpdate(BaseModel):
    """Actualizar hogar."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class HouseholdResponse(BaseModelWithTimestamps):
    """Response de hogar."""
    id: UUID
    name: str
    description: Optional[str]
    owner_id: UUID


class HouseholdMemberCreate(BaseModel):
    """Agregar miembro al hogar."""
    user_id: UUID
    role: Role


class HouseholdMemberUpdate(BaseModel):
    """Actualizar rol de miembro."""
    role: Role


class HouseholdMemberResponse(BaseModel):
    """Response de miembro del hogar."""
    user_id: UUID
    household_id: UUID
    role: Role
    joined_at: datetime
    user: Optional[dict] = None  # Datos del usuario si se incluyen


class HouseholdListResponse(BaseModel):
    """Lista de hogares."""
    households: List[HouseholdResponse]
