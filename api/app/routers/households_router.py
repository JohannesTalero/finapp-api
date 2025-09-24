"""Router para gestión de hogares."""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from ..core.security import User, get_current_user
from ..core.logging import get_logger
from ..core.errors import NotFoundError
from ..deps import verify_household_admin, verify_household_owner
from ..db.repositories.households_repo import HouseholdsRepository
from ..models.households import (
    HouseholdCreate, HouseholdUpdate, HouseholdResponse,
    HouseholdMemberCreate, HouseholdMemberUpdate, HouseholdMemberResponse,
    HouseholdListResponse
)

logger = get_logger(__name__)

router = APIRouter(prefix="/v1/households", tags=["hogares"])
households_repo = HouseholdsRepository()


@router.post("", response_model=HouseholdResponse)
async def create_household(
    request: HouseholdCreate,
    user: User = Depends(get_current_user)
) -> HouseholdResponse:
    """Crea un nuevo hogar."""
    try:
        logger.info("Creando hogar", user_id=str(user.id), name=request.name)
        
        household_data = await households_repo.create_household(
            name=request.name,
            description=request.description,
            owner_id=user.id,
            user=user
        )
        
        logger.info("Hogar creado", household_id=household_data["id"], user_id=str(user.id))
        
        return HouseholdResponse(**household_data)
        
    except Exception as e:
        logger.error("Error creando hogar", user_id=str(user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creando hogar"
        )


@router.get("", response_model=HouseholdListResponse)
async def get_households(
    user: User = Depends(get_current_user)
) -> HouseholdListResponse:
    """Obtiene todos los hogares del usuario."""
    try:
        logger.info("Obteniendo hogares", user_id=str(user.id))
        
        households_data = await households_repo.get_user_households(user.id, user)
        
        households = [HouseholdResponse(**h) for h in households_data]
        
        logger.info("Hogares obtenidos", count=len(households), user_id=str(user.id))
        
        return HouseholdListResponse(households=households)
        
    except Exception as e:
        logger.error("Error obteniendo hogares", user_id=str(user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo hogares"
        )


@router.get("/{household_id}", response_model=HouseholdResponse)
async def get_household(
    household_id: UUID,
    user: User = Depends(get_current_user)
) -> HouseholdResponse:
    """Obtiene un hogar por ID."""
    try:
        logger.info("Obteniendo hogar", household_id=str(household_id), user_id=str(user.id))
        
        household_data = await households_repo.get_household_by_id(household_id, user)
        
        if not household_data:
            raise NotFoundError("Hogar", str(household_id))
        
        logger.info("Hogar obtenido", household_id=str(household_id), user_id=str(user.id))
        
        return HouseholdResponse(**household_data)
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Error obteniendo hogar", household_id=str(household_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo hogar"
        )


@router.patch("/{household_id}", response_model=HouseholdResponse)
async def update_household(
    household_id: UUID,
    request: HouseholdUpdate,
    user: User = Depends(verify_household_owner)
) -> HouseholdResponse:
    """Actualiza un hogar."""
    try:
        household_id, user = user  # Desempaquetar de verify_household_owner
        
        logger.info("Actualizando hogar", household_id=str(household_id), user_id=str(user.id))
        
        household_data = await households_repo.update_household(
            household_id=household_id,
            name=request.name,
            description=request.description,
            user=user
        )
        
        if not household_data:
            raise NotFoundError("Hogar", str(household_id))
        
        logger.info("Hogar actualizado", household_id=str(household_id), user_id=str(user.id))
        
        return HouseholdResponse(**household_data)
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Error actualizando hogar", household_id=str(household_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error actualizando hogar"
        )


@router.delete("/{household_id}")
async def delete_household(
    household_id: UUID,
    user: User = Depends(verify_household_owner)
) -> dict:
    """Elimina un hogar."""
    try:
        household_id, user = user  # Desempaquetar de verify_household_owner
        
        logger.info("Eliminando hogar", household_id=str(household_id), user_id=str(user.id))
        
        success = await households_repo.delete_household(household_id, user)
        
        if not success:
            raise NotFoundError("Hogar", str(household_id))
        
        logger.info("Hogar eliminado", household_id=str(household_id), user_id=str(user.id))
        
        return {"success": True, "message": "Hogar eliminado exitosamente"}
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Error eliminando hogar", household_id=str(household_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error eliminando hogar"
        )


