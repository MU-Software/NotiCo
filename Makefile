include .env
export $(shell sed 's/=.*//' .env)

HOST ?= 127.0.0.1
PORT ?= 8811

MKFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
PROJECT_DIR := $(dir $(MKFILE_PATH))

# Set additional build args for docker image build using make arguments
IMAGE_NAME := notico
ifeq (docker-build,$(firstword $(MAKECMDGOALS)))
  TAG_NAME := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  $(eval $(TAG_NAME):;@:)
endif
TAG_NAME := $(if $(TAG_NAME),$(TAG_NAME),local)
TAG_NAME_FOR_PROD := $(shell date +%Y%m%d-%H%M%S)

ifeq ($(DOCKER_DEBUG),true)
	DOCKER_MID_BUILD_OPTIONS = --progress=plain --no-cache
	DOCKER_END_BUILD_OPTIONS = 2>&1 | tee docker-build.log
else
	DOCKER_MID_BUILD_OPTIONS =
	DOCKER_END_BUILD_OPTIONS =
endif

# =============================================================================
# Local development commands

# Setup local environments
local-setup:
	@poetry install --no-root --sync

# Run local development server
local-api:
	@cd $(PROJECT_DIR)/runtime && poetry run chalice local --host $(HOST) --port $(PORT) --autoreload

# Devtools
hooks-install: local-setup
	poetry run pre-commit install

hooks-upgrade: local-setup
	poetry run pre-commit autoupdate

hooks-lint:
	poetry run pre-commit run --all-files

lint: hooks-lint  # alias

# =============================================================================
# AWS CDK related commands
stack-ecr-deploy:
	@cdk deploy notico-ecr

stack-queue-deploy:
	@cdk deploy notico-queue

stack-s3-deploy:
	@cdk deploy notico-s3

stack-lambda-deploy:
	@DOCKER_TAG=$(TAG_NAME_FOR_PROD) cdk deploy notico-app

stack-deploy: docker-build-prod stack-queue-deploy stack-s3-deploy stack-lambda-deploy

# =============================================================================
# Docker related commands

docker-prebuild:
	@cd $(PROJECT_DIR)/runtime && chalice package ../chalice-build
	@cd $(PROJECT_DIR) && unzip -o ./chalice-build/deployment.zip -d ./chalice-build/deployment
	@rm -f $(PROJECT_DIR)/chalice-build/deployment.zip

docker-postbuild:
	@rm -rf $(PROJECT_DIR)/chalice-build/

# Docker image build
# Usage: make docker-build <tag-name:=local>
# if you want to build with debug mode, set DOCKER_DEBUG=true
# ex) make docker-build or make docker-build some_TAG_NAME DOCKER_DEBUG=true
docker-build: docker-prebuild
	@docker build \
		-f ./Dockerfile -t $(IMAGE_NAME):$(TAG_NAME) \
		--platform linux/amd64 \
		--build-arg GIT_HASH=$(shell git rev-parse HEAD) \
		--build-arg IMAGE_BUILD_DATETIME=$(shell date +%Y-%m-%d_%H:%M:%S) \
		$(DOCKER_MID_BUILD_OPTIONS) $(PROJECT_DIR) $(DOCKER_END_BUILD_OPTIONS)

# Build docker image and push to ECR
docker-build-prod: stack-ecr-deploy docker-prebuild
	@aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
	@docker build \
		-f ./Dockerfile -t $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(IMAGE_NAME):$(TAG_NAME_FOR_PROD) \
		--platform linux/amd64 \
		--build-arg GIT_HASH=$(shell git rev-parse HEAD) \
		--build-arg IMAGE_BUILD_DATETIME=$(shell date +%Y-%m-%d_%H:%M:%S) \
		$(PROJECT_DIR)
	@docker push $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(IMAGE_NAME):$(TAG_NAME_FOR_PROD)
