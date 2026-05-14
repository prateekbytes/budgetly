# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Activate virtualenv (required before running anything)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the dev server (port 5001)
python app.py

# Run all tests
pytest

# Run a single test file
pytest tests/test_auth.py

# Run a single test by name
pytest -k "test_login"
```

## Architecture

**Spendly** is a Flask/SQLite personal expense tracker built as a step-by-step student project. The app is partially scaffolded — placeholder routes exist in `app.py` with "coming in Step N" stubs that students implement incrementally.

### Key files

- `app.py` — Flask application, all route definitions. No blueprints; all routes live here.
- `database/db.py` — SQLite helper module students build in Step 1. Expected to export `get_db()` (returns a connection with `row_factory` and foreign keys on), `init_db()` (creates tables), and `seed_db()` (inserts dev data).
- `templates/base.html` — base layout with navbar and footer. All other templates extend it via `{% extends "base.html" %}`.
- `static/css/style.css` — global styles loaded on every page.
- `static/css/landing.css` — styles for the landing page only, loaded via `{% block head %}`.
- `static/js/main.js` — loaded on every page via base.html; currently a placeholder.

### Template blocks

`base.html` defines four blocks that child templates can fill:
- `title` — `<title>` content
- `head` — extra `<link>` / `<meta>` tags in `<head>`
- `content` — page body inside `<main>`
- `scripts` — page-specific `<script>` tags before `</body>`

### Planned feature set (step progression)

Steps 1-9 are referenced in placeholder routes in `app.py`:
1. Database setup (`database/db.py`)
2-3. Auth (register, login, logout with sessions)
4. Profile page
5-6. Expense listing / dashboard
7-9. Add / edit / delete expenses

The database uses SQLite (no ORM). Foreign keys must be explicitly enabled per connection via `PRAGMA foreign_keys = ON`.
