# Makefile for Amazon Price Fetch

.PHONY: install test format lint type-check clean help

# Install dependencies
install:
	poetry install

# Run tests
test:
	poetry run pytest tests/ -v

# Format code
format:
	poetry run black src/ tests/
	poetry run isort src/ tests/

# Lint code
lint:
	poetry run flake8 src/ tests/

# Type checking
type-check:
	poetry run mypy src/

# Clean cache and build artifacts
clean:
	rm -rf .cache/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete

# Search examples
search-example:
	poetry run amazon-price-fetch search --query "wireless mouse" --pages 2 --output data/mice.csv

search-example-verbose:
	poetry run amazon-price-fetch search --query "laptop" --pages 1 --verbose

# Show help
help:
	@echo "Available commands:"
	@echo "  install        - Install dependencies"
	@echo "  test           - Run tests"
	@echo "  format         - Format code"
	@echo "  lint           - Lint code"
	@echo "  type-check     - Run type checking"
	@echo "  clean          - Clean cache and artifacts"
	@echo "  search-example - Run example search"
	@echo "  help           - Show this help"

# Default target
default: help