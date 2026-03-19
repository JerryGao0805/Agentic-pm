import time
from collections import defaultdict
from typing import Literal
from contextlib import asynccontextmanager
from pathlib import Path

import mysql.connector
from fastapi import FastAPI, HTTPException, Query, Request, Response, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ValidationError
from starlette.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import initialize_database, probe_mysql
from app.kanban import BoardPayload
from app.services.board_service import BoardService
from app.services.chat_service import ChatService
from app.services.ai_assistant_service import (
    AIAssistantFormatError,
    AIAssistantService,
)
from app.services.openai_service import (
    OpenAIConfigError,
    OpenAIService,
    OpenAIUpstreamError,
)

startup_db_error: str | None = None

# M3: Simple in-memory rate limiter for login endpoint
_login_attempts: dict[str, list[float]] = defaultdict(list)
_LOGIN_RATE_LIMIT = 10
_LOGIN_RATE_WINDOW = 60  # seconds


def _check_login_rate_limit(client_ip: str) -> None:
    now = time.time()
    attempts = _login_attempts[client_ip]
    # Prune old entries
    _login_attempts[client_ip] = [t for t in attempts if now - t < _LOGIN_RATE_WINDOW]
    if len(_login_attempts[client_ip]) >= _LOGIN_RATE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )
    _login_attempts[client_ip].append(now)


@asynccontextmanager
async def lifespan(_: FastAPI):
    global startup_db_error
    try:
        initialize_database()
        startup_db_error = None
    except Exception as error:
        startup_db_error = str(error)
    yield


app = FastAPI(title="Project Management MVP Backend", lifespan=lifespan)

# M2: CORS configuration
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# M5: Database error handler
@app.exception_handler(mysql.connector.Error)
async def mysql_error_handler(request: Request, exc: mysql.connector.Error) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"detail": "Database temporarily unavailable."},
    )

board_service = BoardService()
chat_service = ChatService()
openai_service = OpenAIService()
ai_assistant_service = AIAssistantService(openai_service=openai_service)


class LoginRequest(BaseModel):
    username: str
    password: str


class AITestRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)


class AITestResponse(BaseModel):
    model: str
    reply: str


class AIChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class AIChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AIChatResponse(BaseModel):
    assistant_message: str
    board: BoardPayload
    board_updated: bool
    board_update_error: str | None = None
    chat_history: list[AIChatMessage]


def _is_authenticated(request: Request) -> bool:
    token = request.cookies.get(settings.auth_cookie_name)
    return settings.verify_session(token or "") is not None


def _require_authenticated_username(request: Request) -> str:
    if startup_db_error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable.",
        )
    token = request.cookies.get(settings.auth_cookie_name)
    username = settings.verify_session(token or "")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )
    return username


@app.get("/api/health")
def health() -> dict:
    is_connected, error = probe_mysql()
    return {
        "status": "ok" if is_connected else "degraded",
        "database": {
            "connected": is_connected,
        },
    }


@app.get("/api/auth/session")
def auth_session(request: Request) -> dict:
    is_authenticated = _is_authenticated(request)
    return {
        "authenticated": is_authenticated,
        "username": settings.auth_username if is_authenticated else None,
    }


@app.post("/api/auth/login")
def auth_login(payload: LoginRequest, request: Request, response: Response) -> dict:
    _check_login_rate_limit(request.client.host if request.client else "unknown")
    if (
        payload.username != settings.auth_username
        or payload.password != settings.auth_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
        )

    response.set_cookie(
        key=settings.auth_cookie_name,
        value=settings.sign_session(settings.auth_username),
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
        max_age=60 * 60 * 24 * 7,
    )
    return {"authenticated": True, "username": settings.auth_username}


@app.post("/api/auth/logout")
def auth_logout(response: Response) -> dict:
    response.delete_cookie(key=settings.auth_cookie_name, path="/")
    return {"authenticated": False, "username": None}


@app.get("/api/board", response_model=BoardPayload)
def get_board(request: Request) -> dict:
    username = _require_authenticated_username(request)
    try:
        return board_service.get_board(username)
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stored board data is invalid. Please contact support.",
        )


@app.put("/api/board", response_model=BoardPayload)
def update_board(payload: BoardPayload, request: Request) -> dict:
    username = _require_authenticated_username(request)
    return board_service.save_board(username, payload)


@app.post("/api/ai/test", response_model=AITestResponse)
def ai_test(payload: AITestRequest, request: Request) -> dict:
    _require_authenticated_username(request)

    try:
        reply = openai_service.get_text_response(payload.prompt)
    except OpenAIConfigError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    except OpenAIUpstreamError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    return {"model": openai_service.model, "reply": reply}


@app.post("/api/ai/chat", response_model=AIChatResponse)
def ai_chat(payload: AIChatRequest, request: Request) -> dict:
    username = _require_authenticated_username(request)
    user_message = payload.message.strip()
    if not user_message:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Message cannot be empty.",
        )

    board = board_service.get_board(username)
    history_before = chat_service.list_messages(username)

    prompt_history = [*history_before, {"role": "user", "content": user_message}]
    try:
        assistant_output = ai_assistant_service.generate_reply(
            board=board,
            chat_history=prompt_history,
            user_message=user_message,
        )
    except OpenAIConfigError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    except (OpenAIUpstreamError, AIAssistantFormatError) as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error

    assistant_message = assistant_output.assistant_message.strip()
    if not assistant_message:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI response did not include an assistant message.",
        )

    board_updated = False
    board_update_error: str | None = None
    board_after = board
    if assistant_output.board is not None:
        try:
            board_after = board_service.save_board(username, assistant_output.board)
            board_updated = True
        except ValidationError:
            board_update_error = "AI proposed an invalid board update; update was skipped."

    chat_service.append_message(username, "user", user_message)
    chat_service.append_message(username, "assistant", assistant_message)
    chat_history = chat_service.list_messages(username)

    return {
        "assistant_message": assistant_message,
        "board": board_after,
        "board_updated": board_updated,
        "board_update_error": board_update_error,
        "chat_history": chat_history,
    }


@app.get("/api/ai/chat/history", response_model=list[AIChatMessage])
def ai_chat_history(
    request: Request,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[dict[str, str]]:
    username = _require_authenticated_username(request)
    return chat_service.list_messages(username, limit=limit, offset=offset)


def _resolve_frontend_dist_dir() -> Path | None:
    configured = Path(settings.frontend_dist_dir)
    local_fallback = Path(__file__).resolve().parents[2] / "frontend" / "out"

    for candidate in (configured, local_fallback):
        if candidate.exists():
            return candidate
    return None


frontend_dist_dir = _resolve_frontend_dist_dir()

if frontend_dist_dir:
    app.mount("/", StaticFiles(directory=frontend_dist_dir, html=True), name="frontend")
else:
    @app.get("/", response_class=HTMLResponse)
    def frontend_missing() -> str:
        return """
        <h1>Frontend build not found</h1>
        <p>Expected static assets at /app/frontend-dist or frontend/out.</p>
        """
