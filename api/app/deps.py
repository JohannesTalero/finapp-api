"""Dependencias comunes para FastAPI."""

from typing import Optional
from uuid import UUID
from fastapi import Depends, Query, HTTPException, status

from .core.security import User, get_current_user, require_role
from .core.errors import AuthorizationError, NotFoundError
from .core.logging import get_logger, household_id_var
from .db.repositories.households_repo import HouseholdsRepository

logger = get_logger(__name__)


async def get_pagination_params(
    cursor: Optional[str] = Query(None, description="Cursor para paginación"),
    limit: int = Query(20, ge=1, le=100, description="Número de elementos por página")
) -> dict:
    """Parámetros de paginación."""
    return {"cursor": cursor, "limit": limit}


async def get_household_id(
    household_id: UUID = Query(..., description="ID del hogar")
) -> UUID:
    """Extrae el household_id del path."""
    return household_id


async def verify_household_membership(
    household_id: UUID = Depends(get_household_id),
    user: User = Depends(get_current_user)
) -> tuple[UUID, User]:
    """
    Verifica que el usuario sea miembro del hogar.
    
    En producción, esto verificaría la membresía en la base de datos.
    Por ahora, solo establece el contexto de logging.
    """
    # Establecer contexto de logging
    household_id_var.set(str(household_id))
    
    # En producción, verificarías la membresía:
    # households_repo = HouseholdsRepository()
    # membership = await households_repo.get_household_member(household_id, user.id)
    # if not membership:
    #     raise AuthorizationError("No eres miembro de este hogar")
    
    logger.info(
        "Verificación de membresía",
        household_id=str(household_id),
        user_id=str(user.id)
    )
    
    return household_id, user


async def verify_household_admin(
    household_id: UUID = Depends(get_household_id),
    user: User = Depends(get_current_user)
) -> tuple[UUID, User]:
    """
    Verifica que el usuario sea admin del hogar.
    
    En producción, esto verificaría el rol en la base de datos.
    """
    # Establecer contexto de logging
    household_id_var.set(str(household_id))
    
    # En producción, verificarías el rol:
    # households_repo = HouseholdsRepository()
    # membership = await households_repo.get_household_member(household_id, user.id)
    # if not membership or membership["role"] not in ["admin", "owner"]:
    #     raise AuthorizationError("No tienes permisos de administrador en este hogar")
    
    logger.info(
        "Verificación de admin",
        household_id=str(household_id),
        user_id=str(user.id)
    )
    
    return household_id, user


async def verify_household_owner(
    household_id: UUID = Depends(get_household_id),
    user: User = Depends(get_current_user)
) -> tuple[UUID, User]:
    """
    Verifica que el usuario sea propietario del hogar.
    
    En producción, esto verificaría el rol en la base de datos.
    """
    # Establecer contexto de logging
    household_id_var.set(str(household_id))
    
    # En producción, verificarías el rol:
    # households_repo = HouseholdsRepository()
    # membership = await households_repo.get_household_member(household_id, user.id)
    # if not membership or membership["role"] != "owner":
    #     raise AuthorizationError("No eres propietario de este hogar")
    
    logger.info(
        "Verificación de propietario",
        household_id=str(household_id),
        user_id=str(user.id)
    )
    
    return household_id, user


def get_idempotency_key() -> str:
    """Extrae la Idempotency-Key del header."""
    # En producción, esto vendría del header de la request
    # Por ahora retornamos un valor mock
    return "mock_idempotency_key"


# Dependencias para diferentes niveles de autorización
require_member = require_role("member")
require_admin = require_role("admin")
require_owner = require_role("owner")
