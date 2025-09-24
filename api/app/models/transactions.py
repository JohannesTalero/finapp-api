"""Modelos para transacciones."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal

from pydantic import BaseModel, Field, validator
from .base import BaseModelWithTimestamps, TransactionKind, PaginationParams, PaginatedResponse


class TransactionCreate(BaseModel):
    """Crear transacción."""
    kind: TransactionKind
    amount: str = Field(..., regex=r"^\d+(\.\d{1,2})?$")
    account_id: Optional[UUID] = None
    from_account_id: Optional[UUID] = None
    to_account_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    occurred_at: Optional[datetime] = None
    description: Optional[str] = Field(None, max_length=500)
    counterparty: Optional[str] = Field(None, max_length=100)
    
    @validator('account_id', 'from_account_id', 'to_account_id')
    def validate_account_ids(cls, v, values):
        """Valida que se proporcionen las cuentas correctas según el tipo."""
        kind = values.get('kind')
        
        if kind == TransactionKind.TRANSFER:
            if not values.get('from_account_id') or not values.get('to_account_id'):
                raise ValueError('Transferencias requieren from_account_id y to_account_id')
            if values.get('from_account_id') == values.get('to_account_id'):
                raise ValueError('from_account_id y to_account_id deben ser diferentes')
        else:
            if not values.get('account_id'):
                raise ValueError('Ingresos y gastos requieren account_id')
        
        return v


class TransactionUpdate(BaseModel):
    """Actualizar transacción."""
    amount: Optional[str] = Field(None, regex=r"^\d+(\.\d{1,2})?$")
    category_id: Optional[UUID] = None
    occurred_at: Optional[datetime] = None
    description: Optional[str] = Field(None, max_length=500)
    counterparty: Optional[str] = Field(None, max_length=100)


class TransactionResponse(BaseModelWithTimestamps):
    """Response de transacción."""
    id: UUID
    household_id: UUID
    kind: TransactionKind
    amount: str
    account_id: Optional[UUID]
    from_account_id: Optional[UUID]
    to_account_id: Optional[UUID]
    category_id: Optional[UUID]
    occurred_at: datetime
    description: Optional[str]
    counterparty: Optional[str]


class TransactionListParams(PaginationParams):
    """Parámetros para listar transacciones."""
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    kind: Optional[TransactionKind] = None
    category_id: Optional[UUID] = None
    account_id: Optional[UUID] = None
    search: Optional[str] = Field(None, max_length=100)
    sort: str = Field(default="occurred_at")
    order: str = Field(default="desc", regex=r"^(asc|desc)$")


class TransactionListResponse(PaginatedResponse):
    """Lista de transacciones."""
    data: List[TransactionResponse]


class TransactionSummaryResponse(BaseModel):
    """Resumen de transacciones."""
    total_income: str
    total_expense: str
    total_transfer: str
    transaction_count: int
