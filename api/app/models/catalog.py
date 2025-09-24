"""Modelos para catálogos (categorías y cuentas)."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field
from .base import BaseModelWithTimestamps, TransactionKind, AccountType


class CategoryCreate(BaseModel):
    """Crear categoría."""
    name: str = Field(..., min_length=1, max_length=100)
    kind: TransactionKind
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, max_length=50)


class CategoryUpdate(BaseModel):
    """Actualizar categoría."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, max_length=50)


class CategoryResponse(BaseModelWithTimestamps):
    """Response de categoría."""
    id: UUID
    household_id: UUID
    name: str
    kind: TransactionKind
    description: Optional[str]
    color: Optional[str]
    icon: Optional[str]


class AccountCreate(BaseModel):
    """Crear cuenta."""
    name: str = Field(..., min_length=1, max_length=100)
    account_type: AccountType
    currency: str = Field(..., min_length=3, max_length=3)
    initial_balance: Optional[str] = Field("0", pattern=r"^-?\d+(\.\d{1,2})?$")
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, max_length=50)


class AccountUpdate(BaseModel):
    """Actualizar cuenta."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, max_length=50)


class AccountResponse(BaseModelWithTimestamps):
    """Response de cuenta."""
    id: UUID
    household_id: UUID
    name: str
    account_type: AccountType
    currency: str
    balance: str
    description: Optional[str]
    color: Optional[str]
    icon: Optional[str]


class CategoryListResponse(BaseModel):
    """Lista de categorías."""
    categories: List[CategoryResponse]


class AccountListResponse(BaseModel):
    """Lista de cuentas."""
    accounts: List[AccountResponse]
