"""Router para gestión de transacciones."""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Header

from ..core.security import User, get_current_user
from ..core.logging import get_logger
from ..core.errors import NotFoundError, IdempotencyError
from ..deps import verify_household_membership, get_idempotency_key
from ..db.repositories.transactions_repo import TransactionsRepository
from ..services.idempotency_service import idempotency_service
from ..models.transactions import (
    TransactionCreate, TransactionUpdate, TransactionResponse,
    TransactionListParams, TransactionListResponse, TransactionSummaryResponse
)

logger = get_logger(__name__)

router = APIRouter(prefix="/v1/households/{household_id}", tags=["transacciones"])
transactions_repo = TransactionsRepository()


@router.get("/transactions", response_model=TransactionListResponse)
async def get_transactions(
    household_id: UUID,
    params: TransactionListParams = Depends(),
    user: User = Depends(verify_household_membership)
) -> TransactionListResponse:
    """Obtiene transacciones de un hogar con paginación cursor-based."""
    try:
        household_id, user = user  # Desempaquetar de verify_household_membership
        
        logger.info(
            "Obteniendo transacciones",
            household_id=str(household_id),
            cursor=params.cursor,
            limit=params.limit,
            user_id=str(user.id)
        )
        
        transactions_data, next_cursor = await transactions_repo.get_transactions_by_household(
            household_id=household_id,
            from_date=params.from_date,
            to_date=params.to_date,
            kind=params.kind,
            category_id=params.category_id,
            account_id=params.account_id,
            search=params.search,
            cursor=params.cursor,
            limit=params.limit,
            sort=params.sort,
            order=params.order,
            user=user
        )
        
        transactions = [TransactionResponse(**t) for t in transactions_data]
        
        logger.info(
            "Transacciones obtenidas",
            count=len(transactions),
            household_id=str(household_id),
            has_next=next_cursor is not None
        )
        
        return TransactionListResponse(
            data=transactions,
            next_cursor=next_cursor
        )
        
    except Exception as e:
        logger.error("Error obteniendo transacciones", household_id=str(household_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo transacciones"
        )


@router.post("/transactions", response_model=TransactionResponse)
async def create_transaction(
    household_id: UUID,
    request: TransactionCreate,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    user: User = Depends(verify_household_membership)
) -> TransactionResponse:
    """
    Crea una nueva transacción.
    
    REQUIERE header Idempotency-Key para operaciones financieras.
    """
    try:
        household_id, user = user  # Desempaquetar de verify_household_membership
        
        logger.info(
            "Creando transacción",
            household_id=str(household_id),
            kind=request.kind,
            amount=request.amount,
            idempotency_key=idempotency_key,
            user_id=str(user.id)
        )
        
        # Verificar idempotencia
        request_body = request.dict()
        is_duplicate, cached_response = await idempotency_service.check_idempotency(
            key=idempotency_key,
            user_id=user.id,
            household_id=household_id,
            request_body=request_body
        )
        
        if is_duplicate:
            logger.info("Transacción idempotente encontrada", idempotency_key=idempotency_key)
            return TransactionResponse(**cached_response)
        
        # Crear transacción
        transaction_data = await transactions_repo.create_transaction(
            household_id=household_id,
            kind=request.kind,
            amount=request.amount,
            account_id=request.account_id,
            from_account_id=request.from_account_id,
            to_account_id=request.to_account_id,
            category_id=request.category_id,
            occurred_at=request.occurred_at,
            description=request.description,
            counterparty=request.counterparty,
            user=user
        )
        
        transaction_response = TransactionResponse(**transaction_data)
        
        # Almacenar resultado para idempotencia
        await idempotency_service.store_idempotency_result(
            key=idempotency_key,
            user_id=user.id,
            household_id=household_id,
            request_body=request_body,
            response_status=201,
            response_body=transaction_response.dict()
        )
        
        logger.info("Transacción creada", transaction_id=transaction_data["id"], household_id=str(household_id))
        
        return transaction_response
        
    except IdempotencyError:
        raise
    except Exception as e:
        logger.error("Error creando transacción", household_id=str(household_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creando transacción"
        )


@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    household_id: UUID,
    transaction_id: UUID,
    user: User = Depends(verify_household_membership)
) -> TransactionResponse:
    """Obtiene una transacción por ID."""
    try:
        household_id, user = user  # Desempaquetar de verify_household_membership
        
        logger.info("Obteniendo transacción", transaction_id=str(transaction_id), household_id=str(household_id))
        
        transaction_data = await transactions_repo.get_transaction_by_id(transaction_id, user)
        
        if not transaction_data:
            raise NotFoundError("Transacción", str(transaction_id))
        
        logger.info("Transacción obtenida", transaction_id=str(transaction_id))
        
        return TransactionResponse(**transaction_data)
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Error obteniendo transacción", transaction_id=str(transaction_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo transacción"
        )


@router.patch("/transactions/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    household_id: UUID,
    transaction_id: UUID,
    request: TransactionUpdate,
    user: User = Depends(verify_household_membership)
) -> TransactionResponse:
    """Actualiza una transacción."""
    try:
        household_id, user = user  # Desempaquetar de verify_household_membership
        
        logger.info("Actualizando transacción", transaction_id=str(transaction_id), household_id=str(household_id))
        
        transaction_data = await transactions_repo.update_transaction(
            transaction_id=transaction_id,
            amount=request.amount,
            category_id=request.category_id,
            occurred_at=request.occurred_at,
            description=request.description,
            counterparty=request.counterparty,
            user=user
        )
        
        if not transaction_data:
            raise NotFoundError("Transacción", str(transaction_id))
        
        logger.info("Transacción actualizada", transaction_id=str(transaction_id))
        
        return TransactionResponse(**transaction_data)
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Error actualizando transacción", transaction_id=str(transaction_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error actualizando transacción"
        )


@router.delete("/transactions/{transaction_id}")
async def delete_transaction(
    household_id: UUID,
    transaction_id: UUID,
    user: User = Depends(verify_household_membership)
) -> dict:
    """Elimina una transacción."""
    try:
        household_id, user = user  # Desempaquetar de verify_household_membership
        
        logger.info("Eliminando transacción", transaction_id=str(transaction_id), household_id=str(household_id))
        
        success = await transactions_repo.delete_transaction(transaction_id, user)
        
        if not success:
            raise NotFoundError("Transacción", str(transaction_id))
        
        logger.info("Transacción eliminada", transaction_id=str(transaction_id))
        
        return {"success": True, "message": "Transacción eliminada exitosamente"}
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Error eliminando transacción", transaction_id=str(transaction_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error eliminando transacción"
        )


@router.get("/transactions/summary", response_model=TransactionSummaryResponse)
async def get_transaction_summary(
    household_id: UUID,
    from_date: str = None,
    to_date: str = None,
    user: User = Depends(verify_household_membership)
) -> TransactionSummaryResponse:
    """Obtiene resumen de transacciones."""
    try:
        household_id, user = user  # Desempaquetar de verify_household_membership
        
        logger.info("Obteniendo resumen de transacciones", household_id=str(household_id), user_id=str(user.id))
        
        summary_data = await transactions_repo.get_transaction_summary(
            household_id=household_id,
            from_date=from_date,
            to_date=to_date,
            user=user
        )
        
        logger.info("Resumen de transacciones obtenido", household_id=str(household_id))
        
        return TransactionSummaryResponse(**summary_data)
        
    except Exception as e:
        logger.error("Error obteniendo resumen de transacciones", household_id=str(household_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo resumen de transacciones"
        )
