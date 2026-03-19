# Project Management MVP Tutorial (Beginner Friendly)

This tutorial explains what was built in this repository, why it was built this way, and how the pieces work together.

If you are new to coding, do not worry. I will define terms as we go and keep the examples concrete.

## 1. What You Built

You now have a local web app with these features:

- Sign in with a fixed username and password (`user` / `password`)
- Use a Kanban board with fixed workflow columns
- Rename columns, add/delete cards, and drag cards between columns
- Persist board data in MySQL
- Chat with an AI assistant in a sidebar
- Let AI optionally update the board automatically
- Keep chat history persisted in MySQL

You also have:

- Dockerized runtime (one command start/stop)
- Backend + frontend integration through APIs
- Unit tests and end-to-end tests

## 2. Technology Summary

Here is the stack, in plain language:

- `Docker Compose`: starts two containers together: app + database
- `MySQL 8.4`: stores users, board JSON, and chat messages
- `FastAPI` (Python): backend API and static file server
- `Next.js + React + TypeScript`: frontend user interface
- `OpenAI API` (`gpt-4o-mini`): AI responses for chat + board updates
- `Vitest + Testing Library`: frontend unit tests
- `Playwright`: browser end-to-end tests
- `pytest`: backend tests

## 3. High-Level Walkthrough (Parts 1 to 10)

The project was implemented in clear stages:

1. Planning docs were created and agreed.
2. Docker + backend scaffold were added.
3. Existing frontend was served through backend.
4. Dummy login/logout was implemented with session cookie auth.
5. Database schema for users/boards/chat was added.
6. Board read/write backend APIs were built.
7. Frontend was connected to backend board APIs.
8. OpenAI connectivity was added (`/api/ai/test`).
9. AI board assistant backend was built (`/api/ai/chat`).
10. Sidebar AI chat UI was added and connected end-to-end.

The current plan status is tracked in `docs/PLAN.md` and Part 10 is now complete.

## 4. How To Run The App

From project root:

```bash
./scripts/start.sh
```

This runs `docker compose up --build -d` and starts:

- `pm-mysql` on port `3307` (host side)
- `pm-app` on port `8000`

Then open:

- App: `http://localhost:8000`
- Health check: `http://localhost:8000/api/health`

To stop:

```bash
./scripts/stop.sh
```

## 5. Architecture at a Glance

```text
Browser (Next.js UI)
   |
   | HTTP fetch (/api/auth, /api/board, /api/ai/chat, /api/ai/chat/history)
   v
FastAPI backend (main.py)
   |\
   | \--> BoardService -> BoardRepository -> MySQL
   | \--> ChatService  -> ChatRepository  -> MySQL
   | \--> AIAssistantService -> OpenAIService -> OpenAI API
   |
   +--> Serves static frontend build at /
```

## 6. Detailed Code Review

This section is the "deep dive".

### 6.1 Configuration and Environment (`backend/app/config.py`)

The backend centralizes env vars into one immutable settings object:

```python
@dataclass(frozen=True)
class Settings:
    db_host: str = os.getenv("DB_HOST", "mysql")
    db_port: int = _int_env("DB_PORT", 3306)
    auth_username: str = os.getenv("AUTH_USERNAME", "user")
    auth_password: str = os.getenv("AUTH_PASSWORD", "password")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
```

Why this matters for beginners:

- You avoid hardcoding secrets in code.
- You can change behavior by editing `.env`.
- One source of truth prevents config drift.

### 6.2 Database Initialization (`backend/app/db.py`)

On app startup, database and tables are created if missing.

Key idea: bootstrapping should be automatic for local development.

```python
def initialize_database() -> None:
    _create_database_if_missing()
    # create users, boards, chat_messages tables
    # ensure default user exists
    # ensure default board exists for that user
```

The `boards` table keeps one row per user (`user_id` is primary key), and board data is stored as JSON.

The `chat_messages` table stores ordered conversation messages (`user` or `assistant`).

### 6.3 Board Validation Rules (`backend/app/kanban.py`)

