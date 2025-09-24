"""Modelos base y tipos comunes."""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, validator


class TransactionKind(str, Enum):
    """Tipos de transacción."""
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"


class AccountType(str, Enum):
    """Tipos de cuenta."""
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT_CARD = "credit_card"
    INVESTMENT = "investment"
    CASH = "cash"
    OTHER = "other"


class Priority(str, Enum):
    """Prioridades."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Status(str, Enum):
    """Estados."""
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Role(str, Enum):
    """Roles de usuario en hogar."""
    VIEWER = "viewer"
    MEMBER = "member"
    ADMIN = "admin"
    OWNER = "owner"


class RecurrencePattern(str, Enum):
    """Patrones de recurrencia."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class BaseModelWithTimestamps(BaseModel):
    """Modelo base con timestamps."""
    created_at: datetime
    updated_at: datetime


class PaginationParams(BaseModel):
    """Parámetros de paginación."""
    cursor: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    """Respuesta paginada."""
    data: List[Dict[str, Any]]
    next_cursor: Optional[str] = None
    total_count: Optional[int] = None


class ErrorResponse(BaseModel):
    """Respuesta de error en formato Problem+JSON."""
    type: str
    title: str
    detail: str
    status: int
    instance: str
    fields: Optional[Dict[str, Any]] = None


class SuccessResponse(BaseModel):
    """Respuesta de éxito."""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
