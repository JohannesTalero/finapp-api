"""Servicio de idempotencia para operaciones financieras."""

import hashlib
import json
from typing import Optional, Dict, Any, Tuple
from uuid import UUID

from ..core.logging import get_logger
from ..core.errors import IdempotencyError, ConflictError
from ..db.supabase_client import supabase_client

logger = get_logger(__name__)


class IdempotencyService:
    """Servicio para manejar idempotencia de requests."""
    
    def __init__(self):
        self.client = supabase_client.service_client
    
    def _hash_request_body(self, body: Dict[str, Any]) -> str:
        """Genera hash del cuerpo del request."""
        # Ordenar las claves para consistencia
        sorted_body = json.dumps(body, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(sorted_body.encode()).hexdigest()
    
    async def check_idempotency(
        self,
        key: str,
        user_id: UUID,
        household_id: UUID,
        request_body: Dict[str, Any]
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Verifica si el request ya fue procesado.
        
        Returns:
            Tuple[is_duplicate, cached_response]
        """
        request_hash = self._hash_request_body(request_body)
        
        try:
            # Buscar request previo
            result = self.client.table("idempotency_requests").select("*").eq(
                "key", key
            ).eq("user_id", str(user_id)).eq("household_id", str(household_id)).execute()
            
            if not result.data:
                return False, None
            
            existing_request = result.data[0]
            existing_hash = existing_request["request_hash"]
            
            # Verificar si el hash coincide
            if existing_hash != request_hash:
                logger.warning(
                    "Idempotency key conflict",
                    key=key,
                    user_id=str(user_id),
                    household_id=str(household_id),
                    existing_hash=existing_hash,
                    new_hash=request_hash
                )
                raise IdempotencyError(key)
            
            # Retornar respuesta cacheada
            logger.info(
                "Idempotency hit",
                key=key,
                user_id=str(user_id),
                household_id=str(household_id)
            )
            
            return True, existing_request["response_body"]
            
        except Exception as e:
            if isinstance(e, IdempotencyError):
                raise
            logger.error(
                "Error checking idempotency",
                key=key,
                user_id=str(user_id),
                household_id=str(household_id),
                error=str(e)
            )
            raise
    
    async def store_idempotency_result(
        self,
        key: str,
        user_id: UUID,
        household_id: UUID,
        request_body: Dict[str, Any],
        response_status: int,
        response_body: Dict[str, Any]
    ) -> None:
        """Almacena el resultado de un request idempotente."""
        request_hash = self._hash_request_body(request_body)
        
        data = {
            "key": key,
            "user_id": str(user_id),
            "household_id": str(household_id),
            "request_hash": request_hash,
            "response_status": response_status,
            "response_body": response_body
        }
        
        try:
            self.client.table("idempotency_requests").insert(data).execute()
            
            logger.info(
                "Idempotency result stored",
                key=key,
                user_id=str(user_id),
                household_id=str(household_id),
                response_status=response_status
            )
            
        except Exception as e:
            logger.error(
                "Error storing idempotency result",
                key=key,
                user_id=str(user_id),
                household_id=str(household_id),
                error=str(e)
            )
            raise
    
    async def cleanup_old_requests(self, days: int = 30) -> int:
        """Limpia requests idempotentes antiguos."""
        try:
            result = self.client.table("idempotency_requests").delete().lt(
                "created_at", f"now() - interval '{days} days'"
            ).execute()
            
            deleted_count = len(result.data) if result.data else 0
            
            logger.info(
                "Cleaned up old idempotency requests",
                deleted_count=deleted_count,
                days=days
            )
            
            return deleted_count
            
        except Exception as e:
            logger.error("Error cleaning up old idempotency requests", error=str(e))
            raise


# Instancia global del servicio
idempotency_service = IdempotencyService()
