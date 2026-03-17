# Backend guide

## Purpose

This directory contains the FastAPI backend for the Project Management MVP.

## Part 2 scope

- `app/main.py`: FastAPI app, hello page at `/`, health API at `/api/health`.
- `app/db.py`: MySQL connectivity probe used by health endpoint.
- `app/config.py`: environment-backed runtime settings.
- `pyproject.toml`: Python dependencies managed by `uv`.
- `Dockerfile`: backend container image build and runtime command.

## Run (from repository root)

Use `./scripts/start.sh` and `./scripts/stop.sh`.
