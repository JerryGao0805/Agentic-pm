from __future__ import annotations

import json
from typing import Any

import mysql.connector
from mysql.connector import Error, IntegrityError
from mysql.connector.pooling import MySQLConnectionPool

from app.config import settings
from app.kanban import default_board

_pool: MySQLConnectionPool | None = None


def _get_pool() -> MySQLConnectionPool:
    global _pool
    if _pool is None:
        _pool = MySQLConnectionPool(
            pool_name="pm_pool",
            pool_size=5,
            pool_reset_session=True,
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            database=settings.db_name,
        )
    return _pool


def _connect(*, database: str | None, use_admin_credentials: bool) -> Any:
    user = settings.db_admin_user if use_admin_credentials else settings.db_user
    password = (
        settings.db_admin_password if use_admin_credentials else settings.db_password
    )

    params: dict[str, Any] = {
        "host": settings.db_host,
        "port": settings.db_port,
        "user": user,
        "password": password,
    }
    if database:
        params["database"] = database
    return mysql.connector.connect(**params)


def get_connection(database: str | None = None) -> Any:
    if database == settings.db_name:
        try:
            return _get_pool().get_connection()
        except Error:
            pass
    return _connect(database=database, use_admin_credentials=False)


def _create_database_if_missing() -> None:
    db_name = settings.db_name.replace("`", "``")
    statement = (
        f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )

    first_error: Error | None = None
    for use_admin_credentials in (False, True):
        connection = None
        cursor = None
        try:
            connection = _connect(
                database=None,
                use_admin_credentials=use_admin_credentials,
            )
            cursor = connection.cursor()
            cursor.execute(statement)
            connection.commit()
            return
        except Error as error:
            if first_error is None:
                first_error = error
            if use_admin_credentials:
                raise
        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None:
                connection.close()

    if first_error is not None:
        raise first_error


def ensure_user_id(cursor: Any, username: str) -> int:
    cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
    row = cursor.fetchone()
    if row is not None:
        return int(row[0])

    try:
        cursor.execute("INSERT INTO users (username) VALUES (%s)", (username,))
        return int(cursor.lastrowid)
    except IntegrityError:
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError("Failed to create or load user row.")
        return int(row[0])


def initialize_database() -> None:
    _create_database_if_missing()

    schema_statements = (
        """
        CREATE TABLE IF NOT EXISTS users (
            id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) NOT NULL UNIQUE,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
        """
        CREATE TABLE IF NOT EXISTS boards (
            user_id BIGINT NOT NULL PRIMARY KEY,
            board_json JSON NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            CONSTRAINT fk_boards_user
                FOREIGN KEY (user_id) REFERENCES users(id)
                ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
        """
        CREATE TABLE IF NOT EXISTS chat_messages (
            id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            role ENUM('user', 'assistant') NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_chat_messages_user_created_at (user_id, created_at),
            CONSTRAINT fk_chat_messages_user
                FOREIGN KEY (user_id) REFERENCES users(id)
                ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
    )

    connection = None
    cursor = None
    try:
        connection = get_connection(database=settings.db_name)
        cursor = connection.cursor()

        for statement in schema_statements:
            cursor.execute(statement)

        user_id = ensure_user_id(cursor, settings.auth_username)

        cursor.execute("SELECT 1 FROM boards WHERE user_id = %s", (user_id,))
        board_exists = cursor.fetchone() is not None
        if not board_exists:
            cursor.execute(
                "INSERT INTO boards (user_id, board_json) VALUES (%s, CAST(%s AS JSON))",
                (user_id, json.dumps(default_board())),
            )

        connection.commit()
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


def probe_mysql() -> tuple[bool, str | None]:
    connection = None
    cursor = None
    try:
        connection = get_connection(database=settings.db_name)
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        return True, None
    except Error as error:
        return False, str(error)
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()
