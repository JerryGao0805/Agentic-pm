# Project Plan

## Locked decisions

- App runtime: Docker Compose with two containers (`app`, `mysql`).
- App URL: `http://localhost:8000`.
- Scripts: Unix shell scripts only for start/stop.
- Auth: backend session via `HttpOnly` cookie.
- OpenAI model: `gpt-4o-mini`.
- AI board update contract: full board JSON (not operation list).
- Conversation history: persisted in MySQL.
- Column rules: strict fixed column IDs (titles can be renamed).
- Invalid AI board response: keep assistant text, reject board mutation.

## Part 1: Planning and repo docs

### Checklist

- [x] Expand this plan into implementation-ready checklists.
- [x] Add `frontend/AGENTS.md` describing the existing frontend app.
- [x] User reviews and approves this plan before implementation begins.

### Tests

- [ ] Manual review of `docs/PLAN.md` for completeness across parts 2-10.
- [ ] Manual review of `frontend/AGENTS.md` for accuracy against current frontend code.

### Success criteria

- [ ] Plan is explicit enough that another engineer can execute without major decisions.
- [ ] Frontend documentation reflects actual current files/components/tests.

## Part 2: Scaffolding (Docker + FastAPI + scripts)

### Checklist

- [x] Create backend FastAPI app scaffold under `backend/`.
- [x] Add Docker setup for `app` + `mysql` containers (Compose-based local run).
- [x] Use `uv` for Python dependency management in the app container.
- [x] Add Unix start/stop scripts in `scripts/` to run and stop the stack.
- [x] Serve simple static hello page at `/` from FastAPI.
- [x] Add simple API route (for example, `/api/health`) to verify API wiring.

### Tests

- [x] `./scripts/start.sh` starts both containers successfully.
- [x] `curl http://localhost:8000/` returns hello page.
- [x] `curl http://localhost:8000/api/health` returns healthy response.
- [x] `./scripts/stop.sh` cleanly stops containers.

### Success criteria

- [x] Fresh checkout can be started locally using only scripts and `.env`.
- [x] App container can connect to MySQL container.

## Part 3: Serve existing frontend from backend

### Checklist

- [x] Configure Next.js frontend for static export build output.
- [x] Build frontend assets during container build/start process.
- [x] Serve exported frontend static files from FastAPI at `/`.
- [x] Preserve existing visual style and drag/drop behavior.

### Tests

- [x] Frontend unit tests pass (`frontend` test command).
- [x] Frontend e2e test suite passes against served app.
- [x] Visiting `http://localhost:8000/` shows Kanban board with 5 columns.

### Success criteria

- [x] No separate frontend dev server required for normal MVP run.
- [x] Existing Kanban demo behavior works when served by FastAPI.

## Part 4: Dummy sign-in and logout

### Checklist

- [x] Add login UI flow requiring credentials `user` / `password`.
- [x] Add backend login/logout endpoints and session cookie handling.
- [x] Block board access until session is authenticated.
- [x] Add logout control and return user to login state.

### Tests

- [x] Unit tests for login form validation and auth state transitions.
- [x] Backend tests for login success/failure and logout behavior.
- [x] E2E: unauthenticated user is redirected/shown login, authenticated user reaches board.

### Success criteria

- [x] User cannot access board APIs without valid session cookie.
- [x] Reload keeps user logged in until logout.

## Part 5: Database modeling

### Checklist

- [x] Define MySQL schema for users, board JSON state, and chat history.
- [x] Enforce one board per user for MVP while supporting multi-user rows.
- [x] Add board JSON validation constraints aligned with fixed column IDs.
- [x] Document schema and persistence decisions in `docs/`.
- [ ] Get user sign-off on schema doc before implementation-heavy steps continue.

### Tests

- [x] Migration/init test creates DB and required tables when absent.
- [x] Persistence test verifies board and chat rows save/load correctly.
- [x] Validation test rejects malformed board structures.

### Success criteria

- [x] Database is auto-created/initialized for local development.
- [x] Board and chat data model can support future multi-user expansion.

## Part 6: Backend board APIs

### Checklist

- [x] Implement authenticated API routes to read and write a user board.
- [x] Add backend service/repository layer for board persistence.
- [x] Ensure DB initialization is run at startup if database does not exist.
- [x] Add request/response validation for board payload structure.

### Tests

- [x] Unit tests for repository and service logic.
- [x] API tests for auth-required access and normal success paths.
- [x] API tests for invalid payload rejection.

### Success criteria

- [x] Authenticated user can fetch and update board through backend only.
- [x] Persistence survives app restarts.

## Part 7: Frontend/backend integration

### Checklist

- [x] Replace frontend in-memory board source with backend API loading.
- [x] Save board changes (rename/move/add/delete card) through backend API.
- [x] Handle loading/error states with simple UI feedback.
- [x] Keep drag/drop and editing UX responsive.

### Tests

- [x] Frontend unit tests for API-backed board actions.
- [x] Integration/e2e tests for persistence across page reloads.
- [ ] Manual test across login -> edits -> reload -> data retained.

### Success criteria

- [x] Board is no longer frontend-only state.
- [x] All core Kanban actions persist per signed-in user.

## Part 8: OpenAI connectivity

### Checklist

- [x] Add backend OpenAI client using `OPENAI_API_KEY` from root `.env`.
- [x] Implement simple test endpoint/service call using model `gpt-4o-mini`.
- [x] Add guardrails for missing API key and upstream errors.

### Tests

- [x] Mocked unit test for OpenAI client invocation.
- [x] Manual connectivity check for a simple `2+2` prompt in local env.

### Success criteria

- [x] Backend can successfully call OpenAI API with configured key.
- [x] Clear error response when key/config is invalid.

## Part 9: AI board assistant backend

### Checklist

- [x] Build AI endpoint that sends board JSON + chat history + user question.
- [x] Define strict structured output schema: assistant message + optional full board JSON.
- [x] Validate AI-returned board JSON against fixed-column rules.
- [x] Persist assistant/user messages in chat history table.
- [x] If AI board JSON is invalid, keep text response and skip board update.

### Tests

- [x] Unit tests for prompt builder and response parser/validator.
- [x] API tests for text-only response, valid board update, invalid board update.
- [x] Persistence tests for chat history append behavior.

### Success criteria

- [x] AI can return helpful text and optionally update board state.
- [x] Invalid AI board data cannot corrupt persisted board.

## Part 10: Sidebar AI chat in UI

### Checklist

- [x] Add sidebar chat UI with message history and input.
- [x] Call backend AI endpoint from sidebar.
- [x] Update frontend board state when backend returns updated board JSON.
- [x] Keep chat and board behavior stable during loading/error states.

### Tests

- [x] Unit tests for sidebar rendering, send flow, and error handling.
- [x] Integration/e2e tests for end-to-end chat and board-update behavior.
- [x] Manual test of AI-triggered board refresh without page reload.

### Success criteria

- [x] User can chat with AI in sidebar while using Kanban board.
- [x] AI-driven board updates appear automatically in the board UI.
