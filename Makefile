.PHONY: install test lint format-check docker-build docker-test docs-build public-index-generate public-index-up public-index-reload public-index-down public-index-wait public-index-smoke public-alpha-smoke public-alpha-report dev-up dev-reload dev-smoke dev-down pages-smoke pages-alpha-smoke pages-alpha-report

PYTHON ?= $(shell if [ -x .venv/bin/python ]; then printf '%s' .venv/bin/python; else command -v python3; fi)
SPECPM_PUBLIC_INDEX_PORT ?= 8081
SPECPM_PUBLIC_INDEX_REGISTRY_URL ?= http://localhost:$(SPECPM_PUBLIC_INDEX_PORT)
PAGES_REGISTRY_URL ?= https://0al-spec.github.io/SpecPM
PUBLIC_INDEX_OUTPUT ?= .specpm/public-index
PUBLIC_INDEX_MANIFEST ?= public-index/accepted-packages.yml
PUBLIC_INDEX_SMOKE_CAPABILITY ?= document_conversion.email_to_markdown
PUBLIC_INDEX_SMOKE_INTENT ?= intent.document_conversion.email_to_markdown
PUBLIC_ALPHA_SMOKE_PACKAGE ?= specnode.core
PUBLIC_ALPHA_SMOKE_VERSION ?= specnode.core@0.1.0
PUBLIC_ALPHA_SMOKE_CAPABILITY ?= specnode.typed_job_protocol
PUBLIC_ALPHA_REPORT_OUTPUT ?= .specpm/public-alpha-observation.json
PAGES_ALPHA_REPORT_OUTPUT ?= .specpm/pages-alpha-observation.json
SPECPM_VERSION ?= $(shell PYTHONPATH=src $(PYTHON) -c 'from specpm import __version__; print(__version__)')
PAGES_BUILD_NUMBER ?= local
PAGES_BUILD_REVISION ?= $(shell git rev-parse HEAD 2>/dev/null || printf 'unknown')
PAGES_CUSTOM_DOMAIN ?=
PUBLIC_ALPHA_OBSERVE_ARGS ?= \
	--package specpm.core \
	--package $(PUBLIC_ALPHA_SMOKE_PACKAGE) \
	--version specpm.core@0.1.0 \
	--version $(PUBLIC_ALPHA_SMOKE_VERSION) \
	--capability specpm.registry.public_alpha_index \
	--capability $(PUBLIC_ALPHA_SMOKE_CAPABILITY)
PUBLIC_INDEX_COMPOSE_ARGS ?=

install:
	$(PYTHON) -m pip --version >/dev/null 2>&1 || $(PYTHON) -m ensurepip --upgrade
	$(PYTHON) -m pip install -e ".[dev]"

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check src tests

format-check:
	$(PYTHON) -m ruff format --check src tests

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
	PYTHONPATH=src $(PYTHON) scripts/render_pages.py \
		--output ./.docc-build \
		--specpm-version $(SPECPM_VERSION) \
		--build-number $(PAGES_BUILD_NUMBER) \
		--build-revision $(PAGES_BUILD_REVISION) \
		$(if $(PAGES_CUSTOM_DOMAIN),--custom-domain $(PAGES_CUSTOM_DOMAIN),)

public-index-generate:
	PYTHONPATH=src $(PYTHON) -m specpm.cli public-index generate \
		--manifest $(PUBLIC_INDEX_MANIFEST) \
		--output $(PUBLIC_INDEX_OUTPUT) \
		--registry $(SPECPM_PUBLIC_INDEX_REGISTRY_URL) \
		--specpm-version $(SPECPM_VERSION) \
		--build-number $(PAGES_BUILD_NUMBER) \
		--build-revision $(PAGES_BUILD_REVISION) \
		--json

public-index-up:
	SPECPM_PUBLIC_INDEX_PORT=$(SPECPM_PUBLIC_INDEX_PORT) \
	SPECPM_PUBLIC_INDEX_REGISTRY_URL=$(SPECPM_PUBLIC_INDEX_REGISTRY_URL) \
	SPECPM_PUBLIC_INDEX_MANIFEST=$(PUBLIC_INDEX_MANIFEST) \
	SPECPM_VERSION=$(SPECPM_VERSION) \
	SPECPM_PUBLIC_INDEX_BUILD_NUMBER=$(PAGES_BUILD_NUMBER) \
	SPECPM_PUBLIC_INDEX_BUILD_REVISION=$(PAGES_BUILD_REVISION) \
	docker compose up -d --build $(PUBLIC_INDEX_COMPOSE_ARGS) public-index

public-index-reload:
	$(MAKE) public-index-up PUBLIC_INDEX_COMPOSE_ARGS="--force-recreate"

public-index-down:
	docker compose stop public-index

public-index-wait:
	@for attempt in 1 2 3 4 5 6 7 8 9 10; do \
		PYTHONPATH=src $(PYTHON) -m specpm.cli remote status \
			--registry $(SPECPM_PUBLIC_INDEX_REGISTRY_URL) \
			--json >/dev/null 2>&1 && exit 0; \
		sleep 1; \
	done; \
	PYTHONPATH=src $(PYTHON) -m specpm.cli remote status \
		--registry $(SPECPM_PUBLIC_INDEX_REGISTRY_URL) \
		--json >/dev/null

