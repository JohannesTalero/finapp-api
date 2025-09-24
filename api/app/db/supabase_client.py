"""Cliente de Supabase con reenvío de tokens de usuario."""

from typing import Optional, Dict, Any, List
from uuid import UUID
import httpx
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

from ..core.config import settings
from ..core.logging import get_logger
from ..core.security import User

logger = get_logger(__name__)


class SupabaseClient:
    """Cliente de Supabase con soporte para tokens de usuario."""
    
    def __init__(self):
        self._client: Optional[Client] = None
        self._service_client: Optional[Client] = None
    
    @property
    def client(self) -> Client:
        """Cliente con token de usuario."""
        if self._client is None:
            self._client = create_client(
                settings.supabase_url,
                settings.supabase_anon_key,
                options=ClientOptions(
                    auto_refresh_token=True,
                    persist_session=True
                )
            )
        return self._client
    
    @property
    def service_client(self) -> Client:
        """Cliente con service role key."""
        if self._service_client is None:
            self._service_client = create_client(
                settings.supabase_url,
                settings.supabase_service_role_key,
                options=ClientOptions(
                    auto_refresh_token=False,
                    persist_session=False
                )
            )
        return self._service_client
    
    def with_user_token(self, user_token: str) -> Client:
        """Crea un cliente con el token del usuario para RLS."""
        client = create_client(
            settings.supabase_url,
            settings.supabase_anon_key,
            options=ClientOptions(
                auto_refresh_token=False,
                persist_session=False
            )
        )
        
        # Establecer el token del usuario
        client.auth.set_session({"access_token": user_token, "refresh_token": ""})
        
        return client
    
    async def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        user_token: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Ejecuta una query SQL con parámetros."""
        client = self.service_client if not user_token else self.with_user_token(user_token)
        
        try:
            result = client.rpc("execute_sql", {
                "query": query,
                "params": params or {}
            }).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error("Error ejecutando query", query=query, error=str(e))
            raise
    
    async def get_user_access_token(self, user: User) -> str:
        """Obtiene el access token del usuario."""
        # En un escenario real, esto vendría del request
        # Por ahora retornamos un token mock
        return "mock_access_token"


# Instancia global del cliente
supabase_client = SupabaseClient()
