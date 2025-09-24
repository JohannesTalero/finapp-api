"""Router para catálogos (categorías y cuentas)."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query

from ..core.security import User, get_current_user
from ..core.logging import get_logger
from ..core.errors import NotFoundError
from ..deps import verify_household_membership
from ..db.repositories.categories_repo import CategoriesRepository
from ..db.repositories.accounts_repo import AccountsRepository
from ..models.catalog import (
    CategoryCreate, CategoryUpdate, CategoryResponse, CategoryListResponse,
    AccountCreate, AccountUpdate, AccountResponse, AccountListResponse
)
from ..models.base import TransactionKind, AccountType

logger = get_logger(__name__)

router = APIRouter(prefix="/v1/households/{household_id}", tags=["catálogos"])
categories_repo = CategoriesRepository()
accounts_repo = AccountsRepository()


# ===== CATEGORÍAS =====

@router.get("/categories", response_model=CategoryListResponse)
async def get_categories(
    household_id: UUID,
    kind: Optional[TransactionKind] = Query(None, description="Tipo de transacción"),
    user: User = Depends(verify_household_membership)
) -> CategoryListResponse:
    """Obtiene categorías de un hogar."""
    try:
        household_id, user = user  # Desempaquetar de verify_household_membership
        
        logger.info("Obteniendo categorías", household_id=str(household_id), kind=kind, user_id=str(user.id))
        
        categories_data = await categories_repo.get_categories_by_household(
            household_id=household_id,
            kind=kind,
            user=user
        )
        
        categories = [CategoryResponse(**c) for c in categories_data]
        
        logger.info("Categorías obtenidas", count=len(categories), household_id=str(household_id))
        
        return CategoryListResponse(categories=categories)
        
    except Exception as e:
        logger.error("Error obteniendo categorías", household_id=str(household_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo categorías"
        )


@router.post("/categories", response_model=CategoryResponse)
async def create_category(
    household_id: UUID,
    request: CategoryCreate,
    user: User = Depends(verify_household_membership)
) -> CategoryResponse:
    """Crea una nueva categoría."""
    try:
        household_id, user = user  # Desempaquetar de verify_household_membership
        
        logger.info("Creando categoría", household_id=str(household_id), name=request.name, kind=request.kind, user_id=str(user.id))
        
        category_data = await categories_repo.create_category(
            household_id=household_id,
            name=request.name,
            kind=request.kind,
            description=request.description,
            color=request.color,
            icon=request.icon,
            user=user
        )
        
        logger.info("Categoría creada", category_id=category_data["id"], household_id=str(household_id))
        
        return CategoryResponse(**category_data)
        
    except Exception as e:
        logger.error("Error creando categoría", household_id=str(household_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creando categoría"
        )


@router.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(
    household_id: UUID,
    category_id: UUID,
    user: User = Depends(verify_household_membership)
) -> CategoryResponse:
    """Obtiene una categoría por ID."""
    try:
        household_id, user = user  # Desempaquetar de verify_household_membership
        
        logger.info("Obteniendo categoría", category_id=str(category_id), household_id=str(household_id))
        
        category_data = await categories_repo.get_category_by_id(category_id, user)
        
        if not category_data:
            raise NotFoundError("Categoría", str(category_id))
        
        logger.info("Categoría obtenida", category_id=str(category_id))
        
        return CategoryResponse(**category_data)
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Error obteniendo categoría", category_id=str(category_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo categoría"
        )


@router.patch("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    household_id: UUID,
    category_id: UUID,
    request: CategoryUpdate,
    user: User = Depends(verify_household_membership)
) -> CategoryResponse:
    """Actualiza una categoría."""
    try:
        household_id, user = user  # Desempaquetar de verify_household_membership
        
        logger.info("Actualizando categoría", category_id=str(category_id), household_id=str(household_id))
        
        category_data = await categories_repo.update_category(
            category_id=category_id,
            name=request.name,
            description=request.description,
            color=request.color,
            icon=request.icon,
            user=user
        )
        
        if not category_data:
            raise NotFoundError("Categoría", str(category_id))
        
        logger.info("Categoría actualizada", category_id=str(category_id))
        
        return CategoryResponse(**category_data)
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Error actualizando categoría", category_id=str(category_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error actualizando categoría"
        )


@router.delete("/categories/{category_id}")
async def delete_category(
    household_id: UUID,
    category_id: UUID,
    user: User = Depends(verify_household_membership)
) -> dict:
    """Elimina una categoría."""
    try:
        household_id, user = user  # Desempaquetar de verify_household_membership
        
        logger.info("Eliminando categoría", category_id=str(category_id), household_id=str(household_id))
        
        # Verificar si la categoría está en uso
        usage_count = await categories_repo.get_category_usage_count(category_id, user)
        if usage_count > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"No se puede eliminar la categoría porque está siendo usada en {usage_count} transacciones"
            )
        
        success = await categories_repo.delete_category(category_id, user)
        
        if not success:
            raise NotFoundError("Categoría", str(category_id))
        
        logger.info("Categoría eliminada", category_id=str(category_id))
        
        return {"success": True, "message": "Categoría eliminada exitosamente"}
        
    except NotFoundError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error eliminando categoría", category_id=str(category_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error eliminando categoría"
        )


# ===== CUENTAS =====

@router.get("/accounts", response_model=AccountListResponse)
async def get_accounts(
    household_id: UUID,
    account_type: Optional[AccountType] = Query(None, description="Tipo de cuenta"),
    user: User = Depends(verify_household_membership)
) -> AccountListResponse:
    """Obtiene cuentas de un hogar."""
    try:
        household_id, user = user  # Desempaquetar de verify_household_membership
        
        logger.info("Obteniendo cuentas", household_id=str(household_id), account_type=account_type, user_id=str(user.id))
        
        accounts_data = await accounts_repo.get_accounts_by_household(
            household_id=household_id,
            account_type=account_type,
            user=user
        )
        
        accounts = [AccountResponse(**a) for a in accounts_data]
        
        logger.info("Cuentas obtenidas", count=len(accounts), household_id=str(household_id))
        
        return AccountListResponse(accounts=accounts)
        
    except Exception as e:
        logger.error("Error obteniendo cuentas", household_id=str(household_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo cuentas"
        )


@router.post("/accounts", response_model=AccountResponse)
async def create_account(
    household_id: UUID,
    request: AccountCreate,
    user: User = Depends(verify_household_membership)
) -> AccountResponse:
    """Crea una nueva cuenta."""
    try:
        household_id, user = user  # Desempaquetar de verify_household_membership
        
        logger.info("Creando cuenta", household_id=str(household_id), name=request.name, account_type=request.account_type, user_id=str(user.id))
        
        account_data = await accounts_repo.create_account(
            household_id=household_id,
            name=request.name,
            account_type=request.account_type,
            currency=request.currency,
            initial_balance=request.initial_balance,
            description=request.description,
            color=request.color,
            icon=request.icon,
            user=user
        )
        
        logger.info("Cuenta creada", account_id=account_data["id"], household_id=str(household_id))
        
        return AccountResponse(**account_data)
        
    except Exception as e:
        logger.error("Error creando cuenta", household_id=str(household_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creando cuenta"
        )


@router.get("/accounts/{account_id}", response_model=AccountResponse)
async def get_account(
    household_id: UUID,
    account_id: UUID,
    user: User = Depends(verify_household_membership)
) -> AccountResponse:
    """Obtiene una cuenta por ID."""
    try:
        household_id, user = user  # Desempaquetar de verify_household_membership
        
        logger.info("Obteniendo cuenta", account_id=str(account_id), household_id=str(household_id))
        
        account_data = await accounts_repo.get_account_by_id(account_id, user)
        
        if not account_data:
            raise NotFoundError("Cuenta", str(account_id))
        
        logger.info("Cuenta obtenida", account_id=str(account_id))
        
        return AccountResponse(**account_data)
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Error obteniendo cuenta", account_id=str(account_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo cuenta"
        )


@router.patch("/accounts/{account_id}", response_model=AccountResponse)
async def update_account(
    household_id: UUID,
    account_id: UUID,
    request: AccountUpdate,
    user: User = Depends(verify_household_membership)
) -> AccountResponse:
    """Actualiza una cuenta."""
    try:
        household_id, user = user  # Desempaquetar de verify_household_membership
        
        logger.info("Actualizando cuenta", account_id=str(account_id), household_id=str(household_id))
        
        account_data = await accounts_repo.update_account(
            account_id=account_id,
            name=request.name,
            description=request.description,
            color=request.color,
            icon=request.icon,
            user=user
        )
        
        if not account_data:
            raise NotFoundError("Cuenta", str(account_id))
        
        logger.info("Cuenta actualizada", account_id=str(account_id))
        
        return AccountResponse(**account_data)
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Error actualizando cuenta", account_id=str(account_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error actualizando cuenta"
        )


@router.delete("/accounts/{account_id}")
async def delete_account(
    household_id: UUID,
    account_id: UUID,
    user: User = Depends(verify_household_membership)
) -> dict:
    """Elimina una cuenta."""
    try:
        household_id, user = user  # Desempaquetar de verify_household_membership
        
        logger.info("Eliminando cuenta", account_id=str(account_id), household_id=str(household_id))
        
        # Verificar si la cuenta está en uso
        usage_count = await accounts_repo.get_account_transactions_count(account_id, user)
        if usage_count > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"No se puede eliminar la cuenta porque está siendo usada en {usage_count} transacciones"
            )
        
        success = await accounts_repo.delete_account(account_id, user)
        
        if not success:
            raise NotFoundError("Cuenta", str(account_id))
        
        logger.info("Cuenta eliminada", account_id=str(account_id))
        
        return {"success": True, "message": "Cuenta eliminada exitosamente"}
        
    except NotFoundError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error eliminando cuenta", account_id=str(account_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error eliminando cuenta"
        )
