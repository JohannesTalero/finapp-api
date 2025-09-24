# =====================================================
# MAKEFILE PARA FINAPP API
# =====================================================

.PHONY: help install dev test lint fmt types clean

# Variables
PYTHON := python
POETRY := poetry
APP_DIR := api
PORT := 8000
HOST := 0.0.0.0

# Colores para output
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Mostrar ayuda
	@echo "$(GREEN)FinApp API - Comandos disponibles:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'

install: ## Instalar dependencias con Poetry
	@echo "$(GREEN)Instalando dependencias...$(NC)"
	$(POETRY) install
	@echo "$(GREEN)Dependencias instaladas exitosamente$(NC)"

dev: ## Ejecutar servidor de desarrollo
	@echo "$(GREEN)Iniciando servidor de desarrollo...$(NC)"
	@echo "$(YELLOW)Servidor disponible en: http://$(HOST):$(PORT)$(NC)"
	@echo "$(YELLOW)Documentación en: http://$(HOST):$(PORT)/v1/docs$(NC)"
	$(POETRY) run uvicorn app.main:app --app-dir $(APP_DIR) --reload --host $(HOST) --port $(PORT)

test: ## Ejecutar tests
	@echo "$(GREEN)Ejecutando tests...$(NC)"
	$(POETRY) run pytest tests/ -v --tb=short

test-unit: ## Ejecutar solo tests unitarios
	@echo "$(GREEN)Ejecutando tests unitarios...$(NC)"
	$(POETRY) run pytest tests/unit/ -v --tb=short

test-e2e: ## Ejecutar solo tests e2e
	@echo "$(GREEN)Ejecutando tests e2e...$(NC)"
	$(POETRY) run pytest tests/e2e/ -v --tb=short

test-coverage: ## Ejecutar tests con cobertura
	@echo "$(GREEN)Ejecutando tests con cobertura...$(NC)"
	$(POETRY) run pytest tests/ --cov=api/app --cov-report=html --cov-report=term

lint: ## Ejecutar linting con ruff
	@echo "$(GREEN)Ejecutando linting...$(NC)"
	$(POETRY) run ruff check api/ tests/

lint-fix: ## Corregir errores de linting automáticamente
	@echo "$(GREEN)Corrigiendo errores de linting...$(NC)"
	$(POETRY) run ruff check api/ tests/ --fix

fmt: ## Formatear código con black
	@echo "$(GREEN)Formateando código...$(NC)"
	$(POETRY) run black api/ tests/

types: ## Verificar tipos con mypy
	@echo "$(GREEN)Verificando tipos...$(NC)"
	$(POETRY) run mypy api/

check: lint types test ## Ejecutar todas las verificaciones

clean: ## Limpiar archivos temporales
	@echo "$(GREEN)Limpiando archivos temporales...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage

build: ## Construir paquete
	@echo "$(GREEN)Construyendo paquete...$(NC)"
	$(POETRY) build

publish: ## Publicar paquete (solo para desarrollo)
	@echo "$(GREEN)Publicando paquete...$(NC)"
	$(POETRY) publish

shell: ## Abrir shell con entorno virtual
	@echo "$(GREEN)Abriendo shell con entorno virtual...$(NC)"
	$(POETRY) shell

update: ## Actualizar dependencias
	@echo "$(GREEN)Actualizando dependencias...$(NC)"
	$(POETRY) update

outdated: ## Mostrar dependencias desactualizadas
	@echo "$(GREEN)Dependencias desactualizadas:$(NC)"
	$(POETRY) show --outdated

env-example: ## Crear archivo .env.example
	@echo "$(GREEN)Creando archivo .env.example...$(NC)"
	@cp .env.example .env

logs: ## Ver logs en tiempo real (requiere que el servidor esté corriendo)
	@echo "$(GREEN)Mostrando logs en tiempo real...$(NC)"
	@echo "$(YELLOW)Presiona Ctrl+C para salir$(NC)"
	tail -f logs/app.log 2>/dev/null || echo "$(RED)No se encontraron logs$(NC)"

health: ## Verificar salud de la API
	@echo "$(GREEN)Verificando salud de la API...$(NC)"
	@curl -s http://$(HOST):$(PORT)/v1/healthz | jq . || echo "$(RED)API no disponible$(NC)"

