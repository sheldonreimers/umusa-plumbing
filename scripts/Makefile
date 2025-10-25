# Variables
SERVICE_NAME=ops-scripts
TAG=trunk
IMAGE_NAME=$(SERVICE_NAME)
REPOSITORY=europe-west4-docker.pkg.dev/tebi-live-data
REGISTRY_NAME=data
FULL_IMAGE_NAME = $(REPOSITORY)/$(REGISTRY_NAME)/$(IMAGE_NAME)

.PHONY: build-docker ensure-docker-image run-hubspot-accounts push help

# Default target
help:
	@echo "Available targets:"
	@echo "  help                    - Show this help message"
	@echo "  build-docker            - Build Docker image"
	@echo "  ensure-docker-image     - Ensure Docker image exists"
	@echo "  run-hubspot-accounts    - Run HubSpot Accounts synchronization"
	@echo "  push                    - Push Docker image to registry"

build-docker:
	@echo "Building Docker image..."
	docker buildx build \
		--platform linux/amd64 \
		-t $(IMAGE_NAME) .
	@echo "✅ Docker image built successfully"

ensure-docker-image:
	@if ! docker image inspect $(IMAGE_NAME):latest >/dev/null 2>&1; then \
		echo "Docker image $(IMAGE_NAME):latest not found. Building..." ; \
		$(MAKE) build-docker ; \
	else \
		echo "✅ Docker image $(IMAGE_NAME):latest found" ; \
	fi

run-hubspot-accounts: ensure-docker-image
	@echo "Running HubSpot Accounts synchronization..."
	docker run \
		--env-file .env \
		-e GOOGLE_APPLICATION_CREDENTIALS="/root/.config/gcloud/application_default_credentials.json" \
		-v "$HOME/.config/gcloud:/root/.config/gcloud:ro" \
		--rm \
		-it $(IMAGE_NAME):latest

# Push Docker image
push: build-docker
	@echo "Tagging and pushing Docker image..."
	docker tag $(IMAGE_NAME):latest $(FULL_IMAGE_NAME):$(TAG)
	docker push $(FULL_IMAGE_NAME):$(TAG)
	@echo "✅ Docker image pushed successfully"
