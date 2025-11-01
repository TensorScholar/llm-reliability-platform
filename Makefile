 .PHONY: help install test lint format check docker-build docker-up docker-down docker-logs docker-clean api run-sdk quickstart

 help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

 install: ## Install platform and SDK dependencies
	cd LLM-REALIABILITY-PLATFORM/platform && poetry install
	cd LLM-REALIABILITY-PLATFORM/sdk/python && poetry install

 api: ## Run API locally with reload
	cd LLM-REALIABILITY-PLATFORM/platform && uvicorn reliability_platform.main:app --host 0.0.0.0 --port 8000 --reload

 docker-build: ## Build Docker images
	docker-compose build

 docker-up: ## Start local stack
	docker-compose up -d

 docker-down: ## Stop local stack
	docker-compose down

 docker-logs: ## Tail logs
	docker-compose logs -f

 docker-clean: ## Clean Docker resources and volumes
	docker-compose down -v
	docker system prune -f

 quickstart: ## Start infra and API
	@echo "Starting TimescaleDB, Kafka, Redis, and API..."
	docker-compose up -d timescaledb kafka redis platform-api
	@echo "API docs: http://localhost:8000/docs"

