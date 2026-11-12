SIDECAR_DIR := apps/desktop/src-tauri/binaries
TRIPLE := $(shell rustc -vV 2>/dev/null | sed -n 's/host: //p')

.PHONY: install test lint format samples eval backend desktop dev sidecar docker-up docker-down

install:
	uv sync --all-packages
	cd apps/desktop && pnpm install

test:
	uv run pytest
	cd apps/desktop && pnpm test

lint:
	uv run ruff check .
	uv run ruff format --check .
	cd apps/desktop && pnpm typecheck

format:
	uv run ruff check --fix .
	uv run ruff format .

samples:
	uv run python -c "from pathlib import Path; from cip_testkit import build_corpus; build_corpus(Path('samples'))"

eval:
	uv run cip-eval --output eval-report.md

backend:
	CIP_DATA_DIR=.data uv run cip-backend

desktop:
	cd apps/desktop && pnpm dev

dev:
	$(MAKE) -j2 backend desktop

sidecar:
	uv run --with pyinstaller pyinstaller --noconfirm --onefile --name cip-backend \
		--additional-hooks-dir deploy/pyinstaller services/sidecar/src/cip_sidecar/main.py
	mkdir -p $(SIDECAR_DIR)
	cp dist/cip-backend $(SIDECAR_DIR)/cip-backend-$(TRIPLE)

docker-up: samples
	docker compose up --build -d

docker-down:
	docker compose down
