"""Servicio para manejo de recurrencia en metas y obligaciones."""

from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime, date, timedelta
from decimal import Decimal

from ..core.logging import get_logger
from ..core.errors import ValidationError
from ..core.security import User
from ..db.repositories.goals_repo import GoalsRepository
from ..db.repositories.obligations_repo import ObligationsRepository
from ..db.supabase_client import supabase_client

logger = get_logger(__name__)


class RecurrenceService:
    """Servicio para manejar recurrencia."""
    
    def __init__(self):
        self.goals_repo = GoalsRepository()
        self.obligations_repo = ObligationsRepository()
        self.client = supabase_client.service_client
    
    def _calculate_next_date(
        self,
        current_date: date,
        pattern: str,
        completed_at: Optional[datetime] = None
    ) -> date:
        """Calcula la próxima fecha basada en el patrón de recurrencia."""
        base_date = completed_at.date() if completed_at else current_date
        
        if pattern == "daily":
            return base_date + timedelta(days=1)
        elif pattern == "weekly":
            return base_date + timedelta(weeks=1)
        elif pattern == "monthly":
            # Agregar un mes manteniendo el día
            if base_date.month == 12:
                return base_date.replace(year=base_date.year + 1, month=1)
            else:
                return base_date.replace(month=base_date.month + 1)
        elif pattern == "quarterly":
            return base_date + timedelta(days=90)  # Aproximadamente 3 meses
        elif pattern == "yearly":
            return base_date.replace(year=base_date.year + 1)
        else:
            raise ValidationError(f"Patrón de recurrencia no válido: {pattern}")
    
    async def rollover_goal(
        self,
        goal_id: UUID,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        Crea una nueva instancia de una meta recurrente.
        
        Para metas recurrentes completadas, crea una nueva instancia
        con la próxima fecha objetivo basada en el patrón de recurrencia.
        """
        # Obtener la meta actual
        goal = await self.goals_repo.get_goal_by_id(goal_id, user)
        if not goal:
            raise ValidationError("Meta no encontrada")
        
        if not goal["is_recurring"]:
            raise ValidationError("La meta no es recurrente")
        
        if goal["status"] != "completed":
            raise ValidationError("La meta debe estar completada para hacer rollover")
        
        if not goal["recurrence_pattern"]:
            raise ValidationError("La meta recurrente debe tener un patrón de recurrencia")
        
        try:
            # Calcular próxima fecha objetivo
            current_target_date = None
            if goal["target_date"]:
                current_target_date = datetime.fromisoformat(goal["target_date"]).date()
            
            next_target_date = self._calculate_next_date(
                current_target_date or date.today(),
                goal["recurrence_pattern"],
                datetime.fromisoformat(goal["completed_at"]) if goal["completed_at"] else None
            )
            
            # Crear nueva instancia de la meta
            new_goal_data = {
                "household_id": goal["household_id"],
                "name": goal["name"],
                "target_amount": goal["target_amount"],
                "current_amount": "0",  # Resetear monto actual
                "target_date": next_target_date.isoformat(),
                "description": goal["description"],
                "priority": goal["priority"],
                "is_recurring": True,
                "recurrence_pattern": goal["recurrence_pattern"],
                "status": "active",
                "created_at": "now()",
                "updated_at": "now()"
            }
            
            result = self.client.table("goals").insert(new_goal_data).execute()
            
            if not result.data:
                raise Exception("Error creando nueva instancia de meta")
            
            new_goal = result.data[0]
            
            logger.info(
                "Meta recurrente creada",
                original_goal_id=str(goal_id),
                new_goal_id=new_goal["id"],
                next_target_date=next_target_date.isoformat(),
                pattern=goal["recurrence_pattern"]
            )
            
            return {
                "new_goal": new_goal,
                "next_target_date": next_target_date.isoformat(),
                "pattern": goal["recurrence_pattern"]
            }
            
        except Exception as e:
            logger.error(
                "Error haciendo rollover de meta",
                goal_id=str(goal_id),
                error=str(e)
            )
            raise
    
    async def renew_obligation(
        self,
        obligation_id: UUID,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        Crea una nueva instancia de una obligación recurrente.
        
        Para obligaciones recurrentes completadas, crea una nueva instancia
        con la próxima fecha de vencimiento basada en el patrón de recurrencia.
        """
        # Obtener la obligación actual
        obligation = await self.obligations_repo.get_obligation_by_id(obligation_id, user)
        if not obligation:
            raise ValidationError("Obligación no encontrada")
        
        if not obligation["is_recurring"]:
            raise ValidationError("La obligación no es recurrente")
        
        if obligation["status"] != "completed":
            raise ValidationError("La obligación debe estar completada para renovar")
        
        if not obligation["recurrence_pattern"]:
            raise ValidationError("La obligación recurrente debe tener un patrón de recurrencia")
        
        try:
            # Calcular próxima fecha de vencimiento
            current_due_date = None
            if obligation["due_date"]:
                current_due_date = datetime.fromisoformat(obligation["due_date"]).date()
            
            next_due_date = self._calculate_next_date(
                current_due_date or date.today(),
                obligation["recurrence_pattern"],
                datetime.fromisoformat(obligation["completed_at"]) if obligation["completed_at"] else None
            )
            
            # Crear nueva instancia de la obligación
            new_obligation_data = {
                "household_id": obligation["household_id"],
                "name": obligation["name"],
                "total_amount": obligation["total_amount"],
                "outstanding_amount": obligation["total_amount"],  # Resetear monto pendiente
                "due_date": next_due_date.isoformat(),
                "description": obligation["description"],
                "priority": obligation["priority"],
                "creditor": obligation["creditor"],
                "is_recurring": True,
                "recurrence_pattern": obligation["recurrence_pattern"],
                "status": "active",
                "created_at": "now()",
                "updated_at": "now()"
            }
            
            result = self.client.table("obligations").insert(new_obligation_data).execute()
            
            if not result.data:
                raise Exception("Error creando nueva instancia de obligación")
            
            new_obligation = result.data[0]
            
            logger.info(
                "Obligación recurrente creada",
                original_obligation_id=str(obligation_id),
                new_obligation_id=new_obligation["id"],
                next_due_date=next_due_date.isoformat(),
                pattern=obligation["recurrence_pattern"]
            )
            
            return {
                "new_obligation": new_obligation,
                "next_due_date": next_due_date.isoformat(),
                "pattern": obligation["recurrence_pattern"]
            }
            
        except Exception as e:
            logger.error(
                "Error renovando obligación",
                obligation_id=str(obligation_id),
                error=str(e)
            )
            raise
    
    async def get_due_recurring_items(
        self,
        household_id: UUID,
        user: Optional[User] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Obtiene elementos recurrentes que están próximos a vencer."""
        try:
            # Metas recurrentes próximas a vencer (próximos 30 días)
            goals_result = self.client.table("goals").select("*").eq(
                "household_id", str(household_id)
            ).eq("is_recurring", True).eq("status", "completed").execute()
            
            # Obligaciones recurrentes próximas a vencer (próximos 30 días)
            obligations_result = self.client.table("obligations").select("*").eq(
                "household_id", str(household_id)
            ).eq("is_recurring", True).eq("status", "completed").execute()
            
            return {
                "goals": goals_result.data or [],
                "obligations": obligations_result.data or []
            }
            
        except Exception as e:
            logger.error(
                "Error obteniendo elementos recurrentes próximos a vencer",
                household_id=str(household_id),
                error=str(e)
            )
            raise


# Instancia global del servicio
recurrence_service = RecurrenceService()
