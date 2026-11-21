.PHONY: install up down fixture local pipeline register test integration smoke clean
UV ?= $(if $(wildcard verified/tools/uv),verified/tools/uv,uv)
COMPOSE = docker compose --env-file config/images-arm64.env
export UV_OFFLINE = 1
export UV_PYTHON_DOWNLOADS = never
export PYTHONPATH = src
PY = .venv/bin/python
fetch:
	python3 scripts/fetch_artifacts.py
images:
	$(COMPOSE) pull --policy always
install:
	python3 -c "from codeatlas.verification import verify_directory; from pathlib import Path; verify_directory(Path('verified/wheels'), Path('security/wheels-macos-arm64-py312.sha256.json'))"
	$(UV) venv --python python3.12 --allow-existing .venv
	$(UV) export --locked --extra dev --no-emit-project --no-header --output-file verified/runtime.lock --quiet
	$(UV) pip sync --python $(PY) --no-index --find-links verified/wheels --only-binary :all: --require-hashes verified/runtime.lock
up:
	python3 -c 'from codeatlas.verification import verify_jar; verify_jar()'
	$(COMPOSE) up -d --pull never
down:
	$(COMPOSE) down
fixture:
	python3 scripts/init_fixture.py
local: fixture
	@mkdir -p data
	@$(PY) -m codeatlas.cli ingest .fixture-repo --output data > data/latest-input
	@$(PY) -m codeatlas.cli extract "$$(cat data/latest-input)"
	@$(PY) -m codeatlas.cli acl
pipeline: local
	$(PY) scripts/wait_ready.py
	$(PY) -m codeatlas.cli upload
register:
	$(PY) scripts/register.py "$$(cat data/latest-input)"
test:
	$(PY) -m pytest -q
integration:
	$(PY) -m pytest -q -m integration
smoke: pipeline
	$(MAKE) register
	$(PY) scripts/smoke.py
clean:
	rm -rf data .fixture-repo
