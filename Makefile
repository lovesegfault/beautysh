.PHONY: clean format lint test update

default: lint test build

clean:
	rm -f .coverage
	rm -fr .eggs
	rm -fr .pytest_cache
	rm -fr dist
	rm -fr **/__pycache__
	rm -fr build

format:
	isort .
	black .

lint:
	pre-commit run --all-files

test:
	pytest

build:
	poetry build

update:
	poetry update --lock
	nix flake update
