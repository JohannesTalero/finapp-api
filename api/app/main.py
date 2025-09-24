"""Aplicación principal de FastAPI."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .core.config import settings
from .core.logging import configure_logging, get_logger, add_request_context
from .core.errors import (
    http_exception_handler,
    validation_exception_handler,
    api_exception_handler,
    general_exception_handler
)
from .routers import (
    auth_router,
    households_router,
    catalog_router,
    transactions_router,
    goals_router,
    obligations_router,
    reports_router
)

# Configurar logging
configure_logging()
logger = get_logger(__name__)

# Configurar rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación."""
    # Startup
    logger.info("Iniciando aplicación FastAPI", version="1.0.0", env=settings.project_env)
    
    # Aquí podrías inicializar conexiones a DB, caché, etc.
    
    yield
    
    # Shutdown
    logger.info("Cerrando aplicación FastAPI")


# Crear aplicación FastAPI
app = FastAPI(
    title="FinApp API",
    description="API de gestión financiera personal con FastAPI y Supabase",
    version="1.0.0",
    docs_url="/v1/docs",
    redoc_url="/v1/redoc",
    openapi_url="/v1/openapi.json",
    lifespan=lifespan
)

# Configurar rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middleware de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Idempotency-Key",
        "X-Request-ID",
        "Accept"
    ],
)

# Middleware de hosts confiables
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.project_env == "local" else settings.cors_origins
)


@app.middleware("http")
async def add_request_context_middleware(request: Request, call_next):
    """Middleware para agregar contexto de request."""
    # Agregar contexto de logging
    add_request_context(request)
    
    # Procesar request
    response = await call_next(request)
    
    return response


@app.middleware("http")
async def add_security_headers_middleware(request: Request, call_next):
    """Middleware para agregar headers de seguridad."""
    response = await call_next(request)
    
    # Headers de seguridad
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response


# Manejadores de excepciones
app.add_exception_handler(Exception, general_exception_handler)
app.add_exception_handler(ValueError, validation_exception_handler)
app.add_exception_handler(422, validation_exception_handler)


# Health check
@app.get("/v1/healthz")
async def health_check():
    """Health check para liveness y readiness."""
    try:
        # Aquí podrías verificar conexiones a DB, caché, etc.
        # Por ahora retornamos OK
        
        return {
            "status": "healthy",
            "version": "1.0.0",
            "environment": settings.project_env
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


# Endpoint de información de la API
@app.get("/v1")
async def api_info():
    """Información de la API."""
    return {
        "name": "FinApp API",
        "version": "1.0.0",
        "description": "API de gestión financiera personal",
        "docs_url": "/v1/docs",
        "redoc_url": "/v1/redoc",
        "openapi_url": "/v1/openapi.json"
    }


# Incluir routers
app.include_router(auth_router.router)
app.include_router(households_router.router)
app.include_router(catalog_router.router)
app.include_router(transactions_router.router)
app.include_router(goals_router.router)
app.include_router(obligations_router.router)
app.include_router(reports_router.router)


# Endpoint raíz
@app.get("/")
async def root():
    """Endpoint raíz."""
    return {
        "message": "FinApp API",
        "version": "1.0.0",
        "docs": "/v1/docs"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.project_env == "local" else False,
        log_level=settings.log_level.lower()
    )
