# Session Auto-Naming Design

**Date**: 2026-06-06
**Status**: Approved

## Feature

Sessions currently display UUIDs in the sidebar. Add auto-generated human-readable names from the first user message, with inline editing.

## Changes

### Database

- Add `name TEXT` column to `sessions` table (default "New Session")

### Backend

**models.py** — Add `name: str` field to Session dataclass
**database.py** — Migration: ALTER TABLE sessions ADD COLUMN name
**repository.py**:
- `create_session()` → name defaults to "New Session"
- New `update_session_name(session_id, name)` function
- `add_message()` → auto-set name from first user message (first 40 chars)
**chat.py** — After saving first user message, call `update_session_name()` with truncated prompt
**session.py** — New `PATCH /api/sessions/{id}` endpoint accepting `{"name": "..."}`

### Frontend

**chat.html**:
- Session list items display `s.name || s.session_id` (fallback to UUID)
- Click on session name → inline edit (contenteditable or prompt-based)
- On blur/enter → PATCH to update name
- `loadSessions()` returns names in the session list
- `SessionResponse` API model updated to include name

### Auto-naming logic

- Trigger: first user message in a session (check if current name is "New Session")
- Content: `prompt[:40].strip()` — truncate at 40 chars
- Edge case: if prompt is empty/null, keep "New Session"
