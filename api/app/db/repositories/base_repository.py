"""Repositorio base con funcionalidades comunes."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
from datetime import datetime

from ..supabase_client import supabase_client
from ...core.logging import get_logger
from ...core.security import User

logger = get_logger(__name__)


class BaseRepository(ABC):
    """Repositorio base con funcionalidades comunes."""
    
    def __init__(self, table_name: str):
        self.table_name = table_name
    
    def _get_client(self, user: Optional[User] = None) -> Any:
        """Obtiene el cliente de Supabase apropiado."""
        if user:
            # En producción, obtendrías el token del request
            return supabase_client.with_user_token("mock_token")
        return supabase_client.service_client
    
    async def create(
        self,
        data: Dict[str, Any],
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """Crea un nuevo registro."""
        client = self._get_client(user)
        
        try:
            result = client.table(self.table_name).insert(data).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Error creando {self.table_name}", error=str(e), data=data)
            raise
    
    async def get_by_id(
        self,
        record_id: UUID,
        user: Optional[User] = None
    ) -> Optional[Dict[str, Any]]:
        """Obtiene un registro por ID."""
        client = self._get_client(user)
        
        try:
            result = client.table(self.table_name).select("*").eq("id", str(record_id)).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error obteniendo {self.table_name}", error=str(e), id=str(record_id))
            raise
    
    async def update(
        self,
        record_id: UUID,
        data: Dict[str, Any],
        user: Optional[User] = None
    ) -> Optional[Dict[str, Any]]:
        """Actualiza un registro."""
        client = self._get_client(user)
        
        try:
            result = client.table(self.table_name).update(data).eq("id", str(record_id)).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error actualizando {self.table_name}", error=str(e), id=str(record_id), data=data)
            raise
    
    async def delete(
        self,
        record_id: UUID,
        user: Optional[User] = None
    ) -> bool:
        """Elimina un registro."""
        client = self._get_client(user)
        
        try:
            result = client.table(self.table_name).delete().eq("id", str(record_id)).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error eliminando {self.table_name}", error=str(e), id=str(record_id))
            raise
    
    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        user: Optional[User] = None
    ) -> List[Dict[str, Any]]:
        """Lista registros con filtros opcionales."""
        client = self._get_client(user)
        
        try:
            query = client.table(self.table_name).select("*")
            
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            if order_by:
                query = query.order(order_by)
            
            if limit:
                query = query.limit(limit)
            
            if offset:
                query = query.range(offset, offset + (limit or 100) - 1)
            
            result = query.execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error listando {self.table_name}", error=str(e), filters=filters)
            raise
    
    async def count(
        self,
        filters: Optional[Dict[str, Any]] = None,
        user: Optional[User] = None
    ) -> int:
        """Cuenta registros con filtros opcionales."""
        client = self._get_client(user)
        
        try:
            query = client.table(self.table_name).select("id", count="exact")
            
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            result = query.execute()
            return result.count or 0
        except Exception as e:
            logger.error(f"Error contando {self.table_name}", error=str(e), filters=filters)
            raise
