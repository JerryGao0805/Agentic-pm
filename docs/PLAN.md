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

- [ ] Configure Next.js frontend for static export build output.
- [ ] Build frontend assets during container build/start process.
- [ ] Serve exported frontend static files from FastAPI at `/`.
- [ ] Preserve existing visual style and drag/drop behavior.

### Tests

- [ ] Frontend unit tests pass (`frontend` test command).
- [ ] Frontend e2e test suite passes against served app.
- [ ] Visiting `http://localhost:8000/` shows Kanban board with 5 columns.

### Success criteria

- [ ] No separate frontend dev server required for normal MVP run.
- [ ] Existing Kanban demo behavior works when served by FastAPI.

## Part 4: Dummy sign-in and logout

### Checklist

- [ ] Add login UI flow requiring credentials `user` / `password`.
- [ ] Add backend login/logout endpoints and session cookie handling.
- [ ] Block board access until session is authenticated.
- [ ] Add logout control and return user to login state.

### Tests

- [ ] Unit tests for login form validation and auth state transitions.
- [ ] Backend tests for login success/failure and logout behavior.
- [ ] E2E: unauthenticated user is redirected/shown login, authenticated user reaches board.

### Success criteria

- [ ] User cannot access board APIs without valid session cookie.
- [ ] Reload keeps user logged in until logout.

## Part 5: Database modeling

### Checklist

- [ ] Define MySQL schema for users, board JSON state, and chat history.
- [ ] Enforce one board per user for MVP while supporting multi-user rows.
- [ ] Add board JSON validation constraints aligned with fixed column IDs.
- [ ] Document schema and persistence decisions in `docs/`.
- [ ] Get user sign-off on schema doc before implementation-heavy steps continue.

### Tests

- [ ] Migration/init test creates DB and required tables when absent.
- [ ] Persistence test verifies board and chat rows save/load correctly.
- [ ] Validation test rejects malformed board structures.

### Success criteria

- [ ] Database is auto-created/initialized for local development.
- [ ] Board and chat data model can support future multi-user expansion.

## Part 6: Backend board APIs

### Checklist

- [ ] Implement authenticated API routes to read and write a user board.
- [ ] Add backend service/repository layer for board persistence.
- [ ] Ensure DB initialization is run at startup if database does not exist.
- [ ] Add request/response validation for board payload structure.

### Tests

- [ ] Unit tests for repository and service logic.
- [ ] API tests for auth-required access and normal success paths.
- [ ] API tests for invalid payload rejection.

### Success criteria

- [ ] Authenticated user can fetch and update board through backend only.
- [ ] Persistence survives app restarts.

## Part 7: Frontend/backend integration

### Checklist

- [ ] Replace frontend in-memory board source with backend API loading.
- [ ] Save board changes (rename/move/add/delete card) through backend API.
- [ ] Handle loading/error states with simple UI feedback.
- [ ] Keep drag/drop and editing UX responsive.

### Tests

- [ ] Frontend unit tests for API-backed board actions.
- [ ] Integration/e2e tests for persistence across page reloads.
- [ ] Manual test across login -> edits -> reload -> data retained.

### Success criteria

- [ ] Board is no longer frontend-only state.
- [ ] All core Kanban actions persist per signed-in user.

## Part 8: OpenAI connectivity

### Checklist

- [ ] Add backend OpenAI client using `OPENAI_API_KEY` from root `.env`.
- [ ] Implement simple test endpoint/service call using model `gpt-4o-mini`.
- [ ] Add guardrails for missing API key and upstream errors.

### Tests

- [ ] Mocked unit test for OpenAI client invocation.
- [ ] Manual connectivity check for a simple `2+2` prompt in local env.

### Success criteria

- [ ] Backend can successfully call OpenAI API with configured key.
- [ ] Clear error response when key/config is invalid.

## Part 9: AI board assistant backend

### Checklist

- [ ] Build AI endpoint that sends board JSON + chat history + user question.
- [ ] Define strict structured output schema: assistant message + optional full board JSON.
- [ ] Validate AI-returned board JSON against fixed-column rules.
- [ ] Persist assistant/user messages in chat history table.
- [ ] If AI board JSON is invalid, keep text response and skip board update.

### Tests

- [ ] Unit tests for prompt builder and response parser/validator.
- [ ] API tests for text-only response, valid board update, invalid board update.
- [ ] Persistence tests for chat history append behavior.

### Success criteria

- [ ] AI can return helpful text and optionally update board state.
- [ ] Invalid AI board data cannot corrupt persisted board.

## Part 10: Sidebar AI chat in UI

### Checklist

- [ ] Add sidebar chat UI with message history and input.
- [ ] Call backend AI endpoint from sidebar.
- [ ] Update frontend board state when backend returns updated board JSON.
- [ ] Keep chat and board behavior stable during loading/error states.

### Tests

- [ ] Unit tests for sidebar rendering, send flow, and error handling.
- [ ] Integration/e2e tests for end-to-end chat and board-update behavior.
- [ ] Manual test of AI-triggered board refresh without page reload.

### Success criteria

- [ ] User can chat with AI in sidebar while using Kanban board.
- [ ] AI-driven board updates appear automatically in the board UI.
