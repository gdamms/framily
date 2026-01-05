.PHONY: help setup start stop restart startd clean

# Default target
help:
	@echo "Makefile commands:"
	@echo "  setup      - Build and start the development environment"
	@echo "  start      - Start the development environment"
	@echo "  startd     - Start the environment in detached mode"
	@echo "  stop       - Stop the development environment"
	@echo "  restart    - Restart the development environment"
	@echo "  clean      - Stop and remove all containers, networks, and volumes"

# Setup environment
setup:
	@echo "Setting up Framily development environment..."
	@sh ./scripts/setup.sh

# Start development environment
start:
	@echo "Starting Framily..."
	@docker-compose -f docker-compose.dev.yml up

# Detached start
startd:
	@echo "Starting Framily in detached mode..."
	@docker-compose -f docker-compose.dev.yml up -d

# Stop development environment
stop:
	@echo "Stopping Framily..."
	@docker-compose -f docker-compose.dev.yml down

# Restart services
restart:
	@echo "Restarting Framily..."
	@docker-compose -f docker-compose.dev.yml restart

# Clean up
clean:
	@echo "Cleaning up Framily..."
	@echo "This will remove all containers, networks, images, and volumes associated with Framily."
	@echo "Are you sure? (y/N)"
	@read ans; \
	if [ "$$ans" = "y" ] || [ "$$ans" = "Y" ]; then \
		docker-compose -f docker-compose.dev.yml down --rmi all --volumes --remove-orphans; \
		echo "Cleanup completed."; \
	else \
		echo "Cleanup aborted."; \
	fi
