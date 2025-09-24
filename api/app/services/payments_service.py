"""Servicio para pagos de obligaciones."""

from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from ..core.logging import get_logger
from ..core.errors import NotFoundError, ValidationError
from ..core.security import User
from ..db.repositories.obligations_repo import ObligationsRepository
from ..db.repositories.transactions_repo import TransactionsRepository
from ..db.supabase_client import supabase_client

logger = get_logger(__name__)


class PaymentsService:
    """Servicio para manejar pagos de obligaciones."""
    
    def __init__(self):
        self.obligations_repo = ObligationsRepository()
        self.transactions_repo = TransactionsRepository()
        self.client = supabase_client.service_client
    
    async def create_payment(
        self,
        household_id: UUID,
        obligation_id: UUID,
        amount: Decimal,
        from_account_id: UUID,
        occurred_at: Optional[datetime] = None,
        description: Optional[str] = None,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        Crea un pago de obligación con efecto atómico.
        
        Efecto atómico:
        1. Crea transacción (gasto)
        2. Vincula en obligation_payments
        3. Reduce outstanding_amount
        4. Autocierra si outstanding_amount = 0
        """
        # Verificar que la obligación existe y está activa
        obligation = await self.obligations_repo.get_obligation_by_id(obligation_id, user)
        if not obligation:
            raise NotFoundError("Obligación", str(obligation_id))
        
        if obligation["status"] != "active":
            raise ValidationError("La obligación debe estar activa para recibir pagos")
        
        # Verificar que la cuenta existe
        account = await self.client.table("accounts").select("*").eq(
            "id", str(from_account_id)
        ).eq("household_id", str(household_id)).execute()
        
        if not account.data:
            raise NotFoundError("Cuenta", str(from_account_id))
        
        # Verificar que el monto es positivo
        if amount <= 0:
            raise ValidationError("El monto del pago debe ser positivo")
        
        # Verificar que no excede el monto pendiente
        outstanding_amount = Decimal(obligation["outstanding_amount"])
        if amount > outstanding_amount:
            raise ValidationError(
                f"El monto del pago ({amount}) no puede exceder el monto pendiente ({outstanding_amount})"
            )
        
        # Usar transacción de base de datos para atomicidad
        try:
            # 1. Crear transacción de gasto
            transaction_data = {
                "household_id": str(household_id),
                "kind": "expense",
                "amount": str(amount),
                "account_id": str(from_account_id),
                "occurred_at": (occurred_at or datetime.utcnow()).isoformat(),
                "description": description or f"Pago de obligación: {obligation['name']}",
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
            
            # 2. Crear vinculación en obligation_payments
            payment_data = {
                "obligation_id": str(obligation_id),
                "transaction_id": str(transaction_id),
                "amount": str(amount),
                "created_at": "now()"
            }
            
            payment_result = self.client.table("obligation_payments").insert(
                payment_data
            ).execute()
            
            if not payment_result.data:
                raise Exception("Error creando vinculación de pago")
            
            # 3. Actualizar outstanding_amount de la obligación
            new_outstanding = outstanding_amount - amount
            
            obligation_update_result = self.client.table("obligations").update({
                "outstanding_amount": str(new_outstanding),
                "updated_at": "now()"
            }).eq("id", str(obligation_id)).execute()
            
            if not obligation_update_result.data:
                raise Exception("Error actualizando obligación")
            
            updated_obligation = obligation_update_result.data[0]
            
            # 4. Verificar si debe autocerrarse
            if new_outstanding <= 0:
                self.client.table("obligations").update({
                    "status": "completed",
                    "completed_at": "now()",
                    "updated_at": "now()"
                }).eq("id", str(obligation_id)).execute()
                
                logger.info(
                    "Obligación autocerrada por completar pago",
                    obligation_id=str(obligation_id),
                    total_amount=str(obligation["total_amount"]),
                    outstanding_amount=str(new_outstanding)
                )
            
            logger.info(
                "Pago creado exitosamente",
                obligation_id=str(obligation_id),
                transaction_id=str(transaction_id),
                amount=str(amount),
                user_id=str(user.id) if user else None
            )
            
            return {
                "payment": payment_result.data[0],
                "transaction": transaction,
                "obligation": updated_obligation,
                "auto_closed": new_outstanding <= 0
            }
            
        except Exception as e:
            logger.error(
                "Error creando pago",
                obligation_id=str(obligation_id),
                amount=str(amount),
                error=str(e)
            )
            raise
    
    async def get_obligation_payments(
        self,
        obligation_id: UUID,
        user: Optional[User] = None
    ) -> list:
        """Obtiene todos los pagos de una obligación."""
        return await self.obligations_repo.get_obligation_payments(obligation_id, user)
    
    async def get_payment_summary(
        self,
        obligation_id: UUID,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """Obtiene resumen de pagos de una obligación."""
        payments = await self.get_obligation_payments(obligation_id, user)
        
        total_payments = sum(
            Decimal(p["amount"]) for p in payments
        )
        
        return {
            "total_payments": str(total_payments),
            "payment_count": len(payments),
            "payments": payments
        }


# Instancia global del servicio
payments_service = PaymentsService()
