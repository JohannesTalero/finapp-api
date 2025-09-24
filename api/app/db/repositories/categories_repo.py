"""Repositorio para gestión de categorías."""

from typing import List, Optional, Dict, Any
from uuid import UUID

from .base_repository import BaseRepository
from ...core.security import User


class CategoriesRepository(BaseRepository):
    """Repositorio para categorías."""
    
    def __init__(self):
        super().__init__("categories")
    
    async def create_category(
        self,
        household_id: UUID,
        name: str,
        kind: str,
        description: Optional[str] = None,
        color: Optional[str] = None,
        icon: Optional[str] = None,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """Crea una nueva categoría."""
        data = {
            "household_id": str(household_id),
            "name": name,
            "kind": kind,
            "description": description,
            "color": color,
            "icon": icon,
            "created_at": "now()",
            "updated_at": "now()"
        }
        return await self.create(data, user)
    
    async def get_categories_by_household(
        self,
        household_id: UUID,
        kind: Optional[str] = None,
        user: Optional[User] = None
    ) -> List[Dict[str, Any]]:
        """Obtiene categorías de un hogar."""
        filters = {"household_id": str(household_id)}
        if kind:
            filters["kind"] = kind
        
        return await self.list(
            filters=filters,
            order_by="name.asc",
            user=user
        )
    
    async def get_category_by_id(
        self,
        category_id: UUID,
        user: Optional[User] = None
    ) -> Optional[Dict[str, Any]]:
        """Obtiene una categoría por ID."""
        return await self.get_by_id(category_id, user)
    
    async def update_category(
        self,
        category_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[str] = None,
        icon: Optional[str] = None,
        user: Optional[User] = None
    ) -> Optional[Dict[str, Any]]:
        """Actualiza una categoría."""
        data = {"updated_at": "now()"}
        
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if color is not None:
            data["color"] = color
        if icon is not None:
            data["icon"] = icon
        
        return await self.update(category_id, data, user)
    
    async def delete_category(
        self,
        category_id: UUID,
        user: Optional[User] = None
    ) -> bool:
        """Elimina una categoría."""
        return await self.delete(category_id, user)
    
    async def get_category_usage_count(
        self,
        category_id: UUID,
        user: Optional[User] = None
    ) -> int:
        """Cuenta cuántas transacciones usan esta categoría."""
        client = self._get_client(user)
        
        try:
            result = client.table("transactions").select("id", count="exact").eq(
                "category_id", str(category_id)
            ).execute()
            
            return result.count or 0
        except Exception as e:
            self.logger.error("Error contando uso de categoría", error=str(e), category_id=str(category_id))
            raise
