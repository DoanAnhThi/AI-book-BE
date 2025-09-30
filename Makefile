.PHONY: help dev dev-build dev-up dev-down dev-logs prod prod-build prod-up prod-deploy prod-down prod-logs clean build-prod push-prod

# Default target
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

# Development commands
dev: ## Start development environment
	docker compose -f docker-compose.dev.yml --profile dev up -d

dev-build: ## Build and start development environment
	docker compose -f docker-compose.dev.yml --profile dev up --build -d

dev-up: ## Start development environment (alias for dev)
	docker compose -f docker-compose.dev.yml --profile dev up -d

dev-down: ## Stop development environment
	docker compose -f docker-compose.dev.yml --profile dev down

dev-logs: ## Show development logs
	docker compose -f docker-compose.dev.yml --profile dev logs -f

dev-restart: ## Restart development environment
	docker compose -f docker-compose.dev.yml --profile dev restart

# Production commands
prod: ## Start production environment
	docker compose -f docker-compose.prod.yml --profile prod up -d

prod-build: ## Build production image
	docker build -f Dockerfile.prod -t genbook-api:latest .

prod-up: ## Start production environment with existing image
	docker compose -f docker-compose.prod.yml --profile prod up -d

prod-deploy: prod-build prod-up ## Build and deploy production

prod-down: ## Stop production environment
	docker compose -f docker-compose.prod.yml --profile prod down

prod-logs: ## Show production logs
	docker compose -f docker-compose.prod.yml --profile prod logs -f

prod-restart: ## Restart production environment
	docker compose -f docker-compose.prod.yml --profile prod restart

# Utility commands
clean: ## Remove all containers and volumes
	docker compose -f docker-compose.dev.yml --profile dev down -v
	docker compose -f docker-compose.prod.yml --profile prod down -v
	docker system prune -f

clean-dev: ## Remove development containers and volumes
	docker compose -f docker-compose.dev.yml --profile dev down -v

clean-prod: ## Remove production containers and volumes
	docker compose -f docker-compose.prod.yml --profile prod down -v

# Database commands
db-dev: ## Access development database
	docker compose -f docker-compose.dev.yml --profile dev exec db psql -U dev_user -d gen_book_dev

db-prod: ## Access production database
	docker compose -f docker-compose.prod.yml --profile prod exec db psql -U ${DB_USER} -d ${DB_NAME}

# Testing commands
test: ## Run tests (if you have tests)
	docker compose -f docker-compose.dev.yml --profile dev exec ai-book python -m pytest

# Setup commands
setup-dev: ## Setup development environment files
	cp env-dev.txt .env.dev
	cp env-example.txt .env.example
	@echo "Please update .env.dev with your actual API keys and credentials"

setup-prod: ## Setup production environment files
	cp env-prod.txt .env.prod
	@echo "Please update .env.prod with your production credentials"
	@echo "Make sure to set environment variables on your server"

# Docker management
docker-clean: ## Clean up Docker system
	docker system prune -f
	docker volume prune -f
	docker image prune -f

# CI/CD helpers
build-prod-image: ## Build production image with tag
	docker build -f Dockerfile.prod -t genbook-api:$(shell git rev-parse --short HEAD) .
	docker tag genbook-api:$(shell git rev-parse --short HEAD) genbook-api:latest

push-prod-image: ## Push production image to registry (configure registry first)
	@echo "Configure your container registry in this command"
	# docker tag genbook-api:latest your-registry/genbook-api:latest
	# docker push your-registry/genbook-api:latest
