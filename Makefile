# Docker configuration
IMAGE_NAME = goapi2api
VERSION = 1.0.0
DOCKER_HUB_USER = pingpongai
PORT = 8501

.PHONY: build run tag push clean all

# Build the Docker image
build:
	docker build -t $(IMAGE_NAME):$(VERSION) .

# Run the Docker container
run: build
	docker run -p $(PORT):$(PORT) $(IMAGE_NAME):$(VERSION)

# Run Docker container in detached mode
run-detached: build
	docker run -d -p $(PORT):$(PORT) --name $(IMAGE_NAME) $(IMAGE_NAME):$(VERSION)

# Tag the Docker image
tag: build
	docker tag $(IMAGE_NAME):$(VERSION) $(DOCKER_HUB_USER)/$(IMAGE_NAME):$(VERSION)
	docker tag $(IMAGE_NAME):$(VERSION) $(DOCKER_HUB_USER)/$(IMAGE_NAME):latest

# Push the Docker image to Docker Hub
push: tag
	docker push $(DOCKER_HUB_USER)/$(IMAGE_NAME):$(VERSION)
	docker push $(DOCKER_HUB_USER)/$(IMAGE_NAME):latest

# Stop and remove the container
stop:
	docker stop $(IMAGE_NAME) || true
	docker rm $(IMAGE_NAME) || true

# Clean up Docker images
clean: stop
	docker rmi $(IMAGE_NAME):$(VERSION) || true
	docker rmi $(DOCKER_HUB_USER)/$(IMAGE_NAME):$(VERSION) || true
	docker rmi $(DOCKER_HUB_USER)/$(IMAGE_NAME):latest || true

# Build, tag and push
all: build tag push 