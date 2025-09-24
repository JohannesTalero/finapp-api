"""Router para gestión de metas."""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Header

from ..core.security import User, get_current_user
from ..core.logging import get_logger
from ..core.errors import NotFoundError, IdempotencyError
from ..deps import verify_household_membership, get_idempotency_key
from ..db.repositories.goals_repo import GoalsRepository
from ..services.contributions_service import contributions_service
from ..services.idempotency_service import idempotency_service
from ..services.recurrence_service import recurrence_service
from ..models.goals import (
    GoalCreate, GoalUpdate, GoalResponse, GoalListParams, GoalListResponse,
    GoalContributionCreate, GoalContributionResponse, GoalActionResponse
)

logger = get_logger(__name__)

router = APIRouter(prefix="/v1/households/{household_id}", tags=["metas"])
goals_repo = GoalsRepository()


@router.get("/goals", response_model=GoalListResponse)
async def get_goals(
    household_id: UUID,
    params: GoalListParams = Depends(),
    user: User = Depends(verify_household_membership)
) -> GoalListResponse:
    """Obtiene metas de un hogar con paginación cursor-based."""
    try:
        household_id, user = user
        
        goals_data, next_cursor = await goals_repo.get_goals_by_household(
            household_id=household_id,
            status=params.status,
            is_recurring=params.is_recurring,
            cursor=params.cursor,
            limit=params.limit,
            user=user
        )
        
        goals = [GoalResponse(**g) for g in goals_data]
        
        return GoalListResponse(data=goals, next_cursor=next_cursor)
        
    except Exception as e:
        logger.error("Error obteniendo metas", household_id=str(household_id), error=str(e))
        raise HTTPException(status_code=500, detail="Error obteniendo metas")


@router.post("/goals", response_model=GoalResponse)
async def create_goal(
    household_id: UUID,
    request: GoalCreate,
    user: User = Depends(verify_household_membership)
) -> GoalResponse:
    """Crea una nueva meta."""
    try:
        household_id, user = user
        
        goal_data = await goals_repo.create_goal(
            household_id=household_id,
            name=request.name,
            target_amount=request.target_amount,
            current_amount=request.current_amount,
            target_date=request.target_date,
            description=request.description,
            priority=request.priority,
            is_recurring=request.is_recurring,
            recurrence_pattern=request.recurrence_pattern,
            user=user
        )
        
        return GoalResponse(**goal_data)
        
    except Exception as e:
        logger.error("Error creando meta", household_id=str(household_id), error=str(e))
        raise HTTPException(status_code=500, detail="Error creando meta")


@router.get("/goals/{goal_id}", response_model=GoalResponse)
async def get_goal(
    household_id: UUID,
    goal_id: UUID,
    user: User = Depends(verify_household_membership)
) -> GoalResponse:
    """Obtiene una meta por ID."""
    try:
        household_id, user = user
        
        goal_data = await goals_repo.get_goal_by_id(goal_id, user)
        if not goal_data:
            raise NotFoundError("Meta", str(goal_id))
        
        return GoalResponse(**goal_data)
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Error obteniendo meta", goal_id=str(goal_id), error=str(e))
        raise HTTPException(status_code=500, detail="Error obteniendo meta")


@router.post("/goals/{goal_id}/contributions", response_model=GoalContributionResponse)
async def create_contribution(
    household_id: UUID,
    goal_id: UUID,
    request: GoalContributionCreate,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    user: User = Depends(verify_household_membership)
) -> GoalContributionResponse:
    """Crea un aporte a una meta con efecto atómico."""
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
            return GoalContributionResponse(**cached_response)
        
        # Crear aporte
        result = await contributions_service.create_contribution(
            household_id=household_id,
            goal_id=goal_id,
            amount=request.amount,
            source_account_id=request.source_account_id,
            occurred_at=request.occurred_at,
            description=request.description,
            user=user
        )
        
        contribution_response = GoalContributionResponse(**result["contribution"])
        
        # Almacenar resultado para idempotencia
        await idempotency_service.store_idempotency_result(
            key=idempotency_key,
            user_id=user.id,
            household_id=household_id,
            request_body=request_body,
            response_status=201,
            response_body=contribution_response.dict()
        )
        
        return contribution_response
        
    except IdempotencyError:
        raise
    except Exception as e:
        logger.error("Error creando aporte", goal_id=str(goal_id), error=str(e))
        raise HTTPException(status_code=500, detail="Error creando aporte")


@router.post("/goals/{goal_id}:close", response_model=GoalActionResponse)
async def close_goal(
    household_id: UUID,
    goal_id: UUID,
    user: User = Depends(verify_household_membership)
) -> GoalActionResponse:
    """Cierra una meta."""
    try:
        household_id, user = user
        
        goal_data = await goals_repo.update_goal_status(goal_id, "completed", user)
        if not goal_data:
            raise NotFoundError("Meta", str(goal_id))
        
        return GoalActionResponse(
            message="Meta cerrada exitosamente",
            goal=GoalResponse(**goal_data)
        )
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Error cerrando meta", goal_id=str(goal_id), error=str(e))
        raise HTTPException(status_code=500, detail="Error cerrando meta")


@router.post("/goals/{goal_id}:reopen", response_model=GoalActionResponse)
async def reopen_goal(
    household_id: UUID,
    goal_id: UUID,
    user: User = Depends(verify_household_membership)
) -> GoalActionResponse:
    """Reabre una meta."""
    try:
        household_id, user = user
        
        goal_data = await goals_repo.update_goal_status(goal_id, "active", user)
        if not goal_data:
            raise NotFoundError("Meta", str(goal_id))
        
        return GoalActionResponse(
            message="Meta reabierta exitosamente",
            goal=GoalResponse(**goal_data)
        )
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Error reabriendo meta", goal_id=str(goal_id), error=str(e))
        raise HTTPException(status_code=500, detail="Error reabriendo meta")


@router.post("/goals/{goal_id}:rollover", response_model=GoalActionResponse)
async def rollover_goal(
    household_id: UUID,
    goal_id: UUID,
    user: User = Depends(verify_household_membership)
) -> GoalActionResponse:
    """Crea nueva instancia de meta recurrente."""
    try:
        household_id, user = user
        
        result = await recurrence_service.rollover_goal(goal_id, user)
        
        return GoalActionResponse(
            message="Nueva instancia de meta recurrente creada",
            goal=GoalResponse(**result["new_goal"])
        )
        
    except Exception as e:
        logger.error("Error haciendo rollover de meta", goal_id=str(goal_id), error=str(e))
        raise HTTPException(status_code=500, detail="Error haciendo rollover de meta")
