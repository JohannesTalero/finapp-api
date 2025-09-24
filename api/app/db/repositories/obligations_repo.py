"""Repositorio para gestión de obligaciones."""

from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal

from .base_repository import BaseRepository
from ...core.security import User


class ObligationsRepository(BaseRepository):
    """Repositorio para obligaciones."""
    
    def __init__(self):
        super().__init__("obligations")
    
    async def create_obligation(
        self,
        household_id: UUID,
        name: str,
        total_amount: Decimal,
        outstanding_amount: Decimal,
        due_date: Optional[date] = None,
        description: Optional[str] = None,
        priority: str = "medium",
        creditor: Optional[str] = None,
        is_recurring: bool = False,
        recurrence_pattern: Optional[str] = None,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """Crea una nueva obligación."""
        data = {
            "household_id": str(household_id),
            "name": name,
            "total_amount": str(total_amount),
            "outstanding_amount": str(outstanding_amount),
            "due_date": due_date.isoformat() if due_date else None,
            "description": description,
            "priority": priority,
            "creditor": creditor,
            "is_recurring": is_recurring,
            "recurrence_pattern": recurrence_pattern,
            "status": "active",
            "created_at": "now()",
            "updated_at": "now()"
        }
        return await self.create(data, user)
    
    async def get_obligations_by_household(
        self,
        household_id: UUID,
        status: Optional[str] = None,
        due_before: Optional[date] = None,
        priority: Optional[str] = None,
        is_recurring: Optional[bool] = None,
        cursor: Optional[str] = None,
        limit: int = 20,
        user: Optional[User] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Obtiene obligaciones de un hogar con paginación cursor-based."""
        client = self._get_client(user)
        
        try:
            query = client.table(self.table_name).select("*")
            
            # Filtros obligatorios
            query = query.eq("household_id", str(household_id))
            
            # Filtros opcionales
            if status:
                query = query.eq("status", status)
            if due_before:
                query = query.lte("due_date", due_before.isoformat())
            if priority:
                query = query.eq("priority", priority)
            if is_recurring is not None:
                query = query.eq("is_recurring", is_recurring)
            
            # Ordenamiento
            query = query.order("due_date.asc")
            
            # Paginación cursor-based
            if cursor:
                query = query.lt("created_at", cursor)
            
            # Límite
            query = query.limit(limit + 1)
            
            result = query.execute()
            obligations = result.data or []
            
            # Determinar next_cursor
            next_cursor = None
            if len(obligations) > limit:
                obligations = obligations[:limit]
                next_cursor = obligations[-1]["created_at"]
            
            return obligations, next_cursor
            
        except Exception as e:
            self.logger.error("Error obteniendo obligaciones", error=str(e), household_id=str(household_id))
            raise
    
    async def get_obligation_by_id(
        self,
        obligation_id: UUID,
        user: Optional[User] = None
    ) -> Optional[Dict[str, Any]]:
        """Obtiene una obligación por ID."""
        return await self.get_by_id(obligation_id, user)
    
    async def update_obligation(
        self,
        obligation_id: UUID,
        name: Optional[str] = None,
        total_amount: Optional[Decimal] = None,
        outstanding_amount: Optional[Decimal] = None,
        due_date: Optional[date] = None,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        creditor: Optional[str] = None,
        user: Optional[User] = None
    ) -> Optional[Dict[str, Any]]:
        """Actualiza una obligación."""
        data = {"updated_at": "now()"}
        
        if name is not None:
            data["name"] = name
        if total_amount is not None:
            data["total_amount"] = str(total_amount)
        if outstanding_amount is not None:
            data["outstanding_amount"] = str(outstanding_amount)
        if due_date is not None:
            data["due_date"] = due_date.isoformat()
        if description is not None:
            data["description"] = description
        if priority is not None:
            data["priority"] = priority
        if creditor is not None:
            data["creditor"] = creditor
        
        return await self.update(obligation_id, data, user)
    
    async def update_obligation_status(
        self,
        obligation_id: UUID,
        status: str,
        user: Optional[User] = None
    ) -> Optional[Dict[str, Any]]:
        """Actualiza el estado de una obligación."""
        data = {
            "status": status,
            "updated_at": "now()"
        }
        
        if status == "completed":
            data["completed_at"] = "now()"
        elif status == "active":
            data["completed_at"] = None
        
        return await self.update(obligation_id, data, user)
    
    async def add_payment(
        self,
        obligation_id: UUID,
        amount: Decimal,
        user: Optional[User] = None
    ) -> Optional[Dict[str, Any]]:
        """Agrega un pago a una obligación."""
        obligation = await self.get_obligation_by_id(obligation_id, user)
        if not obligation:
            return None
        
        outstanding_amount = Decimal(obligation["outstanding_amount"])
        new_amount = outstanding_amount - amount
        
        return await self.update_obligation(obligation_id, outstanding_amount=new_amount, user=user)
    
    async def delete_obligation(
        self,
        obligation_id: UUID,
        user: Optional[User] = None
    ) -> bool:
        """Elimina una obligación."""
        return await self.delete(obligation_id, user)
    
    async def get_obligation_payments(
        self,
        obligation_id: UUID,
        user: Optional[User] = None
    ) -> List[Dict[str, Any]]:
        """Obtiene los pagos de una obligación."""
        client = self._get_client(user)
        
        try:
            result = client.table("obligation_payments").select(
                "*, transactions(*)"
            ).eq("obligation_id", str(obligation_id)).order("created_at.desc").execute()
            
            return result.data or []
        except Exception as e:
            self.logger.error("Error obteniendo pagos de obligación", error=str(e), obligation_id=str(obligation_id))
            raise