`BoardPayload` is a Pydantic model that enforces strict board consistency.

Important rule sample:

```python
if unique_column_ids != set(FIXED_COLUMN_IDS):
    raise ValueError("Board must include exactly the fixed column IDs...")
```

Other checks include:

- no duplicate card IDs across columns
- all referenced cards must exist in `cards`
- every card must appear in exactly one column
- card map key must equal card object `id`

This is critical because AI can suggest board changes. Validation protects data integrity.

### 6.4 Repository Layer (DB Access)

`BoardRepository` and `ChatRepository` are the only classes that talk directly to MySQL.

Example board save:

```python
cursor.execute(
    """
    INSERT INTO boards (user_id, board_json)
    VALUES (%s, CAST(%s AS JSON))
    ON DUPLICATE KEY UPDATE board_json = CAST(%s AS JSON)
    """,
    (user_id, serialized_board, serialized_board),
)
```

Why this is good:

- API layer does not need SQL knowledge.
- Easier testing (you can fake repositories/services).

### 6.5 Service Layer (Business Logic)

`BoardService` validates incoming/outgoing board payloads.

`ChatService` trims and rejects empty messages.

```python
def append_message(self, username: str, role: ChatRole, content: str) -> None:
    normalized_content = content.strip()
    if not normalized_content:
        raise ValueError("Chat message cannot be empty.")
    self._repository.append_message(username, role, normalized_content)
```

For beginners: this pattern keeps controllers thin and makes logic reusable.

### 6.6 OpenAI Wrapper (`backend/app/services/openai_service.py`)

`OpenAIService` hides SDK details and normalizes errors.

```python
response = client.responses.create(
    model=self._model,
    input=prompt_text,
)
```

Custom exceptions:

- `OpenAIConfigError`: missing API key
- `OpenAIUpstreamError`: network/API failures or empty output

This lets API endpoints return clean HTTP statuses (`503` / `502`).

### 6.7 AI Assistant Orchestration (`backend/app/services/ai_assistant_service.py`)

This service builds a strict prompt and parses strict JSON output.

Prompt requirement summary:

- AI must return JSON only
- JSON keys must be exactly `assistant_message` and `board`
- `board` must be full board object or `null`
- fixed column IDs must remain

Output schema:

```python
class AIAssistantOutput(BaseModel):
    assistant_message: str = Field(min_length=1)
    board: dict[str, Any] | None = None
```

If AI returns malformed JSON or wrong schema, it raises `AIAssistantFormatError`.

### 6.8 API Layer (`backend/app/main.py`)

This is the central entry point.

Main endpoint groups:

- Auth:
  - `GET /api/auth/session`
  - `POST /api/auth/login`
  - `POST /api/auth/logout`
- Board:
  - `GET /api/board`
  - `PUT /api/board`
- AI:
  - `POST /api/ai/test`
  - `POST /api/ai/chat`
  - `GET /api/ai/chat/history`

Auth uses an `HttpOnly` cookie:

```python
response.set_cookie(
    key=settings.auth_cookie_name,
    value=settings.auth_username,
    httponly=True,
    samesite="lax",
)
```

AI chat flow in one sentence:

1. Require auth
2. Save user message
3. Ask AI with board + history
4. Validate optional board update
5. Save assistant message
6. Return assistant text, board status, and full chat history

### 6.9 Frontend Auth Gate (`frontend/src/components/AuthGate.tsx`)

This component controls access to the board UI.

It first checks `/api/auth/session`, then renders:

- loading screen
- sign-in form
- board screen (when authenticated)

It supports a local fallback mode (non-production) using localStorage when backend APIs are unavailable.

### 6.10 Frontend Board (`frontend/src/components/KanbanBoard.tsx`)

Responsibilities:

- load board from `/api/board`
- persist edits to `/api/board`
- manage drag and drop using `@dnd-kit`
- host the AI sidebar

Important integration point:

```tsx
<AISidebarChat board={board} onBoardUpdate={handleAIBoardUpdate} />
```

