# Agentic Arbitrage Factory - Makefile
# Common development tasks

.PHONY: help install install-dev test test-coverage lint format clean run demo status docker-build docker-run

# Default target
help:
	@echo "Agentic Arbitrage Factory - Available Commands:"
	@echo ""
	@echo "  make install       - Install dependencies"
	@echo "  make install-dev   - Install dev dependencies"
	@echo "  make test          - Run tests"
	@echo "  make test-coverage - Run tests with coverage"
	@echo "  make lint          - Run linter"
	@echo "  make format        - Format code"
	@echo "  make clean         - Clean build artifacts"
	@echo "  make run           - Run factory once"
	@echo "  make demo          - Run demo"
	@echo "  make status        - Check factory status"
	@echo "  make continuous    - Run factory continuously"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-run    - Run Docker container"
	@echo ""

# Installation
install:
	uv sync

install-dev:
	uv sync --extra dev

# Testing
test:
	uv run pytest tests/ -v

test-coverage:
	uv run pytest tests/ --cov=. --cov-report=html --cov-report=term

# Code quality
lint:
	uv run flake8 agents/ core/ config/ --max-line-length=100
	uv run mypy agents/ core/ config/ --ignore-missing-imports

format:
	uv run black agents/ core/ config/ --line-length=100
	uv run isort agents/ core/ config/ --profile=black

format-check:
	uv run black agents/ core/ config/ --line-length=100 --check
	uv run isort agents/ core/ config/ --profile=black --check

# Cleaning
clean:
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

clean-data:
	rm -f data/factory.db
	rm -f data/factory.log

clean-all: clean clean-data

# Running
run:
	uv run python factory.py run

demo:
	uv run python demo.py

status:
	uv run python factory.py status

continuous:
	uv run python factory.py continuous

discover:
	uv run python factory.py discover

validate:
	uv run python factory.py validate

build:
	uv run python factory.py build

cull:
	uv run python factory.py cull

# Dashboard
dashboard:
	uv run python dashboard.py

# Database
db-shell:
	sqlite3 data/factory.db

db-backup:
	mkdir -p backups
	sqlite3 data/factory.db ".backup 'backups/factory_$$(date +%Y%m%d_%H%M%S).db'"

db-restore:
	@echo "Usage: make db-restore FILE=backups/factory_YYYYMMDD_HHMMSS.db"
	@if [ -f "$(FILE)" ]; then \
		sqlite3 data/factory.db ".restore '$(FILE)'"; \
	else \
		echo "File not found: $(FILE)"; \
	fi

# Docker
docker-build:
	docker build -t agentic-factory .

docker-run:
	docker run -d \
		--name agentic-factory \
		-v $$(pwd)/data:/app/data \
		-v $$(pwd)/sites:/app/sites \
		agentic-factory

docker-stop:
	docker stop agentic-factory
	docker rm agentic-factory

docker-logs:
	docker logs -f agentic-factory

docker-compose-up:
	docker-compose up -d

docker-compose-down:
	docker-compose down

docker-compose-logs:
	docker-compose logs -f

# Development setup
setup: install-dev
	uv run pre-commit install
	mkdir -p data sites archive
	cp .env.example .env
	@echo "Setup complete! Edit .env file with your API keys."

# Release
release-patch:
	uv run bumpversion patch

release-minor:
	uv run bumpversion minor

release-major:
	uv run bumpversion major

# Documentation
docs-serve:
	uv run mkdocs serve

docs-build:
	uv run mkdocs build

size:
	du -sh .
	du -sh data/
	du -sh sites/

logs:
	tail -f data/factory.log

# CI/CD targets for GitHub Actions
ci-test: install-dev test lint format-check

ci-build: docker-build
