"""Servicio para aportes a metas."""

from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from ..core.logging import get_logger
from ..core.errors import NotFoundError, ValidationError
from ..core.security import User
from ..db.repositories.goals_repo import GoalsRepository
from ..db.repositories.transactions_repo import TransactionsRepository
from ..db.supabase_client import supabase_client

logger = get_logger(__name__)


class ContributionsService:
    """Servicio para manejar aportes a metas."""
    
    def __init__(self):
        self.goals_repo = GoalsRepository()
        self.transactions_repo = TransactionsRepository()
        self.client = supabase_client.service_client
    
    async def create_contribution(
        self,
        household_id: UUID,
        goal_id: UUID,
        amount: Decimal,
        source_account_id: UUID,
        occurred_at: Optional[datetime] = None,
        description: Optional[str] = None,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        Crea un aporte a una meta con efecto atómico.
        
        Efecto atómico:
        1. Crea transacción (ingreso)
        2. Vincula en goal_contributions
        3. Incrementa current_amount
        4. Autocierra si corresponde
        """
        # Verificar que la meta existe y está activa
        goal = await self.goals_repo.get_goal_by_id(goal_id, user)
        if not goal:
            raise NotFoundError("Meta", str(goal_id))
        
        if goal["status"] != "active":
            raise ValidationError("La meta debe estar activa para recibir aportes")
        
        # Verificar que la cuenta existe
        account = await self.client.table("accounts").select("*").eq(
            "id", str(source_account_id)
        ).eq("household_id", str(household_id)).execute()
        
        if not account.data:
            raise NotFoundError("Cuenta", str(source_account_id))
        
        # Verificar que el monto es positivo
        if amount <= 0:
            raise ValidationError("El monto del aporte debe ser positivo")
        
        # Usar transacción de base de datos para atomicidad
        try:
            # 1. Crear transacción de ingreso
            transaction_data = {
                "household_id": str(household_id),
                "kind": "income",
                "amount": str(amount),
                "account_id": str(source_account_id),
                "occurred_at": (occurred_at or datetime.utcnow()).isoformat(),
                "description": description or f"Aporte a meta: {goal['name']}",
                "created_at": "now()",
                "updated_at": "now()"
            }
            
            transaction_result = self.client.table("transactions").insert(
                transaction_data
            ).execute()
            
            if not transaction_result.data:
                raise Exception("Error creando transacción")
            
            transaction = transaction_result.data[0]
            transaction_id = UUID(transaction["id"])
            
            # 2. Crear vinculación en goal_contributions
            contribution_data = {
                "goal_id": str(goal_id),
                "transaction_id": str(transaction_id),
                "amount": str(amount),
                "created_at": "now()"
            }
            
            contribution_result = self.client.table("goal_contributions").insert(
                contribution_data
            ).execute()
            
            if not contribution_result.data:
                raise Exception("Error creando vinculación de aporte")
            
            # 3. Actualizar current_amount de la meta
            current_amount = Decimal(goal["current_amount"])
            new_amount = current_amount + amount
            
            goal_update_result = self.client.table("goals").update({
                "current_amount": str(new_amount),
                "updated_at": "now()"
            }).eq("id", str(goal_id)).execute()
            
            if not goal_update_result.data:
                raise Exception("Error actualizando meta")
            
            updated_goal = goal_update_result.data[0]
            
            # 4. Verificar si debe autocerrarse
            target_amount = Decimal(goal["target_amount"])
            if new_amount >= target_amount:
                self.client.table("goals").update({
                    "status": "completed",
                    "completed_at": "now()",
                    "updated_at": "now()"
                }).eq("id", str(goal_id)).execute()
                
                logger.info(
                    "Meta autocerrada por completar objetivo",
                    goal_id=str(goal_id),
                    target_amount=str(target_amount),
                    current_amount=str(new_amount)
                )
            
            logger.info(
                "Aporte creado exitosamente",
                goal_id=str(goal_id),
                transaction_id=str(transaction_id),
                amount=str(amount),
                user_id=str(user.id) if user else None
            )
            
            return {
                "contribution": contribution_result.data[0],
                "transaction": transaction,
                "goal": updated_goal,
                "auto_closed": new_amount >= target_amount
            }
            
        except Exception as e:
            logger.error(
                "Error creando aporte",
                goal_id=str(goal_id),
                amount=str(amount),
                error=str(e)
            )
            raise
    
    async def get_goal_contributions(
        self,
        goal_id: UUID,
        user: Optional[User] = None
    ) -> list:
        """Obtiene todos los aportes de una meta."""
        return await self.goals_repo.get_goal_contributions(goal_id, user)
    
    async def get_contribution_summary(
        self,
        goal_id: UUID,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """Obtiene resumen de aportes de una meta."""
        contributions = await self.get_goal_contributions(goal_id, user)
        
        total_contributions = sum(
            Decimal(c["amount"]) for c in contributions
        )
        
        return {
            "total_contributions": str(total_contributions),
            "contribution_count": len(contributions),
            "contributions": contributions
        }


# Instancia global del servicio
contributions_service = ContributionsService()
