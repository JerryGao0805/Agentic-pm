# Frontend codebase guide

## Purpose

This directory contains the current frontend-only Kanban MVP demo built with Next.js.
It currently runs without backend persistence or authentication.

## Tech stack

- Next.js App Router (`src/app`)
- React + TypeScript
- Tailwind CSS v4 (via `@tailwindcss/postcss`)
- Drag and drop with `@dnd-kit/*`
- Testing: Vitest + Testing Library + Playwright

## Current behavior

- Renders a single Kanban board at `/`.
- Uses fixed column IDs from `src/lib/kanban.ts`.
- Supports:
  - renaming column titles
  - adding cards
  - deleting cards
  - dragging cards within and across columns
- State is local React state only (not persisted).

## Structure

- `src/app/page.tsx`: app entry; renders `KanbanBoard`.
- `src/components/KanbanBoard.tsx`: board state + drag/drop orchestration.
- `src/components/KanbanColumn.tsx`: droppable column with editable title.
- `src/components/KanbanCard.tsx`: sortable card item.
- `src/components/KanbanCardPreview.tsx`: drag overlay preview.
- `src/components/NewCardForm.tsx`: add-card inline form.
- `src/lib/kanban.ts`: board types, seed data, move helpers, ID creation.

## Styling

- Global theme tokens are in `src/app/globals.css`.
- Core palette already matches project colors:
  - `--accent-yellow: #ecad0a`
  - `--primary-blue: #209dd7`
  - `--secondary-purple: #753991`
  - `--navy-dark: #032147`
  - `--gray-text: #888888`

## Tests

- Unit tests:
  - `src/lib/kanban.test.ts`
  - `src/components/KanbanBoard.test.tsx`
- E2E tests:
  - `tests/kanban.spec.ts`
- Commands:
  - `npm run test:unit`
  - `npm run test:e2e`
  - `npm run test:all`

## Notes for upcoming integration

- Board state currently assumes fixed column IDs and card maps; backend schema should preserve this shape.
- `data-testid` patterns are used by tests (`column-*`, `card-*`), so keep these stable unless tests are updated.
- Playwright config currently targets `http://127.0.0.1:3000`; this will need updating when frontend is served by FastAPI at port `8000`.
