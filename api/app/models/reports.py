"""Modelos para reportes."""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field
from .base import TransactionKind


class AccountBalanceResponse(BaseModel):
    """Balance de cuenta."""
    account_id: UUID
    account_name: str
    account_type: str
    currency: str
    balance: str
    color: Optional[str]
    icon: Optional[str]


class AccountBalancesResponse(BaseModel):
    """Balances de cuentas."""
    balances: List[AccountBalanceResponse]


class CashflowParams(BaseModel):
    """Parámetros para cashflow."""
    from_date: date
    to_date: date
    group_by: str = Field(default="month", pattern=r"^(day|week|month|year)$")


class CashflowItemResponse(BaseModel):
    """Item de cashflow."""
    period: str
    income: str
    expense: str
    net: str


class CashflowResponse(BaseModel):
    """Cashflow."""
    cashflow: List[CashflowItemResponse]


class CategoryAnalysisResponse(BaseModel):
    """Análisis por categoría."""
    category_id: UUID
    category_name: str
    kind: TransactionKind
    total_amount: str
    transaction_count: int
    percentage: float


class CategoryAnalysisParams(BaseModel):
    """Parámetros para análisis de categorías."""
    from_date: date
    to_date: date
    kind: Optional[TransactionKind] = None


class CategoryAnalysisListResponse(BaseModel):
    """Lista de análisis de categorías."""
    categories: List[CategoryAnalysisResponse]


class DashboardResponse(BaseModel):
    """Datos del dashboard."""
    account_balances: List[AccountBalanceResponse]
    top_categories: List[CategoryAnalysisResponse]
    upcoming_obligations: List[Dict[str, Any]]
    active_goals: List[Dict[str, Any]]


class MonthlySummaryParams(BaseModel):
    """Parámetros para resumen mensual."""
    year: int = Field(..., ge=2020, le=2030)
    month: int = Field(..., ge=1, le=12)


class MonthlySummaryResponse(BaseModel):
    """Resumen mensual."""
    year: int
    month: int
    total_income: str
    total_expense: str
    net_income: str
    transaction_count: int
    top_categories: List[CategoryAnalysisResponse]
