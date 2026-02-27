SHELL := /usr/bin/env bash

.PHONY: venv deps db-up db-apply db-bootstrap api fe test smoke verify dev

venv:
	bash scripts/bootstrap_venv.sh

deps: venv

db-up:
	docker compose -f docker/docker-compose.yml up -d postgres

db-apply:
	bash scripts/db_apply.sh

db-bootstrap: db-up db-apply

api:
	bash scripts/run_api.sh

fe:
	bash scripts/run_frontend.sh

test:
	PYTHONPATH=. .venv/bin/pytest -q

smoke:
	bash scripts/smoke_e2e.sh

verify: test smoke

dev:
	bash scripts/dev_all.sh
