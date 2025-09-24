"""Router para reportes y análisis."""

from typing import List
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query

from ..core.security import User, get_current_user
from ..core.logging import get_logger
from ..deps import verify_household_membership
from ..db.repositories.reports_repo import ReportsRepository
from ..models.reports import (
    AccountBalancesResponse, CashflowParams, CashflowResponse,
    CategoryAnalysisParams, CategoryAnalysisListResponse,
    DashboardResponse, MonthlySummaryParams, MonthlySummaryResponse
)

logger = get_logger(__name__)

router = APIRouter(prefix="/v1/households/{household_id}", tags=["reportes"])
reports_repo = ReportsRepository()


@router.get("/balances", response_model=AccountBalancesResponse)
async def get_account_balances(
    household_id: UUID,
    user: User = Depends(verify_household_membership)
) -> AccountBalancesResponse:
    """Obtiene balances de cuentas usando vista v_account_balances."""
    try:
        household_id, user = user
        
        logger.info("Obteniendo balances de cuentas", household_id=str(household_id), user_id=str(user.id))
        
        balances_data = await reports_repo.get_account_balances(household_id, user)
        
        logger.info("Balances obtenidos", count=len(balances_data), household_id=str(household_id))
        
        return AccountBalancesResponse(balances=balances_data)
        
    except Exception as e:
        logger.error("Error obteniendo balances", household_id=str(household_id), error=str(e))
        raise HTTPException(status_code=500, detail="Error obteniendo balances")


@router.get("/cashflow", response_model=CashflowResponse)
async def get_cashflow(
    household_id: UUID,
    params: CashflowParams = Depends(),
    user: User = Depends(verify_household_membership)
) -> CashflowResponse:
    """Obtiene flujo de efectivo agrupado por período."""
    try:
        household_id, user = user
        
        logger.info(
            "Obteniendo cashflow",
            household_id=str(household_id),
            from_date=params.from_date.isoformat(),
            to_date=params.to_date.isoformat(),
            group_by=params.group_by,
            user_id=str(user.id)
        )
        
        cashflow_data = await reports_repo.get_cashflow(
            household_id=household_id,
            from_date=params.from_date,
            to_date=params.to_date,
            group_by=params.group_by,
            user=user
        )
        
        logger.info("Cashflow obtenido", count=len(cashflow_data), household_id=str(household_id))
        
        return CashflowResponse(cashflow=cashflow_data)
        
    except Exception as e:
        logger.error("Error obteniendo cashflow", household_id=str(household_id), error=str(e))
        raise HTTPException(status_code=500, detail="Error obteniendo cashflow")


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    household_id: UUID,
    user: User = Depends(verify_household_membership)
) -> DashboardResponse:
    """Obtiene datos para el dashboard."""
    try:
        household_id, user = user
        
        logger.info("Obteniendo datos del dashboard", household_id=str(household_id), user_id=str(user.id))
        
        dashboard_data = await reports_repo.get_dashboard_data(household_id, user)
        
        logger.info("Datos del dashboard obtenidos", household_id=str(household_id))
        
        return DashboardResponse(**dashboard_data)
        
    except Exception as e:
        logger.error("Error obteniendo datos del dashboard", household_id=str(household_id), error=str(e))
        raise HTTPException(status_code=500, detail="Error obteniendo datos del dashboard")


@router.get("/categories/analysis", response_model=CategoryAnalysisListResponse)
async def get_category_analysis(
    household_id: UUID,
    params: CategoryAnalysisParams = Depends(),
    user: User = Depends(verify_household_membership)
) -> CategoryAnalysisListResponse:
    """Obtiene análisis por categorías."""
    try:
        household_id, user = user
        
        logger.info(
            "Obteniendo análisis de categorías",
            household_id=str(household_id),
            from_date=params.from_date.isoformat(),
            to_date=params.to_date.isoformat(),
            kind=params.kind,
            user_id=str(user.id)
        )
        
        categories_data = await reports_repo.get_category_analysis(
            household_id=household_id,
            from_date=params.from_date,
            to_date=params.to_date,
            kind=params.kind,
            user=user
        )
        
        logger.info("Análisis de categorías obtenido", count=len(categories_data), household_id=str(household_id))
        
        return CategoryAnalysisListResponse(categories=categories_data)
        
    except Exception as e:
        logger.error("Error obteniendo análisis de categorías", household_id=str(household_id), error=str(e))
        raise HTTPException(status_code=500, detail="Error obteniendo análisis de categorías")


@router.get("/monthly-summary", response_model=MonthlySummaryResponse)
async def get_monthly_summary(
    household_id: UUID,
    params: MonthlySummaryParams = Depends(),
    user: User = Depends(verify_household_membership)
) -> MonthlySummaryResponse:
    """Obtiene resumen mensual."""
    try:
        household_id, user = user
        
        logger.info(
            "Obteniendo resumen mensual",
            household_id=str(household_id),
            year=params.year,
            month=params.month,
            user_id=str(user.id)
        )
        
        summary_data = await reports_repo.get_monthly_summary(
            household_id=household_id,
            year=params.year,
            month=params.month,
            user=user
        )
        
        logger.info("Resumen mensual obtenido", household_id=str(household_id))
        
        return MonthlySummaryResponse(**summary_data)
        
    except Exception as e:
        logger.error("Error obteniendo resumen mensual", household_id=str(household_id), error=str(e))
        raise HTTPException(status_code=500, detail="Error obteniendo resumen mensual")
