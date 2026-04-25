.PHONY: install test lint format-check docker-build docker-test docs-build

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
