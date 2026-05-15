# Spec: Registration

## Overview
Implement user registration so new visitors can create a Spendly account. This step adds form handling to the existing `GET /register` stub, validates user input server-side, stores a hashed password in the `users` table, and redirects the user to the login page on success. It is the first half of the auth pair described in Step 2-3 of the roadmap.

## Depends on
- Step 1 (Database setup) — `users` table and `get_db()` must be in place.

## Routes
- `GET /register` — render the registration form — public (already exists, needs no change to route definition)
- `POST /register` — process form submission, insert user, redirect — public

## Database changes
No new tables or columns. The existing `users` table already has all required fields:
- `name TEXT NOT NULL`
- `email TEXT UNIQUE NOT NULL`
- `password_hash TEXT NOT NULL`

## Templates
- **Modify:** `templates/register.html` — replace placeholder content with a real HTML form (`name`, `email`, `password`, `confirm_password` fields). Display flash messages for errors and success. Extends `base.html`.

## Files to change
- `app.py` — add `POST` method to `/register` route; import `request`, `redirect`, `url_for`, `flash`, `session`; add `app.secret_key`
- `templates/register.html` — implement the registration form UI with flash message display

## Files to create
None.

## New dependencies
No new pip packages. Uses:
- `werkzeug.security.generate_password_hash` (already installed)
- `flask.request`, `flask.redirect`, `flask.url_for`, `flask.flash`, `flask.session` (already installed)

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — never string-format SQL
- Passwords hashed with `werkzeug.security.generate_password_hash` using `pbkdf2:sha256`
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- `app.secret_key` must be set (use a hard-coded dev string like `"spendly-dev-secret"` — note: swap for env var in production)
- Server-side validation must check:
  1. All fields are non-empty
  2. `password` and `confirm_password` match
  3. Email is not already registered (catch `UNIQUE` constraint or pre-check with `SELECT`)
- On validation error: re-render the form with a flashed error message; do **not** redirect
- On success: flash a success message and `redirect(url_for("login"))`
- Do **not** log the user in automatically after registration — that is Step 3

## Definition of done
- [ ] Visiting `GET /register` renders a form with `name`, `email`, `password`, and `confirm_password` fields
- [ ] Submitting the form with valid, unique data inserts a new row into `users` with a hashed password
- [ ] Submitting with mismatched passwords re-renders the form with an error message and does not insert a row
- [ ] Submitting with a duplicate email re-renders the form with an error message and does not insert a second row
- [ ] Submitting with any empty field re-renders the form with an error message
- [ ] Successful registration redirects to `GET /login`
- [ ] Raw password is never stored in the database
- [ ] App starts without errors after changes to `app.py`
