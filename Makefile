VENV := .venv/bin

.PHONY: dev dev-backend dev-frontend dev-site install install-backend install-frontend stop build-site

dev:  ## Run both backend and frontend in parallel (Ctrl+C kills both)
	trap 'kill 0' INT TERM; \
	$(MAKE) dev-backend & \
	$(MAKE) dev-frontend & \
	wait

dev-backend:  ## Run FastAPI backend
	cd backend && $(CURDIR)/$(VENV)/uvicorn dodar.main:app --reload --host 0.0.0.0 --port 8001

dev-frontend:  ## Run Vite frontend
	cd frontend && npm run dev

dev-site:  ## Run static site dev server
	cd site && npm run dev -- --port 5174

stop:  ## Kill any lingering dev servers
	-pkill -f "uvicorn dodar.main:app" 2>/dev/null
	-pkill -f "vite" 2>/dev/null

install: install-backend install-frontend  ## Install all dependencies

install-backend:  ## Create venv and install Python backend dependencies
	python3 -m venv .venv && .venv/bin/pip install -e "backend/[dev]" build twine

install-frontend:  ## Install frontend dependencies
	cd frontend && npm install

build-site:  ## Build static site for deployment
	cd site && npm run build

publish-sdk:  ## Build and publish SDK to PyPI
	cd sdk && $(CURDIR)/$(VENV)/python -m build && $(CURDIR)/$(VENV)/python -m twine upload dist/*
