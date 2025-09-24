"""Repositorio para gestión de hogares."""

from typing import List, Optional, Dict, Any
from uuid import UUID

from .base_repository import BaseRepository
from ...core.security import User


class HouseholdsRepository(BaseRepository):
    """Repositorio para hogares."""
    
    def __init__(self):
        super().__init__("households")
    
    async def create_household(
        self,
        name: str,
        description: Optional[str],
        owner_id: UUID,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """Crea un nuevo hogar."""
        data = {
            "name": name,
            "description": description,
            "owner_id": str(owner_id),
            "created_at": "now()",
            "updated_at": "now()"
        }
        return await self.create(data, user)
    
    async def get_household_by_id(
        self,
        household_id: UUID,
        user: Optional[User] = None
    ) -> Optional[Dict[str, Any]]:
        """Obtiene un hogar por ID."""
        return await self.get_by_id(household_id, user)
    
    async def get_user_households(
        self,
        user_id: UUID,
        user: Optional[User] = None
    ) -> List[Dict[str, Any]]:
        """Obtiene todos los hogares del usuario."""
        return await self.list(
            filters={"owner_id": str(user_id)},
            order_by="created_at.desc",
            user=user
        )
    
    async def update_household(
        self,
        household_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        user: Optional[User] = None
    ) -> Optional[Dict[str, Any]]:
        """Actualiza un hogar."""
        data = {"updated_at": "now()"}
        
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        
        return await self.update(household_id, data, user)
    
    async def delete_household(
        self,
        household_id: UUID,
        user: Optional[User] = None
    ) -> bool:
        """Elimina un hogar."""
        return await self.delete(household_id, user)
    
    async def get_household_members(
        self,
        household_id: UUID,
        user: Optional[User] = None
    ) -> List[Dict[str, Any]]:
        """Obtiene los miembros de un hogar."""
        client = self._get_client(user)
        
        try:
            result = client.table("household_members").select(
                "*, users(email, full_name)"
            ).eq("household_id", str(household_id)).execute()
            
            return result.data or []
        except Exception as e:
            self.logger.error("Error obteniendo miembros del hogar", error=str(e), household_id=str(household_id))
            raise
    
    async def add_household_member(
        self,
        household_id: UUID,
        user_id: UUID,
        role: str,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """Agrega un miembro al hogar."""
        data = {
            "household_id": str(household_id),
            "user_id": str(user_id),
            "role": role,
            "joined_at": "now()"
        }
        
        client = self._get_client(user)
        
        try:
            result = client.table("household_members").insert(data).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            self.logger.error("Error agregando miembro al hogar", error=str(e), data=data)
            raise
    
    async def update_household_member_role(
        self,
        household_id: UUID,
        user_id: UUID,
        role: str,
        user: Optional[User] = None
    ) -> Optional[Dict[str, Any]]:
        """Actualiza el rol de un miembro del hogar."""
        client = self._get_client(user)
        
        try:
            result = client.table("household_members").update(
                {"role": role}
            ).eq("household_id", str(household_id)).eq("user_id", str(user_id)).execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            self.logger.error("Error actualizando rol del miembro", error=str(e), household_id=str(household_id), user_id=str(user_id))
            raise
    
    async def remove_household_member(
        self,
        household_id: UUID,
        user_id: UUID,
        user: Optional[User] = None
    ) -> bool:
        """Remueve un miembro del hogar."""
        client = self._get_client(user)
        
        try:
            result = client.table("household_members").delete().eq(
                "household_id", str(household_id)
            ).eq("user_id", str(user_id)).execute()
            
            return len(result.data) > 0
        except Exception as e:
            self.logger.error("Error removiendo miembro del hogar", error=str(e), household_id=str(household_id), user_id=str(user_id))
            raise
