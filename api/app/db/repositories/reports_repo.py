"""Repositorio para reportes y análisis."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date
from decimal import Decimal

from .base_repository import BaseRepository
from ...core.security import User


class ReportsRepository(BaseRepository):
    """Repositorio para reportes."""
    
    def __init__(self):
        super().__init__("reports")
    
    async def get_account_balances(
        self,
        household_id: UUID,
        user: Optional[User] = None
    ) -> List[Dict[str, Any]]:
        """Obtiene balances de cuentas usando vista v_account_balances."""
        client = self._get_client(user)
        
        try:
            result = client.table("v_account_balances").select("*").eq(
                "household_id", str(household_id)
            ).execute()
            
            return result.data or []
        except Exception as e:
            self.logger.error("Error obteniendo balances de cuentas", error=str(e), household_id=str(household_id))
            raise
    
    async def get_cashflow(
        self,
        household_id: UUID,
        from_date: date,
        to_date: date,
        group_by: str = "month",
        user: Optional[User] = None
    ) -> List[Dict[str, Any]]:
        """Obtiene flujo de efectivo agrupado por período."""
        client = self._get_client(user)
        
        try:
            # Usar función RPC para calcular cashflow
            result = client.rpc("get_cashflow", {
                "p_household_id": str(household_id),
                "p_from_date": from_date.isoformat(),
                "p_to_date": to_date.isoformat(),
                "p_group_by": group_by
            }).execute()
            
            return result.data or []
        except Exception as e:
            self.logger.error("Error obteniendo cashflow", error=str(e), household_id=str(household_id))
            raise
    
    async def get_dashboard_data(
        self,
        household_id: UUID,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """Obtiene datos para el dashboard."""
        client = self._get_client(user)
        
        try:
            # Obtener balances de cuentas
            balances_result = client.table("v_account_balances").select("*").eq(
                "household_id", str(household_id)
            ).execute()
            
            # Obtener top categorías (últimos 30 días)
            from datetime import datetime, timedelta
            thirty_days_ago = (datetime.now() - timedelta(days=30)).date()
            
            categories_result = client.rpc("get_top_categories", {
                "p_household_id": str(household_id),
                "p_from_date": thirty_days_ago.isoformat(),
                "p_limit": 5
            }).execute()
            
            # Obtener próximos vencimientos
            upcoming_result = client.table("obligations").select("*").eq(
                "household_id", str(household_id)
            ).eq("status", "active").lte(
                "due_date", (datetime.now() + timedelta(days=30)).date().isoformat()
            ).order("due_date.asc").limit(5).execute()
            
            # Obtener progreso de metas
            goals_result = client.table("goals").select("*").eq(
                "household_id", str(household_id)
            ).eq("status", "active").order("priority.desc").limit(5).execute()
            
            return {
                "account_balances": balances_result.data or [],
                "top_categories": categories_result.data or [],
                "upcoming_obligations": upcoming_result.data or [],
                "active_goals": goals_result.data or []
            }
            
        except Exception as e:
            self.logger.error("Error obteniendo datos del dashboard", error=str(e), household_id=str(household_id))
            raise
    
    async def get_category_analysis(
        self,
        household_id: UUID,
        from_date: date,
        to_date: date,
        kind: Optional[str] = None,
        user: Optional[User] = None
    ) -> List[Dict[str, Any]]:
        """Obtiene análisis por categorías."""
        client = self._get_client(user)
        
        try:
            result = client.rpc("get_category_analysis", {
                "p_household_id": str(household_id),
                "p_from_date": from_date.isoformat(),
                "p_to_date": to_date.isoformat(),
                "p_kind": kind
            }).execute()
            
            return result.data or []
        except Exception as e:
            self.logger.error("Error obteniendo análisis de categorías", error=str(e), household_id=str(household_id))
            raise
    
    async def get_monthly_summary(
        self,
        household_id: UUID,
        year: int,
        month: int,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """Obtiene resumen mensual."""
        client = self._get_client(user)
        
        try:
            result = client.rpc("get_monthly_summary", {
                "p_household_id": str(household_id),
                "p_year": year,
                "p_month": month
            }).execute()
            
            return result.data[0] if result.data else {}
        except Exception as e:
            self.logger.error("Error obteniendo resumen mensual", error=str(e), household_id=str(household_id))
            raise
