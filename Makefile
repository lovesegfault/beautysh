.PHONY: lint test update

lint:
	poetry run pre-commit run --all-files

test: lint
	poetry run pytest

build: test
	poetry build

update:
	poetry update --lock
	nix flake update
