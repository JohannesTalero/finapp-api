"""Repositorio para gestión de metas."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal

from .base_repository import BaseRepository
from ...core.security import User


class GoalsRepository(BaseRepository):
    """Repositorio para metas."""
    
    def __init__(self):
        super().__init__("goals")
    
    async def create_goal(
        self,
        household_id: UUID,
        name: str,
        target_amount: Decimal,
        current_amount: Decimal = Decimal("0"),
        target_date: Optional[date] = None,
        description: Optional[str] = None,
        priority: str = "medium",
        is_recurring: bool = False,
        recurrence_pattern: Optional[str] = None,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """Crea una nueva meta."""
        data = {
            "household_id": str(household_id),
            "name": name,
            "target_amount": str(target_amount),
            "current_amount": str(current_amount),
            "target_date": target_date.isoformat() if target_date else None,
            "description": description,
            "priority": priority,
            "is_recurring": is_recurring,
            "recurrence_pattern": recurrence_pattern,
            "status": "active",
            "created_at": "now()",
            "updated_at": "now()"
        }
        return await self.create(data, user)
    
    async def get_goals_by_household(
        self,
        household_id: UUID,
        status: Optional[str] = None,
        is_recurring: Optional[bool] = None,
        cursor: Optional[str] = None,
        limit: int = 20,
        user: Optional[User] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Obtiene metas de un hogar con paginación cursor-based."""
        client = self._get_client(user)
        
        try:
            query = client.table(self.table_name).select("*")
            
            # Filtros obligatorios
            query = query.eq("household_id", str(household_id))
            
            # Filtros opcionales
            if status:
                query = query.eq("status", status)
            if is_recurring is not None:
                query = query.eq("is_recurring", is_recurring)
            
            # Ordenamiento
            query = query.order("created_at.desc")
            
            # Paginación cursor-based
            if cursor:
                query = query.lt("created_at", cursor)
            
            # Límite
            query = query.limit(limit + 1)
            
            result = query.execute()
            goals = result.data or []
            
            # Determinar next_cursor
            next_cursor = None
            if len(goals) > limit:
                goals = goals[:limit]
                next_cursor = goals[-1]["created_at"]
            
            return goals, next_cursor
            
        except Exception as e:
            self.logger.error("Error obteniendo metas", error=str(e), household_id=str(household_id))
            raise
    
    async def get_goal_by_id(
        self,
        goal_id: UUID,
        user: Optional[User] = None
    ) -> Optional[Dict[str, Any]]:
        """Obtiene una meta por ID."""
        return await self.get_by_id(goal_id, user)
    
    async def update_goal(
        self,
        goal_id: UUID,
        name: Optional[str] = None,
        target_amount: Optional[Decimal] = None,
        current_amount: Optional[Decimal] = None,
        target_date: Optional[date] = None,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        user: Optional[User] = None
    ) -> Optional[Dict[str, Any]]:
        """Actualiza una meta."""
        data = {"updated_at": "now()"}
        
        if name is not None:
            data["name"] = name
        if target_amount is not None:
            data["target_amount"] = str(target_amount)
        if current_amount is not None:
            data["current_amount"] = str(current_amount)
        if target_date is not None:
            data["target_date"] = target_date.isoformat()
        if description is not None:
            data["description"] = description
        if priority is not None:
            data["priority"] = priority
        
        return await self.update(goal_id, data, user)
    
    async def update_goal_status(
        self,
        goal_id: UUID,
        status: str,
        user: Optional[User] = None
    ) -> Optional[Dict[str, Any]]:
        """Actualiza el estado de una meta."""
        data = {
            "status": status,
            "updated_at": "now()"
        }
        
        if status == "completed":
            data["completed_at"] = "now()"
        elif status == "active":
            data["completed_at"] = None
        
        return await self.update(goal_id, data, user)
    
    async def add_contribution(
        self,
        goal_id: UUID,
        amount: Decimal,
        user: Optional[User] = None
    ) -> Optional[Dict[str, Any]]:
        """Agrega un aporte a una meta."""
        goal = await self.get_goal_by_id(goal_id, user)
        if not goal:
            return None
        
        current_amount = Decimal(goal["current_amount"])
        new_amount = current_amount + amount
        
        return await self.update_goal(goal_id, current_amount=new_amount, user=user)
    
    async def delete_goal(
        self,
        goal_id: UUID,
        user: Optional[User] = None
    ) -> bool:
        """Elimina una meta."""
        return await self.delete(goal_id, user)
    
    async def get_goal_contributions(
        self,
        goal_id: UUID,
        user: Optional[User] = None
    ) -> List[Dict[str, Any]]:
        """Obtiene los aportes de una meta."""
        client = self._get_client(user)
        
        try:
            result = client.table("goal_contributions").select(
                "*, transactions(*)"
            ).eq("goal_id", str(goal_id)).order("created_at.desc").execute()
            
            return result.data or []
        except Exception as e:
            self.logger.error("Error obteniendo aportes de meta", error=str(e), goal_id=str(goal_id))
            raise
