"""Router para gestión de obligaciones."""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Header

from ..core.security import User, get_current_user
from ..core.logging import get_logger
from ..core.errors import NotFoundError, IdempotencyError
from ..deps import verify_household_membership, get_idempotency_key
from ..db.repositories.obligations_repo import ObligationsRepository
from ..services.payments_service import payments_service
from ..services.idempotency_service import idempotency_service
from ..services.recurrence_service import recurrence_service
from ..models.obligations import (
    ObligationCreate, ObligationUpdate, ObligationResponse, ObligationListParams, ObligationListResponse,
    ObligationPaymentCreate, ObligationPaymentResponse, ObligationActionResponse
)

logger = get_logger(__name__)

router = APIRouter(prefix="/v1/households/{household_id}", tags=["obligaciones"])
obligations_repo = ObligationsRepository()


@router.get("/obligations", response_model=ObligationListResponse)
async def get_obligations(
    household_id: UUID,
    params: ObligationListParams = Depends(),
    user: User = Depends(verify_household_membership)
) -> ObligationListResponse:
    """Obtiene obligaciones de un hogar con paginación cursor-based."""
    try:
        household_id, user = user
        
        obligations_data, next_cursor = await obligations_repo.get_obligations_by_household(
            household_id=household_id,
            status=params.status,
            due_before=params.due_before,
            priority=params.priority,
            is_recurring=params.is_recurring,
            cursor=params.cursor,
            limit=params.limit,
            user=user
        )
        
        obligations = [ObligationResponse(**o) for o in obligations_data]
        
        return ObligationListResponse(data=obligations, next_cursor=next_cursor)
        
    except Exception as e:
        logger.error("Error obteniendo obligaciones", household_id=str(household_id), error=str(e))
        raise HTTPException(status_code=500, detail="Error obteniendo obligaciones")


@router.post("/obligations", response_model=ObligationResponse)
async def create_obligation(
    household_id: UUID,
    request: ObligationCreate,
    user: User = Depends(verify_household_membership)
) -> ObligationResponse:
    """Crea una nueva obligación."""
    try:
        household_id, user = user
        
        obligation_data = await obligations_repo.create_obligation(
            household_id=household_id,
            name=request.name,
            total_amount=request.total_amount,
            outstanding_amount=request.outstanding_amount,
            due_date=request.due_date,
            description=request.description,
            priority=request.priority,
            creditor=request.creditor,
            is_recurring=request.is_recurring,
            recurrence_pattern=request.recurrence_pattern,
            user=user
        )
        
        return ObligationResponse(**obligation_data)
        
    except Exception as e:
        logger.error("Error creando obligación", household_id=str(household_id), error=str(e))
        raise HTTPException(status_code=500, detail="Error creando obligación")


@router.get("/obligations/{obligation_id}", response_model=ObligationResponse)
async def get_obligation(
    household_id: UUID,
    obligation_id: UUID,
    user: User = Depends(verify_household_membership)
) -> ObligationResponse:
    """Obtiene una obligación por ID."""
    try:
        household_id, user = user
        
        obligation_data = await obligations_repo.get_obligation_by_id(obligation_id, user)
        if not obligation_data:
            raise NotFoundError("Obligación", str(obligation_id))
        
        return ObligationResponse(**obligation_data)
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Error obteniendo obligación", obligation_id=str(obligation_id), error=str(e))
        raise HTTPException(status_code=500, detail="Error obteniendo obligación")


@router.post("/obligations/{obligation_id}/payments", response_model=ObligationPaymentResponse)
async def create_payment(
    household_id: UUID,
    obligation_id: UUID,
    request: ObligationPaymentCreate,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    user: User = Depends(verify_household_membership)
) -> ObligationPaymentResponse:
    """Crea un pago de obligación con efecto atómico."""
    try:
        household_id, user = user
        
        # Verificar idempotencia
        request_body = request.dict()
        is_duplicate, cached_response = await idempotency_service.check_idempotency(
            key=idempotency_key,
            user_id=user.id,
            household_id=household_id,
            request_body=request_body
        )
        
        if is_duplicate:
            return ObligationPaymentResponse(**cached_response)
        
        # Crear pago
        result = await payments_service.create_payment(
            household_id=household_id,
            obligation_id=obligation_id,
            amount=request.amount,
            from_account_id=request.from_account_id,
            occurred_at=request.occurred_at,
            description=request.description,
            user=user
        )
        
        payment_response = ObligationPaymentResponse(**result["payment"])
        
        # Almacenar resultado para idempotencia
        await idempotency_service.store_idempotency_result(
            key=idempotency_key,
            user_id=user.id,
            household_id=household_id,
            request_body=request_body,
            response_status=201,
            response_body=payment_response.dict()
        )
        
        return payment_response
        
    except IdempotencyError:
        raise
    except Exception as e:
        logger.error("Error creando pago", obligation_id=str(obligation_id), error=str(e))
        raise HTTPException(status_code=500, detail="Error creando pago")


@router.post("/obligations/{obligation_id}:close", response_model=ObligationActionResponse)
async def close_obligation(
    household_id: UUID,
    obligation_id: UUID,
    user: User = Depends(verify_household_membership)
) -> ObligationActionResponse:
    """Cierra una obligación."""
    try:
        household_id, user = user
        
        obligation_data = await obligations_repo.update_obligation_status(obligation_id, "completed", user)
        if not obligation_data:
            raise NotFoundError("Obligación", str(obligation_id))
        
        return ObligationActionResponse(
            message="Obligación cerrada exitosamente",
            obligation=ObligationResponse(**obligation_data)
        )
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Error cerrando obligación", obligation_id=str(obligation_id), error=str(e))
        raise HTTPException(status_code=500, detail="Error cerrando obligación")


@router.post("/obligations/{obligation_id}:reopen", response_model=ObligationActionResponse)
async def reopen_obligation(
    household_id: UUID,
    obligation_id: UUID,
    user: User = Depends(verify_household_membership)
) -> ObligationActionResponse:
    """Reabre una obligación."""
    try:
        household_id, user = user
        
        obligation_data = await obligations_repo.update_obligation_status(obligation_id, "active", user)
        if not obligation_data:
            raise NotFoundError("Obligación", str(obligation_id))
        
        return ObligationActionResponse(
            message="Obligación reabierta exitosamente",
            obligation=ObligationResponse(**obligation_data)
        )
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Error reabriendo obligación", obligation_id=str(obligation_id), error=str(e))
        raise HTTPException(status_code=500, detail="Error reabriendo obligación")


@router.post("/obligations/{obligation_id}:renew", response_model=ObligationActionResponse)
async def renew_obligation(
    household_id: UUID,
    obligation_id: UUID,
    user: User = Depends(verify_household_membership)
) -> ObligationActionResponse:
    """Crea nueva instancia de obligación recurrente."""
    try:
        household_id, user = user
        
        result = await recurrence_service.renew_obligation(obligation_id, user)
        
        return ObligationActionResponse(
            message="Nueva instancia de obligación recurrente creada",
            obligation=ObligationResponse(**result["new_obligation"])
        )
        
    except Exception as e:
        logger.error("Error renovando obligación", obligation_id=str(obligation_id), error=str(e))
        raise HTTPException(status_code=500, detail="Error renovando obligación")
