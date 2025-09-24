# FinApp API

API de gestión financiera personal construida con FastAPI y Supabase. Proporciona una capa segura entre el frontend y Supabase para manejar transacciones, metas, obligaciones y reportes financieros.

## 🚀 Características

- **Arquitectura segura**: Frontend → FastAPI → Supabase (el frontend nunca toca Supabase directamente)
- **Autenticación robusta**: JWT con Supabase, cookies HttpOnly, CORS restringido
- **Autorización granular**: RBAC por hogar (viewer/member/admin/owner) + RLS en Postgres
- **Idempotencia**: Operaciones financieras con Idempotency-Key para evitar duplicados
- **Paginación eficiente**: Cursor-based para listas grandes
- **Reglas de negocio**: Aportes/pagos con efecto atómico y autocierre
- **Observabilidad**: Logging estructurado JSON, health checks, rate limiting
- **Testing completo**: Tests unitarios y e2e con cobertura

## 📋 Requisitos

- Python 3.11+
- Poetry
- Supabase (cuenta y proyecto)
- Git

## 🛠️ Instalación

### 1. Clonar el repositorio

```bash
git clone <repository-url>
cd finapp-api
```

### 2. Instalar dependencias

```bash
make install
```

### 3. Configurar variables de entorno

```bash
cp env.example .env
```

Editar `.env` con tus credenciales de Supabase:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
PROJECT_ENV=local
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:3000"]
```

### 4. Configurar base de datos

Ejecutar las migraciones SQL en Supabase:

1. Ir a Supabase Dashboard → SQL Editor
2. Ejecutar `migrations/000_schema.sql`
3. Ejecutar `migrations/001_idempotency.sql`
4. Ejecutar `migrations/002_helpers.sql`

### 5. Ejecutar la aplicación

```bash
make dev
```

La API estará disponible en:
- **API**: http://localhost:8000
- **Documentación**: http://localhost:8000/v1/docs
- **ReDoc**: http://localhost:8000/v1/redoc

## 📚 Uso

### Autenticación

```bash
# Login
curl -X POST "http://localhost:8000/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Usar token en requests
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/v1/households"
```

### Crear transacción con idempotencia

```bash
curl -X POST "http://localhost:8000/v1/households/{household_id}/transactions" \
  -H "Authorization: Bearer <token>" \
  -H "Idempotency-Key: <uuid>" \
  -H "Content-Type: application/json" \
  -d '{
    "kind": "income",
    "amount": "100.00",
    "account_id": "<account_id>",
    "category_id": "<category_id>",
    "description": "Salary"
  }'
```

### Crear aporte a meta

```bash
curl -X POST "http://localhost:8000/v1/households/{household_id}/goals/{goal_id}/contributions" \
  -H "Authorization: Bearer <token>" \
  -H "Idempotency-Key: <uuid>" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": "50.00",
    "source_account_id": "<account_id>",
    "description": "Monthly contribution"
  }'
```

## 🧪 Testing

### Ejecutar todos los tests

```bash
make test
```

### Tests específicos

```bash
# Solo tests unitarios
make test-unit

# Solo tests e2e
make test-e2e

# Tests con cobertura
make test-coverage
```

### Tests individuales

```bash
# Test específico
poetry run pytest tests/unit/test_security.py -v

# Test con marcadores
poetry run pytest -m unit -v
poetry run pytest -m e2e -v
```

## 🔧 Desarrollo

### Comandos útiles

```bash
# Desarrollo con hot reload
make dev

# Desarrollo con debug
make dev-debug

# Verificar código
make check

# Formatear código
make fmt

# Linting
make lint

# Verificar tipos
make types

