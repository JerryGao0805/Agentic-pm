# Code Review Report

Comprehensive review of the entire repository. Each finding includes severity, location, and a recommended action.

## Summary

| Severity | Backend | Frontend | Infra | Total |
|----------|---------|----------|-------|-------|
| Critical | 1       | 1        | 2     | 4     |
| High     | 5       | 3        | 3     | 11    |
| Medium   | 16      | 12       | 6     | 34    |
| Low      | 10      | 14       | 6     | 30    |

---

## Critical

### C1. Auth cookie is trivially forgeable
- **File:** `backend/app/main.py:78,127-134`
- **Area:** Backend / Security
- The session cookie value is the plaintext username. Anyone who knows the username can forge it without logging in. No signing, no HMAC, no random session token.
- **Action:** Replace with a cryptographically signed session token (e.g., `itsdangerous.URLSafeTimedSerializer` or FastAPI session middleware with a secret key).

### C2. Hardcoded credentials in client JavaScript bundle
- **File:** `frontend/src/components/AuthGate.tsx:7-8`
- **Area:** Frontend / Security
- `AUTH_USERNAME = "user"` and `AUTH_PASSWORD = "password"` are defined at module scope and ship in the production JS bundle regardless of whether the local fallback is used.
- **Action:** Remove hardcoded credentials from client code. If needed for dev fallback, gate behind `process.env.NODE_ENV !== "production"` or move to a dev-only env variable.

### C3. Database passwords committed in docker-compose.yml
- **File:** `docker-compose.yml:7,10,35`
- **Area:** Infra / Security
- `MYSQL_ROOT_PASSWORD`, `MYSQL_PASSWORD`, and `DB_PASSWORD` are trivially guessable and committed to version control.
- **Action:** Move all secrets to `.env` and reference via `${VARIABLE}` interpolation. Use strong, randomly generated passwords. Create a `.env.example` with placeholders.

### C4. OpenAI API key in plaintext `.env` with no `.env.example`
- **File:** `.env:1`
- **Area:** Infra / Security
- A real `sk-proj-...` key is present on disk. While `.env` is gitignored, there is no `.env.example` to document required variables for new developers.
- **Action:** Rotate the key in the OpenAI dashboard. Create `.env.example` with placeholder values.

---

## High

### H1. No database connection pooling
- **File:** `backend/app/db.py:13-27`
- **Area:** Backend / Performance
- Every request creates a new TCP connection to MySQL. Under load this will exhaust `max_connections` and add significant latency.
- **Action:** Use `mysql.connector.pooling.MySQLConnectionPool` or switch to an async driver with pooling.

### H2. User message persisted to chat before AI call -- corrupts history on failure
- **File:** `backend/app/main.py:193`
- **Area:** Backend / Error Handling
- `chat_service.append_message()` is called before `ai_assistant_service.generate_reply()`. If the AI call fails, the user message is saved but no assistant response exists, creating a dangling turn. On retry the message appears twice.
- **Action:** Defer persisting the user message until after a successful AI response, or delete it on failure.

### H3. Unbounded chat history sent to OpenAI
- **File:** `backend/app/repositories/chat_repository.py:21-29`, `backend/app/main.py:195`
- **Area:** Backend / Performance + Cost
- `list_messages` has no `LIMIT`. All history is fetched and sent to the OpenAI API, which could exceed token limits and cause high costs.
- **Action:** Add a `LIMIT` clause (e.g., last 50 messages) and truncate history before sending to AI.

### H4. `get_board` race condition on initial board creation
- **File:** `backend/app/repositories/board_repository.py:27`
- **Area:** Backend / Database
- `get_board` uses a plain `INSERT` for the default board without `ON DUPLICATE KEY`. Two concurrent requests for a new user can hit a duplicate key error.
- **Action:** Add `ON DUPLICATE KEY UPDATE` or `INSERT IGNORE` for the default board creation.

### H5. No tests for database error scenarios in API endpoints
- **Area:** Backend / Test Coverage
- All tests use fake services that never raise DB errors. No test verifies that a MySQL failure returns a clean HTTP error instead of a raw 500.
- **Action:** Add tests with fake services that raise `mysql.connector.Error`.

