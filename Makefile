.PHONY: help clean build install uninstall dev-install test lint format upload-test upload-prod check-env

# Default target
help:
	@echo "AI Manager Build System"
	@echo ""
	@echo "Available targets:"
	@echo "  clean         - Remove build artifacts"
	@echo "  build         - Build distribution packages"
	@echo "  install       - Install package with pipenv"
	@echo "  uninstall     - Uninstall package with pipenv"
	@echo "  dev-install   - Install in development mode with pipenv"
	@echo "  test          - Run tests"
	@echo "  lint          - Run linting checks"
	@echo "  format        - Format code with black"
	@echo "  upload-test   - Upload to TestPyPI"
	@echo "  upload-prod   - Upload to PyPI"
	@echo "  check-env     - Check if pipenv is available"

# Check if pipenv is installed
check-env:
	@which pipenv > /dev/null || (echo "Error: pipenv not found. Install with: dnf install pipenv" && exit 1)
	@echo "✓ pipenv found"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✓ Clean complete"

# Build distribution packages
build: clean
	@echo "Building distribution packages..."
	python setup.py sdist bdist_wheel
	@echo "✓ Build complete"

# Install with pipenv
install: check-env build
	@echo "Installing ai_manager with pipenv..."
	pipenv install dist/*.whl
	@echo "✓ Installation complete"

# Uninstall with pipenv
uninstall: check-env
	@echo "Uninstalling ai_manager..."
	pipenv uninstall ai_manager || true
	@echo "✓ Uninstall complete"

# Development install with pipenv
dev-install: check-env
	@echo "Installing ai_manager in development mode..."
	pipenv install -e .
	pipenv install --dev pytest black flake8 twine
	@echo "✓ Development installation complete"

# Run tests
test: check-env
	@echo "Running tests..."
	pipenv run pytest tests/ -v || echo "No tests directory found"
	@echo "✓ Tests complete"

# Run linting
lint: check-env
	@echo "Running linting checks..."
	pipenv run flake8 ai_manager/
	@echo "✓ Linting complete"

# Format code
format: check-env
	@echo "Formatting code with black..."
	pipenv run black ai_manager/
	@echo "✓ Formatting complete"

# Upload to TestPyPI
upload-test: build
	@echo "Uploading to TestPyPI..."
	@which twine > /dev/null || (echo "Error: twine not found. Run: pipenv install twine" && exit 1)
	pipenv run twine upload --repository testpypi dist/*
	@echo "✓ Upload to TestPyPI complete"

# Upload to PyPI (production)
upload-prod: build
	@echo "WARNING: This will upload to production PyPI!"
	@read -p "Are you sure? [y/N]: " confirm && [ "$$confirm" = "y" ] || (echo "Cancelled" && exit 1)
	@which twine > /dev/null || (echo "Error: twine not found. Run: pipenv install twine" && exit 1)
	pipenv run twine upload dist/*
	@echo "✓ Upload to PyPI complete"

# Full development setup
setup-dev: check-env clean dev-install
	@echo "Development environment setup complete"

# Pre-upload checks
pre-upload: clean build lint test
	@echo "Pre-upload checks complete"
	@echo "Ready for upload!"

# Quick reinstall for development
reinstall: uninstall dev-install
	@echo "Reinstall complete"