# Limpiar archivos temporales
make clean
```

### Estructura del proyecto

```
api/
├── app/
│   ├── core/           # Configuración, seguridad, logging, errores
│   ├── db/             # Cliente Supabase y repositorios
│   ├── models/         # DTOs Pydantic
│   ├── routers/        # Endpoints FastAPI
│   ├── services/       # Lógica de negocio
│   ├── deps.py         # Dependencias comunes
│   └── main.py         # Aplicación principal
├── tests/
│   ├── unit/           # Tests unitarios
│   ├── e2e/            # Tests end-to-end
│   └── conftest.py     # Configuración de tests
└── migrations/         # Migraciones SQL
```

## 📖 API Reference

### Endpoints principales

#### Autenticación
- `POST /v1/auth/login` - Iniciar sesión
- `POST /v1/auth/refresh` - Renovar token
- `POST /v1/auth/logout` - Cerrar sesión

#### Hogares
- `GET /v1/households` - Listar hogares
- `POST /v1/households` - Crear hogar
- `GET /v1/households/{id}/members` - Listar miembros

#### Transacciones
- `GET /v1/households/{id}/transactions` - Listar transacciones
- `POST /v1/households/{id}/transactions` - Crear transacción
- `GET /v1/households/{id}/transactions/summary` - Resumen

#### Metas
- `GET /v1/households/{id}/goals` - Listar metas
- `POST /v1/households/{id}/goals` - Crear meta
- `POST /v1/households/{id}/goals/{id}/contributions` - Aportar

#### Obligaciones
- `GET /v1/households/{id}/obligations` - Listar obligaciones
- `POST /v1/households/{id}/obligations` - Crear obligación
- `POST /v1/households/{id}/obligations/{id}/payments` - Pagar

#### Reportes
- `GET /v1/households/{id}/balances` - Balances de cuentas
- `GET /v1/households/{id}/cashflow` - Flujo de efectivo
- `GET /v1/households/{id}/dashboard` - Dashboard

### Modelos de datos

#### Transacción
```json
{
  "kind": "income|expense|transfer",
  "amount": "100.00",
  "account_id": "uuid",
  "category_id": "uuid",
  "occurred_at": "2024-01-01T00:00:00Z",
  "description": "string",
  "counterparty": "string"
}
```

#### Meta
```json
{
  "name": "string",
  "target_amount": "1000.00",
  "current_amount": "100.00",
  "target_date": "2024-12-31",
  "priority": "low|medium|high",
  "is_recurring": false
}
```

## 🔒 Seguridad

### Autenticación
- JWT tokens de Supabase
- Cookies HttpOnly para tokens
- Refresh token rotation
- Rate limiting en escrituras

### Autorización
- RBAC por hogar (viewer/member/admin/owner)
- RLS en Postgres con `auth.uid()`
- Validación de membresía en cada request

### Idempotencia
- Header `Idempotency-Key` obligatorio en operaciones financieras
- Almacenamiento de hash de request body
- Rechazo de requests inconsistentes

### Headers de seguridad
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`

## 📊 Observabilidad

### Logging
- Formato JSON estructurado
- Correlation ID por request
- Contexto de usuario y hogar
- Niveles configurables

### Health Checks
- `GET /v1/healthz` - Liveness/readiness
- Verificación de conexiones a DB
- Métricas de salud del sistema

### Métricas
- Rate limiting por endpoint
- Latencia de requests
- Errores por tipo
- Uso de recursos

## 🚀 Despliegue

### Variables de entorno de producción

```env
PROJECT_ENV=production
LOG_LEVEL=INFO
CORS_ORIGINS=["https://your-frontend.com"]
RATE_LIMIT_REQUESTS=5
RATE_LIMIT_BURST=10
```

### Docker (opcional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-dev

COPY api/ ./api/
EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Comandos de producción

```bash
# Ejecutar en producción
make dev-prod

# Verificar salud
make health

# Monitorear recursos
make monitor
```

## 🤝 Contribuir

### Agregar nuevo router

1. Crear router en `api/app/routers/`
2. Definir modelos en `api/app/models/`
3. Implementar repositorio en `api/app/db/repositories/`
4. Agregar tests en `tests/`
5. Registrar router en `api/app/main.py`

### Agregar nuevo servicio

1. Crear servicio en `api/app/services/`
2. Implementar lógica de negocio
3. Agregar tests unitarios
4. Integrar con repositorios

### Ejemplo: Router de categorías

```python
# api/app/routers/categories_router.py
from fastapi import APIRouter, Depends
from ..models.catalog import CategoryCreate, CategoryResponse
from ..deps import verify_household_membership

router = APIRouter(prefix="/v1/households/{household_id}", tags=["categorías"])

@router.post("/categories", response_model=CategoryResponse)
async def create_category(
    household_id: UUID,
    request: CategoryCreate,
    user: User = Depends(verify_household_membership)
):
    # Implementar lógica
    pass
```

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 🆘 Soporte

### Problemas comunes

1. **Error de conexión a Supabase**
   - Verificar `SUPABASE_URL` y `SUPABASE_ANON_KEY`
   - Confirmar que el proyecto está activo

2. **Error de autenticación**
   - Verificar que el usuario existe en Supabase
   - Confirmar configuración de RLS

3. **Error de idempotencia**
   - Verificar que se incluye `Idempotency-Key` header
   - Confirmar que la tabla `idempotency_requests` existe

4. **Tests fallando**
   - Ejecutar `make clean` y `make install`
   - Verificar configuración de tests en `conftest.py`

### Logs y debugging

```bash
# Ver logs en tiempo real
make logs

# Ejecutar con debug
LOG_LEVEL=DEBUG make dev

# Verificar configuración
make validate
```

### Contacto

Para reportar bugs o solicitar features, crear un issue en el repositorio.

---

**FinApp API** - Gestión financiera personal segura y escalable 🚀