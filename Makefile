.PHONY: install test lint format-check docker-build docker-test docs-build public-index-generate public-index-up public-index-down public-index-smoke

SPECPM_PUBLIC_INDEX_PORT ?= 8081
SPECPM_PUBLIC_INDEX_REGISTRY_URL ?= http://localhost:$(SPECPM_PUBLIC_INDEX_PORT)
PUBLIC_INDEX_OUTPUT ?= .specpm/public-index
PUBLIC_INDEX_PACKAGE ?= examples/email_tools
PUBLIC_INDEX_SMOKE_CAPABILITY ?= document_conversion.email_to_markdown

install:
	python3 -m pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check src tests

format-check:
	ruff format --check src tests

docker-build:
	docker build -t specpm:dev .

docker-test:
	docker compose run --rm --entrypoint python specpm -m pytest

docs-build:
	swift package --allow-writing-to-directory ./.docc-build \
		generate-documentation \
		--target SpecPM \
		--output-path ./.docc-build \
		--transform-for-static-hosting \
		--hosting-base-path SpecPM

public-index-generate:
	PYTHONPATH=src python3 -m specpm.cli public-index generate $(PUBLIC_INDEX_PACKAGE) \
		--output $(PUBLIC_INDEX_OUTPUT) \
		--registry $(SPECPM_PUBLIC_INDEX_REGISTRY_URL) \
		--json

public-index-up:
	SPECPM_PUBLIC_INDEX_PORT=$(SPECPM_PUBLIC_INDEX_PORT) \
	SPECPM_PUBLIC_INDEX_REGISTRY_URL=$(SPECPM_PUBLIC_INDEX_REGISTRY_URL) \
	docker compose up -d --build public-index

public-index-down:
	docker compose stop public-index

public-index-smoke:
	PYTHONPATH=src python3 -m specpm.cli remote search $(PUBLIC_INDEX_SMOKE_CAPABILITY) \
		--registry $(SPECPM_PUBLIC_INDEX_REGISTRY_URL) \
		--json
