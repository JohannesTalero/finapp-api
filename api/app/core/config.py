"""Configuración de la aplicación usando Pydantic Settings."""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración de la aplicación."""
    
    # Supabase
    supabase_url: str = Field(..., description="URL de Supabase")
    supabase_anon_key: str = Field(..., description="Clave anónima de Supabase")
    supabase_service_role_key: str = Field(..., description="Clave de servicio de Supabase")
    
    # Entorno
    project_env: str = Field(default="local", description="Entorno del proyecto")
    log_level: str = Field(default="INFO", description="Nivel de logging")
    
    # CORS
    cors_origins: List[str] = Field(default=["http://localhost:3000"], description="Orígenes permitidos para CORS")
    
    # Rate limiting
    rate_limit_requests: int = Field(default=5, description="Límite de requests por segundo")
    rate_limit_burst: int = Field(default=10, description="Burst de rate limiting")
    
    # Paginación
    default_page_size: int = Field(default=20, description="Tamaño de página por defecto")
    max_page_size: int = Field(default=100, description="Tamaño máximo de página")
    
    # Seguridad
    jwt_algorithm: str = Field(default="HS256", description="Algoritmo JWT")
    access_token_expire_minutes: int = Field(default=30, description="Expiración del access token en minutos")
    refresh_token_expire_days: int = Field(default=7, description="Expiración del refresh token en días")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Instancia global de configuración
settings = Settings()