### H6. Undefined cards crash when card ID in column but missing from cards map
- **File:** `frontend/src/components/KanbanBoard.tsx:331`
- **Area:** Frontend / Reliability
- `column.cardIds.map((cardId) => board.cards[cardId])` produces `undefined` if a cardId is missing from the map. This is passed as `card` prop to `KanbanCard`, which crashes on `card.id`.
- **Action:** Add `.filter(Boolean)` or validate board data on load.

### H7. Drag-and-drop not keyboard accessible
- **File:** `frontend/src/components/KanbanBoard.tsx:159-163`
- **Area:** Frontend / Accessibility
- Only `PointerSensor` is configured. Keyboard-only users cannot drag cards.
- **Action:** Add `KeyboardSensor` from `@dnd-kit/core` to the `useSensors` call.

### H8. Credential hint displayed on login page
- **File:** `frontend/src/components/AuthGate.tsx:168`
- **Area:** Frontend / Security
- The login form renders "Use credentials: user / password" as visible text.
- **Action:** Remove or hide behind an environment flag for non-demo deployments.

### H9. Container runs as root
- **File:** `backend/Dockerfile`
- **Area:** Infra / Security
- The application runs as `root` inside the container.
- **Action:** Add a non-root user: `RUN addgroup --system app && adduser --system --ingroup app app` then `USER app`.

### H10. No health check on app container
- **File:** `docker-compose.yml:21-39`
- **Area:** Infra / Reliability
- MySQL has a health check but the app service does not. Docker cannot determine if the app is actually healthy.
- **Action:** Add a health check hitting `/api/health`.

### H11. MySQL port exposed to host
- **File:** `docker-compose.yml:11-12`
- **Area:** Infra / Security
- Port `3307:3306` exposes MySQL to the host network with weak passwords.
- **Action:** Remove the `ports` mapping or restrict to `127.0.0.1:3307:3306`.

---

## Medium

### M1. Cookie missing `secure=True` flag
- **File:** `backend/app/main.py:127`
- **Action:** Add `secure=True` for production deployments (configurable for dev).

### M2. No CORS configuration
- **File:** `backend/app/main.py`
- **Action:** Add explicit `CORSMiddleware` with a restrictive allow-list.

### M3. No rate limiting on login endpoint
- **File:** `backend/app/main.py:116`
- **Action:** Add rate limiting (e.g., `slowapi`) or lockout mechanism.

### M4. No input length limit on board payload
- **File:** `backend/app/kanban.py`
- Card title, details, and card count have no max limits. An authenticated user could submit a massive board.
- **Action:** Add `max_length` on string fields and a validator limiting card count.

### M5. Database errors in repositories propagate as raw 500s
- **Files:** `backend/app/repositories/board_repository.py`, `chat_repository.py`
- **Action:** Add a FastAPI exception handler that maps DB errors to sanitized 503 responses.

### M6. `initialize_database()` failure silently swallowed at startup
- **File:** `backend/app/main.py:29-36`
- App starts but all endpoints fail with raw errors.
- **Action:** Fail fast on startup, or add middleware returning 503 when `startup_db_error` is set.

### M7. Duplicate `ChatRole` type alias in two modules
- **Files:** `backend/app/repositories/chat_repository.py:8`, `backend/app/services/chat_service.py:7`
- **Action:** Define once in a shared module and import.

### M8. Module-level singleton services instead of FastAPI `Depends()`
- **File:** `backend/app/main.py:40-43`
- Makes testing harder; requires monkeypatching globals.
- **Action:** Refactor to use FastAPI dependency injection.

### M9. Settings resolved at import time via `os.getenv`
- **File:** `backend/app/config.py:16-33`
- **Action:** Consider using Pydantic `BaseSettings` for validation and test overrides.

### M10. No pagination on chat history endpoint
- **File:** `backend/app/main.py:242`
- **Action:** Add `limit` and `offset` query parameters.

### M11. `GET /api/board` double-validates response
- **File:** `backend/app/main.py:144-147`
- If DB contains corrupted data that fails re-validation, user gets a 500 instead of a meaningful error.
- **Action:** Catch `ValidationError` and return a clear error message.

### M12. Health endpoint leaks internal DB host/port/name
- **File:** `backend/app/main.py:91-104`
- Unauthenticated endpoint exposes infrastructure details.
- **Action:** Limit public health response to `status: ok/degraded`.

