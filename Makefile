# Blog Development Makefile
# Common commands for Hugo development and publishing workflow

.PHONY: dev build publish-dry clean help

# Default target
.DEFAULT_GOAL := help

# Hugo settings
HUGO := hugo
HUGO_DEV_ENV := development
HUGO_PROD_ENV := production

# Scripts directory
SCRIPTS_DIR := scripts

#------------------------------------------------------------------------------
# Development
#------------------------------------------------------------------------------

## Start Hugo development server with development config (local MinIO URLs)
dev:
	$(HUGO) server -e $(HUGO_DEV_ENV) --buildDrafts --buildFuture

#------------------------------------------------------------------------------
# Build
#------------------------------------------------------------------------------

## Build the site for production
build:
	$(HUGO) -e $(HUGO_PROD_ENV)

## Build with verbose output
build-verbose:
	$(HUGO) -e $(HUGO_PROD_ENV) --verbose

#------------------------------------------------------------------------------
# Publishing
#------------------------------------------------------------------------------

## Dry-run publish scan - preview what would be published without making changes
publish-dry:
	python3 $(SCRIPTS_DIR)/publish.py publish --all --dry-run

## Scan vault for notes marked with publish: true
publish-scan:
	python3 $(SCRIPTS_DIR)/publish.py scan

## List all publishable notes and their target paths
publish-list:
	python3 $(SCRIPTS_DIR)/publish.py list

#------------------------------------------------------------------------------
# Utilities
#------------------------------------------------------------------------------

## Clean generated files
clean:
	rm -rf public/
	rm -f .hugo_build.lock

## Run tests for publish scripts
test:
	cd $(SCRIPTS_DIR) && python3 -m pytest -v

#------------------------------------------------------------------------------
# Help
#------------------------------------------------------------------------------

## Show this help message
help:
	@echo "Blog Development Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/## /  /' | while read line; do \
		target=$$(echo "$$line" | head -1); \
		echo "$$target"; \
	done
	@echo ""
	@echo "Main Targets:"
	@echo "  dev          - Start Hugo dev server with development config"
	@echo "  build        - Build site for production"
	@echo "  publish-dry  - Dry-run publish scan (preview only)"
	@echo ""
	@echo "Other Targets:"
	@echo "  publish-scan - Scan vault for publishable notes"
	@echo "  publish-list - List notes and their target paths"
	@echo "  clean        - Remove generated files"
	@echo "  test         - Run publish script tests"
