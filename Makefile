VENV := backend/.venv/bin

.PHONY: dev dev-backend dev-frontend install install-backend install-frontend stop

dev:  ## Run both backend and frontend in parallel (Ctrl+C kills both)
	trap 'kill 0' INT TERM; \
	$(MAKE) dev-backend & \
	$(MAKE) dev-frontend & \
	wait

dev-backend:  ## Run FastAPI backend
	cd backend && $(CURDIR)/$(VENV)/uvicorn dodar.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:  ## Run Vite frontend
	cd frontend && npm run dev

stop:  ## Kill any lingering dev servers
	-pkill -f "uvicorn dodar.main:app" 2>/dev/null
	-pkill -f "vite" 2>/dev/null

install: install-backend install-frontend  ## Install all dependencies

install-backend:  ## Create venv and install Python backend dependencies
	cd backend && python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"

install-frontend:  ## Install frontend dependencies
	cd frontend && npm install
