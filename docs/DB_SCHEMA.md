# Database Schema

## Scope

This schema supports the MVP requirements and keeps multi-user extension straightforward.
Current MVP behavior still uses a single hardcoded credential (`user` / `password`), but data is user-scoped in the database.

## Tables

### `users`

- `id` (`BIGINT`, PK, auto-increment)
- `username` (`VARCHAR(255)`, unique, not null)
- `created_at` (`TIMESTAMP`, default `CURRENT_TIMESTAMP`)

Notes:
- One row per future real user.
- MVP login seeds `user` at startup.

### `boards`

- `user_id` (`BIGINT`, PK, FK -> `users.id`, cascade delete)
- `board_json` (`JSON`, not null)
- `created_at` (`TIMESTAMP`, default `CURRENT_TIMESTAMP`)
- `updated_at` (`TIMESTAMP`, default `CURRENT_TIMESTAMP`, auto-update on row update)

Notes:
- One board per user is enforced by `user_id` being the primary key.
- Board state is stored as full JSON (single document).

### `chat_messages`

- `id` (`BIGINT`, PK, auto-increment)
- `user_id` (`BIGINT`, FK -> `users.id`, cascade delete)
- `role` (`ENUM('user', 'assistant')`, not null)
- `content` (`TEXT`, not null)
- `created_at` (`TIMESTAMP`, default `CURRENT_TIMESTAMP`)
- index: `(user_id, created_at)`

Notes:
- Stores ordered sidebar conversation history per user.
- Included now so AI features can persist history in the next implementation steps.

## Board JSON contract

The backend validates board payloads before persistence:

- Columns must contain exactly these fixed IDs (titles are editable):
  - `col-backlog`
  - `col-discovery`
  - `col-progress`
  - `col-review`
  - `col-done`
- Column IDs must be unique.
- Every card ID may appear in at most one column.
- Every card referenced in columns must exist in `cards`.
- Every `cards` entry must appear in exactly one column.
- Each card map key must match the card object's `id`.

Invalid payloads are rejected with request validation errors.

## Initialization behavior

On backend startup:

1. Create database if missing (`CREATE DATABASE IF NOT EXISTS`).
2. Create tables if missing.
3. Ensure default MVP user exists.
4. Ensure the user has a default board row.

The database creation step tries app credentials first, then admin credentials (`DB_ADMIN_USER` / `DB_ADMIN_PASSWORD`) if needed.
