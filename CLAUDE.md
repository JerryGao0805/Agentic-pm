# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Project Management MVP: Kanban board web app with AI chat sidebar. Single-user MVP (hardcoded `user`/`password` login), one board per user, MySQL-backed persistence, OpenAI-powered assistant that can read and modify the board.

## Commands

### Run the full app (Docker)
```bash
./scripts/start.sh    # builds and starts app + mysql containers
./scripts/stop.sh     # stops containers
# App at http://localhost:8000
```

### Frontend development (standalone, no backend)
```bash
cd frontend
npm install
npm run dev            # Next.js dev server at http://127.0.0.1:3000
npm run build          # static export to frontend/out/
```

### Frontend tests
```bash
cd frontend
npm run test:unit      # vitest
npm run test:e2e       # playwright (needs dev server at :3000)
npm run test:all       # both
```

### Backend tests
```bash
cd backend
uv run pytest          # all backend tests
uv run pytest tests/test_board_api.py           # single file
uv run pytest tests/test_board_api.py -k "test_name"  # single test
```

### Frontend lint
```bash
cd frontend
npm run lint           # eslint
```

## Architecture

**Two-service Docker Compose stack**: `app` (FastAPI serving static frontend + API) and `mysql` (MySQL 8.4). The backend builds the frontend static export during Docker build and serves it at `/`.

### Backend (`backend/`)
- **FastAPI app** (`app/main.py`): all API routes defined here (auth, board CRUD, AI chat). No router splitting.
- **Config** (`app/config.py`): env-backed settings (DB, auth, OpenAI key/model).
- **DB** (`app/db.py`): raw MySQL connector (not an ORM). Auto-creates database/tables/seed data on startup.
- **Board validation** (`app/kanban.py`): Pydantic models enforcing fixed column IDs (`col-backlog`, `col-discovery`, `col-progress`, `col-review`, `col-done`). Titles are editable, IDs are not.
- **Repository layer** (`app/repositories/`): board and chat persistence (direct SQL).
- **Service layer** (`app/services/`): board validation+save orchestration, chat message handling, OpenAI client wrapper, AI assistant prompt builder + JSON response parser.
- **Python deps**: managed with `uv` (see `pyproject.toml`).

### Frontend (`frontend/`)
- **Next.js App Router** with static export (`src/app/`).
- **Components** in `src/components/`: `AuthGate` (login gate) -> `KanbanBoard` (board + drag-drop via `@dnd-kit`) -> columns/cards. `AISidebarChat` for AI interaction.
- **Board logic** in `src/lib/kanban.ts`: types, seed data, move helpers.
- Has a **localStorage fallback mode** when backend is unavailable (for standalone `next dev`).

### Data flow
- Board state is a single JSON document stored in MySQL `boards` table (one row per user).
- AI chat sends full board JSON + chat history to OpenAI. Response includes assistant text + optional full replacement board JSON. Invalid AI board mutations are rejected silently (text still shown).
- Chat history persisted in MySQL `chat_messages` table.

## Key conventions

- No emojis in code or docs.
- Keep `data-testid` patterns stable (`column-*`, `card-*`) unless tests are updated.
- Board JSON must always contain exactly the 5 fixed column IDs. Payloads violating this are rejected.
- `OPENAI_API_KEY` lives in root `.env`. Model is `gpt-4o-mini`.
- MySQL exposed on host port 3307 (maps to container 3306).
- Planning docs live in `docs/`. Review `docs/PLAN.md` for implementation context.
