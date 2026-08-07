.PHONY: help setup start stop restart startd clean start-prod start-prodd stop-prod start-demo start-demod stop-demo

DEV_COMPOSE_FILE=config/compose/docker-compose.dev.yml
PROD_COMPOSE_FILE=config/compose/docker-compose.prod.yml
DEMO_COMPOSE_FILE=config/compose/docker-compose.demo.yml
DEV_ENV_FILE=config/env/.dev.env
PROD_ENV_FILE=config/env/.prod.env
DEMO_ENV_FILE=config/env/.demo.env

# Default target
help:
	@echo "Makefile commands:"
	@echo "  setup       - Build and start the development environment"
	@echo "  start       - Start the development environment"
	@echo "  startd      - Start the environment in detached mode"
	@echo "  stop        - Stop the development environment"
	@echo "  restart     - Restart the development environment"
	@echo "  clean       - Stop and remove all containers, networks, and volumes"
	@echo "  start-prod  - Start the production compose stack (builds from source)"
	@echo "  start-prodd - Start production stack in detached mode"
	@echo "  stop-prod   - Stop the production compose stack"
	@echo "  start-demo  - Start the demo stack (pulls the published image, no build)"
	@echo "  start-demod - Start the demo stack in detached mode"
	@echo "  stop-demo   - Stop the demo stack"

# Setup environment
setup:
	@echo "Setting up Framily development environment..."
	@sh ./scripts/setup.sh

# Start development environment
start:
	@echo "Starting Framily..."
	@docker-compose -f $(DEV_COMPOSE_FILE) --env-file $(DEV_ENV_FILE) up

# Detached start
startd:
	@echo "Starting Framily in detached mode..."
	@docker-compose -f $(DEV_COMPOSE_FILE) --env-file $(DEV_ENV_FILE) up -d

# Stop development environment
stop:
	@echo "Stopping Framily..."
	@docker-compose -f $(DEV_COMPOSE_FILE) --env-file $(DEV_ENV_FILE) down

# Restart services
restart:
	@echo "Restarting Framily..."
	@docker-compose -f $(DEV_COMPOSE_FILE) --env-file $(DEV_ENV_FILE) restart

# Clean up
clean:
	@echo "Cleaning up Framily..."
	@echo "This will remove all containers, networks, images, and volumes associated with Framily."
	@echo "Are you sure? (y/N)"
	@read ans; \
	if [ "$$ans" = "y" ] || [ "$$ans" = "Y" ]; then \
		docker-compose -f $(DEV_COMPOSE_FILE) --env-file $(DEV_ENV_FILE) down --rmi all --volumes --remove-orphans; \
		echo "Cleanup completed."; \
	else \
		echo "Cleanup aborted."; \
	fi

# Start production environment
start-prod:
	@echo "Starting Framily production stack..."
	@docker-compose -f $(PROD_COMPOSE_FILE) --env-file $(PROD_ENV_FILE) up

# Detached production start
start-prodd:
	@echo "Starting Framily production stack in detached mode..."
	@docker-compose -f $(PROD_COMPOSE_FILE) --env-file $(PROD_ENV_FILE) up -d

# Stop production environment
stop-prod:
	@echo "Stopping Framily production stack..."
	@docker-compose -f $(PROD_COMPOSE_FILE) --env-file $(PROD_ENV_FILE) down

# Start demo environment (pulls the published image instead of building)
start-demo:
	@echo "Starting Framily demo stack..."
	@docker-compose -f $(DEMO_COMPOSE_FILE) --env-file $(DEMO_ENV_FILE) up

# Detached demo start
start-demod:
	@echo "Starting Framily demo stack in detached mode..."
	@docker-compose -f $(DEMO_COMPOSE_FILE) --env-file $(DEMO_ENV_FILE) up -d

# Stop demo environment
stop-demo:
	@echo "Stopping Framily demo stack..."
	@docker-compose -f $(DEMO_COMPOSE_FILE) --env-file $(DEMO_ENV_FILE) down