### M13. Hardcoded default credentials in backend config
- **File:** `backend/app/config.py:20-27`
- **Action:** Require env vars or log a warning when defaults are used.

### M14. No CSRF protection on API mutations
- **Files:** `frontend/src/components/AuthGate.tsx:111`, `KanbanBoard.tsx:125`, `AISidebarChat.tsx:295`
- POST/PUT requests use `credentials: "include"` but send no CSRF token.
- **Action:** Implement CSRF tokens.

### M15. Unsafe `as string` cast on dnd-kit IDs
- **File:** `frontend/src/components/KanbanBoard.tsx:168,182-184`
- **Action:** Use `String(event.active.id)` instead.

### M16. Side effect inside `setBoard` state updater
- **File:** `frontend/src/components/KanbanBoard.tsx:146-154`
- `persistBoard` is called inside the state updater, which should be pure.
- **Action:** Separate the state update from the persist call.

### M17. `handleLogout` does not handle fetch failure
- **File:** `frontend/src/components/AuthGate.tsx:132-145`
- **Action:** Wrap in try/catch.

### M18. Unsafe `JSON.parse` with `as SomeType` in multiple places
- **Files:** `KanbanBoard.tsx:26,39,85`, `AISidebarChat.tsx:36,321`
- No runtime validation on parsed data.
- **Action:** Add Zod schemas or manual runtime checks.

### M19. Column rename fires API call on every keystroke
- **File:** `frontend/src/components/KanbanColumn.tsx:44`
- **Action:** Debounce the persist call, or use `onBlur` to trigger persistence.

### M20. Accessibility: column title inputs all share same aria-label
- **File:** `frontend/src/components/KanbanColumn.tsx:46`
- **Action:** Use dynamic label: `aria-label={`${column.title} column title`}`.

### M21. Accessibility: NewCardForm inputs lack labels
- **File:** `frontend/src/components/NewCardForm.tsx:27-43`
- **Action:** Add `aria-label` attributes.

### M22. No unit tests for `KanbanCard`, `KanbanCardPreview`, `KanbanColumn`, `NewCardForm`
- **Action:** Add focused unit tests for these components.

### M23. No tests for local fallback mode
- localStorage-based paths in `AISidebarChat`, `AuthGate`, and `KanbanBoard` are untested.
- **Action:** Add tests simulating 404 responses.

### M24. Responsive layout: columns stack vertically on small screens
- **File:** `frontend/src/components/KanbanBoard.tsx:326`
- **Action:** Add horizontal scrolling for columns on smaller screens.

### M25. AI sidebar off-screen on narrow viewports
- **File:** `frontend/src/components/KanbanBoard.tsx:319`
- **Action:** Consider a collapsible sidebar or floating chat button.

### M26. No `uv.lock` committed -- builds are not reproducible
- **File:** `backend/Dockerfile:24-25`
- `uv sync` without a lock file means dependency versions drift between builds.
- **Action:** Generate `uv.lock`, commit it, and use `uv sync --frozen`.

### M27. Dockerfile CMD uses `uv run` unnecessarily
- **File:** `backend/Dockerfile:35`
- `.venv/bin` is already on `PATH`.
- **Action:** Change CMD to `["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]`.

### M28. `.dockerignore` is too minimal
- **File:** `.dockerignore`
- Missing exclusions for `scripts/`, `*.md`, `backend/.venv/`, `backend/__pycache__/`.
- **Action:** Add comprehensive exclusions.

### M29. `localStorage` auth state trivially spoofable
- **File:** `frontend/src/components/AuthGate.tsx:20-25`
- Acceptable for dev-only fallback, but add a comment documenting the risk.

### M30. `readLocalBoard` uses unsafe `JSON.parse` without validation
- **File:** `frontend/src/components/KanbanBoard.tsx:39`
- Corrupted localStorage data will crash downstream code.
- **Action:** Add runtime validation.

---

## Low

### L1. `_decode_board_json` error message lacks context
- **File:** `backend/app/repositories/board_repository.py:74`
- **Action:** Include the actual type in the error message.

### L2. `conftest.py` and `test_auth.py` duplicate `sys.path` manipulation
- **Action:** Remove the duplicate from `test_auth.py`.

