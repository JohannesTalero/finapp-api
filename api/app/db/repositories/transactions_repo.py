"""Repositorio para gestión de transacciones."""

from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal

from .base_repository import BaseRepository
from ...core.security import User


class TransactionsRepository(BaseRepository):
    """Repositorio para transacciones."""
    
    def __init__(self):
        super().__init__("transactions")
    
    async def create_transaction(
        self,
        household_id: UUID,
        kind: str,
        amount: Decimal,
        account_id: Optional[UUID] = None,
        from_account_id: Optional[UUID] = None,
        to_account_id: Optional[UUID] = None,
        category_id: Optional[UUID] = None,
        occurred_at: Optional[datetime] = None,
        description: Optional[str] = None,
        counterparty: Optional[str] = None,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """Crea una nueva transacción."""
        data = {
            "household_id": str(household_id),
            "kind": kind,
            "amount": str(amount),
            "account_id": str(account_id) if account_id else None,
            "from_account_id": str(from_account_id) if from_account_id else None,
            "to_account_id": str(to_account_id) if to_account_id else None,
            "category_id": str(category_id) if category_id else None,
            "occurred_at": occurred_at.isoformat() if occurred_at else datetime.utcnow().isoformat(),
            "description": description,
            "counterparty": counterparty,
            "created_at": "now()",
            "updated_at": "now()"
        }
        return await self.create(data, user)
    
    async def get_transactions_by_household(
        self,
        household_id: UUID,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        kind: Optional[str] = None,
        category_id: Optional[UUID] = None,
        account_id: Optional[UUID] = None,
        search: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: int = 20,
        sort: str = "occurred_at",
        order: str = "desc",
        user: Optional[User] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Obtiene transacciones de un hogar con paginación cursor-based."""
        client = self._get_client(user)
        
        try:
            query = client.table(self.table_name).select("*")
            
            # Filtros obligatorios
            query = query.eq("household_id", str(household_id))
            
            # Filtros opcionales
            if from_date:
                query = query.gte("occurred_at", from_date.isoformat())
            if to_date:
                query = query.lte("occurred_at", to_date.isoformat())
            if kind:
                query = query.eq("kind", kind)
            if category_id:
                query = query.eq("category_id", str(category_id))
            if account_id:
                query = query.or_(f"account_id.eq.{account_id},from_account_id.eq.{account_id},to_account_id.eq.{account_id}")
            if search:
                query = query.or_(f"description.ilike.%{search}%,counterparty.ilike.%{search}%")
            
            # Ordenamiento
            sort_field = f"{sort}.{order}"
            query = query.order(sort_field)
            
            # Paginación cursor-based
            if cursor:
                # Decodificar cursor (en formato base64: occurred_at|id)
                import base64
                try:
                    decoded = base64.b64decode(cursor).decode()
                    occurred_at_str, id_str = decoded.split("|")
                    occurred_at_cursor = datetime.fromisoformat(occurred_at_str)
                    
                    if order == "desc":
                        query = query.lt("occurred_at", occurred_at_cursor.isoformat()).or_(
                            f"occurred_at.eq.{occurred_at_cursor.isoformat()},id.lt.{id_str}"
                        )
                    else:
                        query = query.gt("occurred_at", occurred_at_cursor.isoformat()).or_(
                            f"occurred_at.eq.{occurred_at_cursor.isoformat()},id.gt.{id_str}"
                        )
                except Exception:
                    # Si el cursor es inválido, ignorarlo
                    pass
            
            # Límite
            query = query.limit(limit + 1)  # +1 para determinar si hay más páginas
            
            result = query.execute()
            transactions = result.data or []
            
            # Determinar next_cursor
            next_cursor = None
            if len(transactions) > limit:
                transactions = transactions[:limit]
                last_transaction = transactions[-1]
                occurred_at = last_transaction["occurred_at"]
                transaction_id = last_transaction["id"]
                
                # Crear cursor (base64: occurred_at|id)
                import base64
                cursor_data = f"{occurred_at}|{transaction_id}"
                next_cursor = base64.b64encode(cursor_data.encode()).decode()
            
            return transactions, next_cursor
            
        except Exception as e:
            self.logger.error("Error obteniendo transacciones", error=str(e), household_id=str(household_id))
            raise
    
    async def get_transaction_by_id(
        self,
        transaction_id: UUID,
        user: Optional[User] = None
    ) -> Optional[Dict[str, Any]]:
        """Obtiene una transacción por ID."""
        return await self.get_by_id(transaction_id, user)
    
    async def update_transaction(
        self,
        transaction_id: UUID,
        amount: Optional[Decimal] = None,
        category_id: Optional[UUID] = None,
        occurred_at: Optional[datetime] = None,
        description: Optional[str] = None,
        counterparty: Optional[str] = None,
        user: Optional[User] = None
    ) -> Optional[Dict[str, Any]]:
        """Actualiza una transacción."""
        data = {"updated_at": "now()"}
        
        if amount is not None:
            data["amount"] = str(amount)
        if category_id is not None:
            data["category_id"] = str(category_id)
        if occurred_at is not None:
            data["occurred_at"] = occurred_at.isoformat()
        if description is not None:
            data["description"] = description
        if counterparty is not None:
            data["counterparty"] = counterparty
        
        return await self.update(transaction_id, data, user)
    
    async def delete_transaction(
        self,
        transaction_id: UUID,
        user: Optional[User] = None
    ) -> bool:
        """Elimina una transacción."""
        return await self.delete(transaction_id, user)
    
    async def get_transaction_summary(
        self,
        household_id: UUID,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """Obtiene resumen de transacciones."""
        client = self._get_client(user)
        
        try:
            query = client.table(self.table_name).select("kind,amount")
            query = query.eq("household_id", str(household_id))
            
            if from_date:
                query = query.gte("occurred_at", from_date.isoformat())
            if to_date:
                query = query.lte("occurred_at", to_date.isoformat())
            
            result = query.execute()
            transactions = result.data or []
            
            # Calcular totales por tipo
            summary = {
                "total_income": Decimal("0"),
                "total_expense": Decimal("0"),
                "total_transfer": Decimal("0"),
                "transaction_count": len(transactions)
            }
            
            for tx in transactions:
                amount = Decimal(tx["amount"])
                kind = tx["kind"]
                
                if kind == "income":
                    summary["total_income"] += amount
                elif kind == "expense":
                    summary["total_expense"] += amount
                elif kind == "transfer":
                    summary["total_transfer"] += amount
            
            # Convertir a string para JSON
            summary["total_income"] = str(summary["total_income"])
            summary["total_expense"] = str(summary["total_expense"])
            summary["total_transfer"] = str(summary["total_transfer"])
            
            return summary
            
        except Exception as e:
            self.logger.error("Error obteniendo resumen de transacciones", error=str(e), household_id=str(household_id))
            raise