`handleAIBoardUpdate` applies AI-returned board state immediately in UI, and optionally persists if in local mode.

### 6.11 Sidebar AI Chat (`frontend/src/components/AISidebarChat.tsx`)

This is the Part 10 feature.

What it does:

- loads history from `/api/ai/chat/history`
- sends messages to `/api/ai/chat`
- renders user + assistant bubbles
- handles loading, API errors, board-update warnings
- updates board state using callback from `KanbanBoard`

Send flow core:

```tsx
const response = await fetch("/api/ai/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  credentials: "include",
  body: JSON.stringify({ message: trimmedMessage }),
});
```

If backend returns `board_updated: true`, it calls:

```tsx
onBoardUpdate(payload.board, { persist: false });
```

Local fallback behavior:

- if API endpoint is missing or network fails in dev mode, chat switches to local mode
- local mode supports simple rename commands like: `Rename backlog to Intake`

### 6.12 Shared Board Logic (`frontend/src/lib/kanban.ts`)

This file defines:

- board/card/column types
- initial seed board
- `moveCard` algorithm used by drag-drop
- `createId` helper for new cards

Why this matters:

- shared pure logic is easier to test and reason about
- UI components stay focused on rendering/events

## 7. End-to-End User Story Example

Let’s trace this real action:

User types in chat: `Rename backlog to Intake`

1. Frontend `AISidebarChat` sends POST `/api/ai/chat`.
2. Backend validates auth from cookie.
3. Backend loads current board + chat history from MySQL.
4. Backend appends user message to `chat_messages`.
5. Backend asks OpenAI for structured response.
6. If AI returns a valid full board, backend validates it with `BoardPayload`.
7. If valid, backend saves board JSON in `boards`.
8. Backend stores assistant message in `chat_messages`.
9. Backend returns updated board + chat history.
10. Frontend updates board state immediately, no page reload required.

## 8. Testing Strategy

### Backend tests (`pytest`)

Coverage includes:

- auth endpoint behavior
- board API auth + validation
- db initialization and schema creation
- OpenAI wrapper behavior
- AI prompt + parser behavior
- AI chat API success/error cases
- chat repository persistence behavior

### Frontend unit tests (`Vitest`)

Coverage includes:

- auth gate behavior
- board basic operations
- sidebar chat history rendering
- sidebar send flow and board update callback
- sidebar error rendering

### Frontend e2e tests (`Playwright`)

Coverage includes browser scenarios:

- login required
- card add/persist/move
- logout
- AI chat updates board without page reload

## 9. Why This Design Is Strong for an MVP

- It is simple and layered (API -> service -> repository).
- It enforces data integrity before persistence.
- It degrades gracefully in local dev (fallback modes).
- It keeps user-visible behavior responsive.
- It has good baseline automated test coverage.

## 10. Self-Review: Improvement Suggestions (with estimated impact %)

Below are practical next improvements, each with an estimated impact on reliability, usability, or maintainability.

1. Add optimistic update rollback for board saves. Estimated impact: `18%` reliability.
2. Add server-side rate limiting on AI chat endpoint. Estimated impact: `12%` abuse protection.
3. Add structured logging (request id, endpoint, user, error class). Estimated impact: `14%` operability.
4. Add migration tool (Alembic or similar) instead of startup SQL only. Estimated impact: `16%` long-term maintainability.
5. Replace local fallback AI parser with shared command parser module + tests. Estimated impact: `8%` behavior consistency.
6. Add pagination/windowing for long chat histories. Estimated impact: `7%` performance.
7. Add stronger typing for API contracts shared between frontend and backend (schema generation). Estimated impact: `9%` correctness.
8. Add integration test that runs against real MySQL + app startup lifecycle in CI. Estimated impact: `10%` release confidence.
9. Add multi-user session model (real user table auth, hashed passwords). Estimated impact: `22%` product readiness.
10. Add UI accessibility audit (keyboard, focus order, ARIA announcements). Estimated impact: `11%` UX quality.

If you want, the next tutorial can be "Part 11" and we can implement 1 to 3 of these improvements step-by-step.
