.PHONY: install test lint format-check docker-build docker-test

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

