"""Inicialización perezosa del cliente de Supabase (soporta nuevas API keys)."""

from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)


class Supa:
    """Singleton de cliente Supabase con validaciones básicas de llaves."""

    _client: Optional[Client] = None
    _service_client: Optional[Client] = None

    @staticmethod
    def _clean(value: str) -> str:
        return value.strip().rstrip("\r").rstrip("\n").rstrip("/")

    @classmethod
    def get_user_client(cls) -> Client:
        if cls._client is None:
            url = cls._clean(settings.supabase_url)
            key = cls._clean(settings.supabase_anon_key)
            cls._client = create_client(
                url,
                key,
                options=ClientOptions(auto_refresh_token=True, persist_session=True),
            )
        return cls._client

    @classmethod
    def get_service_client(cls) -> Client:
        if cls._service_client is None:
            url = cls._clean(settings.supabase_url)
            key = cls._clean(settings.supabase_service_role_key)
            # Validación defensiva mínima para nuevas llaves
            if not (key.startswith("sb_secret_") or key.startswith("eyJ")):
                # Permitimos JWT legacy (empieza con eyJ) para entornos antiguos
                raise ValueError("Se esperaba una secret key válida para Supabase")
            cls._service_client = create_client(
                url,
                key,
                options=ClientOptions(auto_refresh_token=False, persist_session=False),
            )
        return cls._service_client

    @classmethod
    def with_user_token(cls, user_token: str) -> Client:
        url = cls._clean(settings.supabase_url)
        key = cls._clean(settings.supabase_anon_key)
        client = create_client(
            url,
            key,
            options=ClientOptions(auto_refresh_token=False, persist_session=False),
        )
        client.auth.set_session({"access_token": user_token, "refresh_token": ""})
        return client


async def execute_query(
    query: str,
    params: Optional[Dict[str, Any]] = None,
    user_token: Optional[str] = None,
) -> List[Dict[str, Any]]:
    client = Supa.get_service_client() if not user_token else Supa.with_user_token(user_token)
    try:
        result = client.rpc("execute_sql", {"query": query, "params": params or {}}).execute()
        return result.data if result.data else []
    except Exception as e:
        logger.error("Error ejecutando query", query=query, error=str(e))
        raise


# Shim de compatibilidad para imports existentes: `from ..db.supabase_client import supabase_client`
class _CompatSupabaseClient:
    @property
    def service_client(self) -> Client:
        return Supa.get_service_client()

    @property
    def client(self) -> Client:
        return Supa.get_user_client()

    def with_user_token(self, user_token: str) -> Client:
        return Supa.with_user_token(user_token)


supabase_client = _CompatSupabaseClient()