@router.get("/{household_id}/members", response_model=List[HouseholdMemberResponse])
async def get_household_members(
    household_id: UUID,
    user: User = Depends(get_current_user)
) -> List[HouseholdMemberResponse]:
    """Obtiene los miembros de un hogar."""
    try:
        logger.info("Obteniendo miembros", household_id=str(household_id), user_id=str(user.id))
        
        members_data = await households_repo.get_household_members(household_id, user)
        
        members = [HouseholdMemberResponse(**m) for m in members_data]
        
        logger.info("Miembros obtenidos", count=len(members), household_id=str(household_id))
        
        return members
        
    except Exception as e:
        logger.error("Error obteniendo miembros", household_id=str(household_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo miembros"
        )


@router.post("/{household_id}/members", response_model=HouseholdMemberResponse)
async def add_household_member(
    household_id: UUID,
    request: HouseholdMemberCreate,
    user: User = Depends(verify_household_admin)
) -> HouseholdMemberResponse:
    """Agrega un miembro al hogar."""
    try:
        household_id, user = user  # Desempaquetar de verify_household_admin
        
        logger.info(
            "Agregando miembro",
            household_id=str(household_id),
            new_user_id=str(request.user_id),
            role=request.role,
            admin_user_id=str(user.id)
        )
        
        member_data = await households_repo.add_household_member(
            household_id=household_id,
            user_id=request.user_id,
            role=request.role,
            user=user
        )
        
        logger.info("Miembro agregado", household_id=str(household_id), user_id=str(request.user_id))
        
        return HouseholdMemberResponse(**member_data)
        
    except Exception as e:
        logger.error("Error agregando miembro", household_id=str(household_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error agregando miembro"
        )


@router.patch("/{household_id}/members/{user_id}", response_model=HouseholdMemberResponse)
async def update_household_member_role(
    household_id: UUID,
    user_id: UUID,
    request: HouseholdMemberUpdate,
    admin_user: User = Depends(verify_household_admin)
) -> HouseholdMemberResponse:
    """Actualiza el rol de un miembro del hogar."""
    try:
        household_id, admin_user = admin_user  # Desempaquetar de verify_household_admin
        
        logger.info(
            "Actualizando rol de miembro",
            household_id=str(household_id),
            user_id=str(user_id),
            new_role=request.role,
            admin_user_id=str(admin_user.id)
        )
        
        member_data = await households_repo.update_household_member_role(
            household_id=household_id,
            user_id=user_id,
            role=request.role,
            user=admin_user
        )
        
        if not member_data:
            raise NotFoundError("Miembro", str(user_id))
        
        logger.info("Rol de miembro actualizado", household_id=str(household_id), user_id=str(user_id))
        
        return HouseholdMemberResponse(**member_data)
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Error actualizando rol de miembro", household_id=str(household_id), user_id=str(user_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error actualizando rol de miembro"
        )


@router.delete("/{household_id}/members/{user_id}")
async def remove_household_member(
    household_id: UUID,
    user_id: UUID,
    admin_user: User = Depends(verify_household_admin)
) -> dict:
    """Remueve un miembro del hogar."""
    try:
        household_id, admin_user = admin_user  # Desempaquetar de verify_household_admin
        
        logger.info(
            "Removiendo miembro",
            household_id=str(household_id),
            user_id=str(user_id),
            admin_user_id=str(admin_user.id)
        )
        
        success = await households_repo.remove_household_member(
            household_id=household_id,
            user_id=user_id,
            user=admin_user
        )
        
        if not success:
            raise NotFoundError("Miembro", str(user_id))
        
        logger.info("Miembro removido", household_id=str(household_id), user_id=str(user_id))
        
        return {"success": True, "message": "Miembro removido exitosamente"}
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Error removiendo miembro", household_id=str(household_id), user_id=str(user_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error removiendo miembro"
        )
