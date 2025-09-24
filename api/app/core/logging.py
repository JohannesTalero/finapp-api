"""Configuración de logging estructurado con JSON."""

import logging
import sys
import uuid
from typing import Any, Dict, Optional
from contextvars import ContextVar

import structlog
from fastapi import Request

from .config import settings

# Context variables para tracking de requests
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
household_id_var: ContextVar[Optional[str]] = ContextVar("household_id", default=None)


def add_request_context(request: Request) -> None:
    """Agrega contexto del request a las variables de contexto."""
    request_id = str(uuid.uuid4())
    request_id_var.set(request_id)
    
    # Intentar extraer user_id del token si está disponible
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        # Aquí podrías decodificar el JWT para extraer el user_id
        # Por ahora lo dejamos como None
        user_id_var.set(None)


def get_context_vars() -> Dict[str, Any]:
    """Obtiene las variables de contexto para logging."""
    context = {}
    
    if request_id := request_id_var.get():
        context["request_id"] = request_id
    
    if user_id := user_id_var.get():
        context["user_id"] = user_id
        
    if household_id := household_id_var.get():
        context["household_id"] = household_id
    
    return context


def configure_logging() -> None:
    """Configura el logging estructurado."""
    
    # Configurar structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper())
        ),
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configurar logging estándar
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Obtiene un logger estructurado."""
    return structlog.get_logger(name)


# Logger por defecto
logger = get_logger(__name__)
