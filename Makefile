.PHONY: install test lint format-check docker-build docker-test docs-build public-index-generate public-index-up public-index-reload public-index-down public-index-wait public-index-smoke dev-up dev-reload dev-smoke dev-down pages-smoke

SPECPM_PUBLIC_INDEX_PORT ?= 8081
SPECPM_PUBLIC_INDEX_REGISTRY_URL ?= http://localhost:$(SPECPM_PUBLIC_INDEX_PORT)
PAGES_REGISTRY_URL ?= https://0al-spec.github.io/SpecPM
PUBLIC_INDEX_OUTPUT ?= .specpm/public-index
PUBLIC_INDEX_MANIFEST ?= public-index/accepted-packages.yml
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
	PYTHONPATH=src python3 -m specpm.cli public-index generate \
		--manifest $(PUBLIC_INDEX_MANIFEST) \
		--output $(PUBLIC_INDEX_OUTPUT) \
		--registry $(SPECPM_PUBLIC_INDEX_REGISTRY_URL) \
		--json

public-index-up:
	SPECPM_PUBLIC_INDEX_PORT=$(SPECPM_PUBLIC_INDEX_PORT) \
	SPECPM_PUBLIC_INDEX_REGISTRY_URL=$(SPECPM_PUBLIC_INDEX_REGISTRY_URL) \
	SPECPM_PUBLIC_INDEX_MANIFEST=$(PUBLIC_INDEX_MANIFEST) \
	docker compose up -d --build public-index

public-index-reload:
	SPECPM_PUBLIC_INDEX_PORT=$(SPECPM_PUBLIC_INDEX_PORT) \
	SPECPM_PUBLIC_INDEX_REGISTRY_URL=$(SPECPM_PUBLIC_INDEX_REGISTRY_URL) \
	SPECPM_PUBLIC_INDEX_MANIFEST=$(PUBLIC_INDEX_MANIFEST) \
	docker compose up -d --build --force-recreate public-index

public-index-down:
	docker compose stop public-index

public-index-wait:
	@for attempt in 1 2 3 4 5 6 7 8 9 10; do \
		PYTHONPATH=src python3 -m specpm.cli remote status \
			--registry $(SPECPM_PUBLIC_INDEX_REGISTRY_URL) \
			--json >/dev/null 2>&1 && exit 0; \
		sleep 1; \
	done; \
	PYTHONPATH=src python3 -m specpm.cli remote status \
		--registry $(SPECPM_PUBLIC_INDEX_REGISTRY_URL) \
		--json >/dev/null

public-index-smoke: public-index-wait
	PYTHONPATH=src python3 -m specpm.cli remote status \
		--registry $(SPECPM_PUBLIC_INDEX_REGISTRY_URL) \
		--json
	PYTHONPATH=src python3 -m specpm.cli remote packages \
		--registry $(SPECPM_PUBLIC_INDEX_REGISTRY_URL) \
		--json
	PYTHONPATH=src python3 -m specpm.cli remote search $(PUBLIC_INDEX_SMOKE_CAPABILITY) \
		--registry $(SPECPM_PUBLIC_INDEX_REGISTRY_URL) \
		--json

dev-up: public-index-up public-index-smoke

dev-reload: public-index-reload public-index-smoke

dev-smoke: public-index-smoke

dev-down: public-index-down

pages-smoke:
	PYTHONPATH=src python3 -m specpm.cli remote status \
		--registry $(PAGES_REGISTRY_URL) \
		--json
	PYTHONPATH=src python3 -m specpm.cli remote packages \
		--registry $(PAGES_REGISTRY_URL) \
		--json
	PYTHONPATH=src python3 -m specpm.cli remote search $(PUBLIC_INDEX_SMOKE_CAPABILITY) \
		--registry $(PAGES_REGISTRY_URL) \
		--json