public-index-smoke: public-index-wait
	PYTHONPATH=src $(PYTHON) -m specpm.cli remote status \
		--registry $(SPECPM_PUBLIC_INDEX_REGISTRY_URL) \
		--json
	PYTHONPATH=src $(PYTHON) -m specpm.cli remote packages \
		--registry $(SPECPM_PUBLIC_INDEX_REGISTRY_URL) \
		--json
	PYTHONPATH=src $(PYTHON) -m specpm.cli remote intents \
		--registry $(SPECPM_PUBLIC_INDEX_REGISTRY_URL) \
		--json
	PYTHONPATH=src $(PYTHON) -m specpm.cli remote intent $(PUBLIC_INDEX_SMOKE_INTENT) \
		--registry $(SPECPM_PUBLIC_INDEX_REGISTRY_URL) \
		--json
	PYTHONPATH=src $(PYTHON) -m specpm.cli remote search $(PUBLIC_INDEX_SMOKE_CAPABILITY) \
		--registry $(SPECPM_PUBLIC_INDEX_REGISTRY_URL) \
		--json
	PYTHONPATH=src $(PYTHON) -m specpm.cli remote search-intent $(PUBLIC_INDEX_SMOKE_INTENT) \
		--registry $(SPECPM_PUBLIC_INDEX_REGISTRY_URL) \
		--json

public-alpha-smoke: public-index-smoke
	PYTHONPATH=src $(PYTHON) -m specpm.cli remote package $(PUBLIC_ALPHA_SMOKE_PACKAGE) \
		--registry $(SPECPM_PUBLIC_INDEX_REGISTRY_URL) \
		--json
	PYTHONPATH=src $(PYTHON) -m specpm.cli remote version $(PUBLIC_ALPHA_SMOKE_VERSION) \
		--registry $(SPECPM_PUBLIC_INDEX_REGISTRY_URL) \
		--json
	PYTHONPATH=src $(PYTHON) -m specpm.cli remote search $(PUBLIC_ALPHA_SMOKE_CAPABILITY) \
		--registry $(SPECPM_PUBLIC_INDEX_REGISTRY_URL) \
		--json

public-alpha-report: public-index-wait
	mkdir -p $(dir $(PUBLIC_ALPHA_REPORT_OUTPUT))
	PYTHONPATH=src $(PYTHON) -m specpm.cli remote observe $(PUBLIC_ALPHA_OBSERVE_ARGS) \
		--registry $(SPECPM_PUBLIC_INDEX_REGISTRY_URL) \
		--json > $(PUBLIC_ALPHA_REPORT_OUTPUT)
	cat $(PUBLIC_ALPHA_REPORT_OUTPUT)

dev-up: public-index-up public-index-smoke

dev-reload: public-index-reload public-index-smoke

dev-smoke: public-index-smoke

dev-down: public-index-down

pages-smoke:
	PYTHONPATH=src $(PYTHON) -m specpm.cli remote status \
		--registry $(PAGES_REGISTRY_URL) \
		--json
	PYTHONPATH=src $(PYTHON) -m specpm.cli remote packages \
		--registry $(PAGES_REGISTRY_URL) \
		--json
	PYTHONPATH=src $(PYTHON) -m specpm.cli remote intents \
		--registry $(PAGES_REGISTRY_URL) \
		--json
	PYTHONPATH=src $(PYTHON) -m specpm.cli remote intent $(PUBLIC_INDEX_SMOKE_INTENT) \
		--registry $(PAGES_REGISTRY_URL) \
		--json
	PYTHONPATH=src $(PYTHON) -m specpm.cli remote search $(PUBLIC_INDEX_SMOKE_CAPABILITY) \
		--registry $(PAGES_REGISTRY_URL) \
		--json
	PYTHONPATH=src $(PYTHON) -m specpm.cli remote search-intent $(PUBLIC_INDEX_SMOKE_INTENT) \
		--registry $(PAGES_REGISTRY_URL) \
		--json

pages-alpha-smoke: pages-smoke
	PYTHONPATH=src $(PYTHON) -m specpm.cli remote package $(PUBLIC_ALPHA_SMOKE_PACKAGE) \
		--registry $(PAGES_REGISTRY_URL) \
		--json
	PYTHONPATH=src $(PYTHON) -m specpm.cli remote version $(PUBLIC_ALPHA_SMOKE_VERSION) \
		--registry $(PAGES_REGISTRY_URL) \
		--json
	PYTHONPATH=src $(PYTHON) -m specpm.cli remote search $(PUBLIC_ALPHA_SMOKE_CAPABILITY) \
		--registry $(PAGES_REGISTRY_URL) \
		--json

pages-alpha-report:
	mkdir -p $(dir $(PAGES_ALPHA_REPORT_OUTPUT))
	PYTHONPATH=src $(PYTHON) -m specpm.cli remote observe $(PUBLIC_ALPHA_OBSERVE_ARGS) \
		--registry $(PAGES_REGISTRY_URL) \
		--json > $(PAGES_ALPHA_REPORT_OUTPUT)
	cat $(PAGES_ALPHA_REPORT_OUTPUT)
