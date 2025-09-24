"""Manejo de errores con formato Problem+JSON."""

from typing import Any, Dict, Optional, Union
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import uuid

from .logging import get_logger, request_id_var

logger = get_logger(__name__)


class ProblemDetail:
    """Clase para errores en formato Problem+JSON."""
    
    def __init__(
        self,
        type: str,
        title: str,
        detail: str,
        status: int,
        instance: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None
    ):
        self.type = type
        self.title = title
        self.detail = detail
        self.status = status
        self.instance = instance or f"/v1/problems/{uuid.uuid4()}"
        self.fields = fields or {}


class APIException(HTTPException):
    """Excepción personalizada para la API."""
    
    def __init__(
        self,
        status_code: int,
        type: str,
        title: str,
        detail: str,
        instance: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None
    ):
        self.problem = ProblemDetail(
            type=type,
            title=title,
            detail=detail,
            status=status_code,
            instance=instance,
            fields=fields
        )
        super().__init__(status_code=status_code, detail=detail)


# Errores comunes
class ValidationError(APIException):
    """Error de validación."""
    
    def __init__(self, detail: str, fields: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=422,
            type="https://example.com/problems/validation-error",
            title="Error de validación",
            detail=detail,
            fields=fields
        )


class AuthenticationError(APIException):
    """Error de autenticación."""
    
    def __init__(self, detail: str = "No autenticado"):
        super().__init__(
            status_code=401,
            type="https://example.com/problems/authentication-error",
            title="Error de autenticación",
            detail=detail
        )


class AuthorizationError(APIException):
    """Error de autorización."""
    
    def __init__(self, detail: str = "No autorizado"):
        super().__init__(
            status_code=403,
            type="https://example.com/problems/authorization-error",
            title="Error de autorización",
            detail=detail
        )


class NotFoundError(APIException):
    """Error de recurso no encontrado."""
    
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            status_code=404,
            type="https://example.com/problems/not-found",
            title="Recurso no encontrado",
            detail=f"{resource} con identificador '{identifier}' no encontrado"
        )


class ConflictError(APIException):
    """Error de conflicto."""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=409,
            type="https://example.com/problems/conflict",
            title="Conflicto",
            detail=detail
        )


class IdempotencyError(ConflictError):
    """Error de idempotencia."""
    
    def __init__(self, key: str):
        super().__init__(
            detail=f"Request con Idempotency-Key '{key}' ya procesado con parámetros diferentes"
        )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Manejador para HTTPException."""
    request_id = request_id_var.get() or str(uuid.uuid4())
    
    logger.error(
        "HTTP Exception",
        request_id=request_id,
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": "https://example.com/problems/http-error",
            "title": "Error HTTP",
            "detail": exc.detail,
            "status": exc.status_code,
            "instance": f"/v1/problems/{request_id}"
        }
    )


async def validation_exception_handler(
    request: Request, 
    exc: RequestValidationError
) -> JSONResponse:
    """Manejador para errores de validación de Pydantic."""
    request_id = request_id_var.get() or str(uuid.uuid4())
    
    # Extraer errores de validación
    fields = {}
    for error in exc.errors():
        field_path = ".".join(str(loc) for loc in error["loc"])
        fields[field_path] = {
            "message": error["msg"],
            "type": error["type"]
        }
    
    logger.error(
        "Validation Error",
        request_id=request_id,
        errors=exc.errors(),
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "type": "https://example.com/problems/validation-error",
            "title": "Error de validación",
            "detail": "Los datos proporcionados no son válidos",
            "status": 422,
            "instance": f"/v1/problems/{request_id}",
            "fields": fields
        }
    )


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """Manejador para APIException."""
    request_id = request_id_var.get() or str(uuid.uuid4())
    
    logger.error(
        "API Exception",
        request_id=request_id,
        type=exc.problem.type,
        title=exc.problem.title,
        detail=exc.problem.detail,
        status=exc.problem.status,
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=exc.problem.status,
        content={
            "type": exc.problem.type,
            "title": exc.problem.title,
            "detail": exc.problem.detail,
            "status": exc.problem.status,
            "instance": exc.problem.instance,
            "fields": exc.problem.fields
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Manejador para excepciones generales."""
    request_id = request_id_var.get() or str(uuid.uuid4())
    
    logger.error(
        "Unhandled Exception",
        request_id=request_id,
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "type": "https://example.com/problems/internal-error",
            "title": "Error interno del servidor",
            "detail": "Ha ocurrido un error interno. Por favor, inténtalo de nuevo.",
            "status": 500,
            "instance": f"/v1/problems/{request_id}"
        }
    )
