# Hospital Management System Makefile

.PHONY: help install dev test clean migrate init-db run docker-build docker-run

# Default target
help:
	@echo "Hospital Management System - Available Commands:"
	@echo ""
	@echo "  install     - Install dependencies"
	@echo "  dev         - Install development dependencies"
	@echo "  test        - Run tests"
	@echo "  clean       - Clean up generated files"
	@echo "  migrate     - Run database migrations"
	@echo "  init-db     - Initialize database with sample data"
	@echo "  run         - Run development server"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run  - Run with Docker Compose"
	@echo ""

# Install dependencies
install:
	pip install -r requirements.txt

# Install development dependencies
dev: install
	pip install pytest pytest-asyncio httpx hypothesis

# Run tests
test:
	pytest -v

# Clean up generated files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -f test.db

# Run database migrations
migrate:
	alembic upgrade head

# Initialize database with sample data
init-db:
	python scripts/init_db.py

# Run development server
run:
	python run.py

# Build Docker image
docker-build:
	docker build -t hospital-management-system .

# Run with Docker Compose
docker-run:
	docker-compose up -d

# Stop Docker Compose
docker-stop:
	docker-compose down

# View Docker logs
docker-logs:
	docker-compose logs -f

# Format code
format:
	black app/ tests/ scripts/
	isort app/ tests/ scripts/

# Lint code
lint:
	flake8 app/ tests/ scripts/
	mypy app/

# Create new migration
migration:
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

# Backup database
backup:
	@echo "Creating database backup..."
	mkdir -p backups
	pg_dump $(DATABASE_URL) > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql

# Restore database
restore:
	@read -p "Enter backup file path: " file; \
	psql $(DATABASE_URL) < $$file