"""Repositorio para gestión de cuentas."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from decimal import Decimal

from .base_repository import BaseRepository
from ...core.security import User


class AccountsRepository(BaseRepository):
    """Repositorio para cuentas."""
    
    def __init__(self):
        super().__init__("accounts")
    
    async def create_account(
        self,
        household_id: UUID,
        name: str,
        account_type: str,
        currency: str,
        initial_balance: Optional[Decimal] = None,
        description: Optional[str] = None,
        color: Optional[str] = None,
        icon: Optional[str] = None,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """Crea una nueva cuenta."""
        data = {
            "household_id": str(household_id),
            "name": name,
            "account_type": account_type,
            "currency": currency,
            "balance": str(initial_balance) if initial_balance is not None else "0",
            "description": description,
            "color": color,
            "icon": icon,
            "created_at": "now()",
            "updated_at": "now()"
        }
        return await self.create(data, user)
    
    async def get_accounts_by_household(
        self,
        household_id: UUID,
        account_type: Optional[str] = None,
        user: Optional[User] = None
    ) -> List[Dict[str, Any]]:
        """Obtiene cuentas de un hogar."""
        filters = {"household_id": str(household_id)}
        if account_type:
            filters["account_type"] = account_type
        
        return await self.list(
            filters=filters,
            order_by="name.asc",
            user=user
        )
    
    async def get_account_by_id(
        self,
        account_id: UUID,
        user: Optional[User] = None
    ) -> Optional[Dict[str, Any]]:
        """Obtiene una cuenta por ID."""
        return await self.get_by_id(account_id, user)
    
    async def update_account(
        self,
        account_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[str] = None,
        icon: Optional[str] = None,
        user: Optional[User] = None
    ) -> Optional[Dict[str, Any]]:
        """Actualiza una cuenta."""
        data = {"updated_at": "now()"}
        
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if color is not None:
            data["color"] = color
        if icon is not None:
            data["icon"] = icon
        
        return await self.update(account_id, data, user)
    
    async def update_account_balance(
        self,
        account_id: UUID,
        new_balance: Decimal,
        user: Optional[User] = None
    ) -> Optional[Dict[str, Any]]:
        """Actualiza el balance de una cuenta."""
        data = {
            "balance": str(new_balance),
            "updated_at": "now()"
        }
        return await self.update(account_id, data, user)
    
    async def delete_account(
        self,
        account_id: UUID,
        user: Optional[User] = None
    ) -> bool:
        """Elimina una cuenta."""
        return await self.delete(account_id, user)
    
    async def get_account_balance(
        self,
        account_id: UUID,
        user: Optional[User] = None
    ) -> Optional[Decimal]:
        """Obtiene el balance actual de una cuenta."""
        account = await self.get_account_by_id(account_id, user)
        if account:
            return Decimal(account["balance"])
        return None
    
    async def get_account_transactions_count(
        self,
        account_id: UUID,
        user: Optional[User] = None
    ) -> int:
        """Cuenta cuántas transacciones tiene esta cuenta."""
        client = self._get_client(user)
        
        try:
            result = client.table("transactions").select("id", count="exact").or_(
                f"account_id.eq.{account_id},from_account_id.eq.{account_id},to_account_id.eq.{account_id}"
            ).execute()
            
            return result.count or 0
        except Exception as e:
            self.logger.error("Error contando transacciones de cuenta", error=str(e), account_id=str(account_id))
            raise
