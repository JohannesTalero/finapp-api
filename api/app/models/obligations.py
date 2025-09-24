"""Modelos para obligaciones."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal

from pydantic import BaseModel, Field
from .base import BaseModelWithTimestamps, Priority, Status, RecurrencePattern, PaginationParams, PaginatedResponse


class ObligationCreate(BaseModel):
    """Crear obligación."""
    name: str = Field(..., min_length=1, max_length=100)
    total_amount: str = Field(..., pattern=r"^\d+(\.\d{1,2})?$")
    outstanding_amount: str = Field(..., pattern=r"^\d+(\.\d{1,2})?$")
    due_date: Optional[date] = None
    description: Optional[str] = Field(None, max_length=500)
    priority: Priority = Priority.MEDIUM
    creditor: Optional[str] = Field(None, max_length=100)
    is_recurring: bool = False
    recurrence_pattern: Optional[RecurrencePattern] = None


class ObligationUpdate(BaseModel):
    """Actualizar obligación."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    total_amount: Optional[str] = Field(None, pattern=r"^\d+(\.\d{1,2})?$")
    outstanding_amount: Optional[str] = Field(None, pattern=r"^\d+(\.\d{1,2})?$")
    due_date: Optional[date] = None
    description: Optional[str] = Field(None, max_length=500)
    priority: Optional[Priority] = None
    creditor: Optional[str] = Field(None, max_length=100)


class ObligationResponse(BaseModelWithTimestamps):
    """Response de obligación."""
    id: UUID
    household_id: UUID
    name: str
    total_amount: str
    outstanding_amount: str
    due_date: Optional[date]
    description: Optional[str]
    priority: Priority
    creditor: Optional[str]
    is_recurring: bool
    recurrence_pattern: Optional[RecurrencePattern]
    status: Status
    completed_at: Optional[datetime]


class ObligationListParams(PaginationParams):
    """Parámetros para listar obligaciones."""
    status: Optional[Status] = None
    due_before: Optional[date] = None
    priority: Optional[Priority] = None
    is_recurring: Optional[bool] = None


class ObligationListResponse(PaginatedResponse):
    """Lista de obligaciones."""
    data: List[ObligationResponse]


class ObligationPaymentCreate(BaseModel):
    """Crear pago de obligación."""
    amount: str = Field(..., pattern=r"^\d+(\.\d{1,2})?$")
    from_account_id: UUID
    occurred_at: Optional[datetime] = None
    description: Optional[str] = Field(None, max_length=500)


class ObligationPaymentResponse(BaseModel):
    """Response de pago de obligación."""
    id: UUID
    obligation_id: UUID
    transaction_id: UUID
    amount: str
    created_at: datetime
    transaction: Optional[dict] = None


class ObligationPaymentListResponse(BaseModel):
    """Lista de pagos de obligación."""
    payments: List[ObligationPaymentResponse]


class ObligationActionResponse(BaseModel):
    """Response de acción en obligación."""
    success: bool = True
    message: str
    obligation: Optional[ObligationResponse] = None