### L3. `probe_mysql` could use `autocommit=True`
- **File:** `backend/app/db.py:150-165`
- **Action:** Minor cleanup.

### L4. No database migration strategy
- **File:** `backend/app/db.py:86-147`
- **Action:** Adopt Alembic for future schema changes.

### L5. No OpenAPI tags on endpoints
- **Action:** Add `tags=["auth"]`, `tags=["board"]`, `tags=["ai"]`.

### L6. Logout does not require authentication
- **File:** `backend/app/main.py:138-141`
- **Action:** Accept as by-design or add auth check.

### L7. Uvicorn runs with single worker
- **File:** `backend/Dockerfile:35`
- Sync endpoints block the event loop.
- **Action:** Add `--workers N` or convert to async endpoints.

### L8. `test_ai_api.py` defines `value_error` mode but no test uses it
- **Action:** Add a test for the `ValueError` -> 422 path.

### L9. No tests for `/api/health` endpoint
- **Action:** Add tests for healthy and degraded states.

### L10. No tests for `_resolve_frontend_dist_dir` / fallback HTML
- **Action:** Add tests for frontend fallback behavior.

### L11. Chat messages keyed by index
- **File:** `frontend/src/components/AISidebarChat.tsx:375`
- **Action:** Acceptable for append-only; add unique IDs if editing is added.

### L12. No `useCallback` on handlers passed to child components
- **File:** `frontend/src/components/KanbanBoard.tsx:189,198,214`
- **Action:** Wrap with `useCallback` or memoize children.

### L13. No retry button for failed board load
- **File:** `frontend/src/components/KanbanBoard.tsx:256-263`
- **Action:** Add a "Retry" button.

### L14. No retry button for failed chat history load
- **File:** `frontend/src/components/AISidebarChat.tsx:410-413`
- **Action:** Add a retry button.

### L15. Chat textarea does not support Enter-to-send
- **File:** `frontend/src/components/AISidebarChat.tsx:401-408`
- **Action:** Add `onKeyDown` handler for Enter key.

### L16. No confirmation dialog for card deletion
- **File:** `frontend/src/components/KanbanCard.tsx:44`
- **Action:** Add confirmation or undo.

### L17. "Signed in as" shows hardcoded username instead of session username
- **File:** `frontend/src/components/AuthGate.tsx:225`
- **Action:** Display actual username from the API response.

### L18. Hardcoded hex colors mixed with CSS variables
- Error/warning colors use raw hex while theme colors use variables.
- **Action:** Add `--error` and `--warning` CSS variables in `globals.css`.

### L19. `createId` uses `Math.random()` -- predictable IDs
- **File:** `frontend/src/lib/kanban.ts:165`
- **Action:** Acceptable for card IDs. Consider `crypto.randomUUID()` if needed.

### L20. Chat auto-scroll missing
- **File:** `frontend/src/components/AISidebarChat.tsx:360`
- **Action:** Add a `useEffect` with ref to scroll to bottom on new messages.

### L21. `scripts/start.sh` always rebuilds
- **Action:** Make `--build` optional via a flag.

### L22. Playwright tests only target Chromium
- **File:** `frontend/playwright.config.ts`
- **Action:** Add Firefox/WebKit if cross-browser coverage desired.

### L23. `pyproject.toml` uses loose version bounds without lock file
- **Action:** Acceptable if `uv.lock` is committed (see M26).

### L24. Confusing Dockerfile env vars: `PYTHONDONTWRITEBYTECODE` + `UV_COMPILE_BYTECODE`
- **Action:** Add a comment explaining the intent.

---

## Recommended priority order

1. **Rotate the OpenAI API key** (C4) -- immediate
2. **Move secrets out of docker-compose.yml** (C3) -- immediate
3. **Sign the auth cookie** (C1) -- before any non-local deployment
4. **Remove hardcoded credentials from JS bundle** (C2) -- before any non-local deployment
5. **Add connection pooling** (H1) -- before any load testing
6. **Fix chat history persistence on AI failure** (H2) -- data integrity
7. **Add board data guard against undefined cards** (H6) -- crash prevention
8. **Add keyboard accessibility to drag-and-drop** (H7) -- accessibility compliance
9. **Run container as non-root** (H9) -- security hardening
10. **Add app container health check** (H10) -- operational reliability