docs: ## Abrir documentación en el navegador
	@echo "$(GREEN)Abriendo documentación...$(NC)"
	@echo "$(YELLOW)Documentación disponible en: http://$(HOST):$(PORT)/v1/docs$(NC)"
	@command -v xdg-open >/dev/null 2>&1 && xdg-open http://$(HOST):$(PORT)/v1/docs || \
	command -v open >/dev/null 2>&1 && open http://$(HOST):$(PORT)/v1/docs || \
	echo "$(YELLOW)Abre manualmente: http://$(HOST):$(PORT)/v1/docs$(NC)"

# Comandos de desarrollo específicos
dev-debug: ## Ejecutar servidor con debug habilitado
	@echo "$(GREEN)Iniciando servidor con debug...$(NC)"
	LOG_LEVEL=DEBUG $(POETRY) run uvicorn app.main:app --app-dir $(APP_DIR) --reload --host $(HOST) --port $(PORT) --log-level debug

dev-prod: ## Ejecutar servidor en modo producción
	@echo "$(GREEN)Iniciando servidor en modo producción...$(NC)"
	$(POETRY) run uvicorn app.main:app --app-dir $(APP_DIR) --host $(HOST) --port $(PORT) --workers 4

# Comandos de base de datos
db-migrate: ## Ejecutar migraciones de base de datos
	@echo "$(GREEN)Ejecutando migraciones...$(NC)"
	@echo "$(YELLOW)Ejecuta manualmente las migraciones en Supabase$(NC)"
	@echo "$(YELLOW)Archivos disponibles en: migrations/$(NC)"

db-seed: ## Poblar base de datos con datos de prueba
	@echo "$(GREEN)Poblando base de datos...$(NC)"
	@echo "$(YELLOW)Implementar seeding según necesidades$(NC)"

# Comandos de seguridad
security-scan: ## Escanear vulnerabilidades de seguridad
	@echo "$(GREEN)Escaneando vulnerabilidades...$(NC)"
	$(POETRY) run safety check

# Comandos de monitoreo
monitor: ## Monitorear recursos del sistema
	@echo "$(GREEN)Monitoreando recursos...$(NC)"
	@echo "$(YELLOW)CPU:$(NC)" && top -bn1 | grep "Cpu(s)" | awk '{print $$2}' | cut -d'%' -f1
	@echo "$(YELLOW)Memoria:$(NC)" && free -h | grep "Mem:"
	@echo "$(YELLOW)Disco:$(NC)" && df -h | grep -E '^/dev/'

# Comandos de backup
backup: ## Crear backup de configuración
	@echo "$(GREEN)Creando backup...$(NC)"
	@mkdir -p backups
	@tar -czf backups/finapp-backup-$$(date +%Y%m%d-%H%M%S).tar.gz \
		--exclude='.git' \
		--exclude='__pycache__' \
		--exclude='*.pyc' \
		--exclude='.pytest_cache' \
		--exclude='.mypy_cache' \
		--exclude='.ruff_cache' \
		--exclude='htmlcov' \
		--exclude='backups' \
		.
	@echo "$(GREEN)Backup creado en backups/$(NC)"

# Comandos de información
info: ## Mostrar información del proyecto
	@echo "$(GREEN)Información del proyecto:$(NC)"
	@echo "$(YELLOW)Nombre:$(NC) FinApp API"
	@echo "$(YELLOW)Versión:$(NC) 1.0.0"
	@echo "$(YELLOW)Python:$(NC) $$($(POETRY) run python --version)"
	@echo "$(YELLOW)Poetry:$(NC) $$($(POETRY) --version)"
	@echo "$(YELLOW)Directorio de app:$(NC) $(APP_DIR)"
	@echo "$(YELLOW)Puerto:$(NC) $(PORT)"
	@echo "$(YELLOW)Host:$(NC) $(HOST)"

# Comandos de limpieza específicos
clean-logs: ## Limpiar archivos de log
	@echo "$(GREEN)Limpiando logs...$(NC)"
	find . -name "*.log" -delete
	rm -rf logs/

clean-cache: ## Limpiar caché de Poetry
	@echo "$(GREEN)Limpiando caché de Poetry...$(NC)"
	$(POETRY) cache clear --all pypi

# Comandos de validación
validate: ## Validar configuración del proyecto
	@echo "$(GREEN)Validando configuración...$(NC)"
	@test -f pyproject.toml || (echo "$(RED)Error: pyproject.toml no encontrado$(NC)" && exit 1)
	@test -f .env.example || (echo "$(RED)Error: .env.example no encontrado$(NC)" && exit 1)
	@test -d $(APP_DIR) || (echo "$(RED)Error: Directorio $(APP_DIR) no encontrado$(NC)" && exit 1)
	@echo "$(GREEN)Configuración válida$(NC)"

# Comando por defecto
.DEFAULT_GOAL := help
