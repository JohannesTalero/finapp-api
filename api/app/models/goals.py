"""Modelos para metas."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal

from pydantic import BaseModel, Field
from .base import BaseModelWithTimestamps, Priority, Status, RecurrencePattern, PaginationParams, PaginatedResponse


class GoalCreate(BaseModel):
    """Crear meta."""
    name: str = Field(..., min_length=1, max_length=100)
    target_amount: str = Field(..., regex=r"^\d+(\.\d{1,2})?$")
    current_amount: str = Field("0", regex=r"^\d+(\.\d{1,2})?$")
    target_date: Optional[date] = None
    description: Optional[str] = Field(None, max_length=500)
    priority: Priority = Priority.MEDIUM
    is_recurring: bool = False
    recurrence_pattern: Optional[RecurrencePattern] = None


class GoalUpdate(BaseModel):
    """Actualizar meta."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    target_amount: Optional[str] = Field(None, regex=r"^\d+(\.\d{1,2})?$")
    current_amount: Optional[str] = Field(None, regex=r"^\d+(\.\d{1,2})?$")
    target_date: Optional[date] = None
    description: Optional[str] = Field(None, max_length=500)
    priority: Optional[Priority] = None


class GoalResponse(BaseModelWithTimestamps):
    """Response de meta."""
    id: UUID
    household_id: UUID
    name: str
    target_amount: str
    current_amount: str
    target_date: Optional[date]
    description: Optional[str]
    priority: Priority
    is_recurring: bool
    recurrence_pattern: Optional[RecurrencePattern]
    status: Status
    completed_at: Optional[datetime]


class GoalListParams(PaginationParams):
    """Parámetros para listar metas."""
    status: Optional[Status] = None
    is_recurring: Optional[bool] = None


class GoalListResponse(PaginatedResponse):
    """Lista de metas."""
    data: List[GoalResponse]


class GoalContributionCreate(BaseModel):
    """Crear aporte a meta."""
    amount: str = Field(..., regex=r"^\d+(\.\d{1,2})?$")
    source_account_id: UUID
    occurred_at: Optional[datetime] = None
    description: Optional[str] = Field(None, max_length=500)


class GoalContributionResponse(BaseModel):
    """Response de aporte a meta."""
    id: UUID
    goal_id: UUID
    transaction_id: UUID
    amount: str
    created_at: datetime
    transaction: Optional[dict] = None


class GoalContributionListResponse(BaseModel):
    """Lista de aportes a meta."""
    contributions: List[GoalContributionResponse]


class GoalActionResponse(BaseModel):
    """Response de acción en meta."""
    success: bool = True
    message: str
    goal: Optional[GoalResponse] = None
