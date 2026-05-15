# Spec: Login and Logout

## Overview
Implement login and logout so registered users can authenticate and maintain a session across requests. The `GET /login` route already renders a template; this step adds `POST /login` to validate credentials with `check_password_hash`, writes the authenticated user's `id` and `name` into `session`, and redirects to the dashboard (or a placeholder until Step 5). The stub `/logout` route is replaced with a real handler that clears the session and redirects to the landing page. Together these complete the auth pair started in Step 2 (Registration).

## Depends on
- Step 1 (Database setup) — `get_db()` and the `users` table must be in place.
- Step 2 (Registration) — users must exist in the `users` table with hashed passwords.

## Routes
- `GET /login` — render the login form — public (already exists, no change to route definition)
- `POST /login` — validate credentials, set session, redirect — public
- `GET /logout` — clear session, redirect to `/` — logged-in (currently a stub)

## Database changes
No database changes. The existing `users` table already contains `email` and `password_hash`, which are the only fields needed for login.

## Templates
- **Create:** `templates/login.html` — login form with `email` and `password` fields, flash message display, link to `/register`. Extends `base.html`.
- **Modify:** `templates/base.html` — update navbar links to show "Logout" when `session.user_id` is set, and "Login" / "Register" when not.

## Files to change
- `app.py` — add `POST` method to `/login` route; replace the `/logout` stub with a real handler; import `check_password_hash` from `werkzeug.security`; import `session` (already imported).

## Files to create
- `templates/login.html` — login form template.

## New dependencies
No new dependencies. Uses:
- `werkzeug.security.check_password_hash` (already installed)
- `flask.session`, `flask.flash`, `flask.redirect`, `flask.url_for`, `flask.request` (already installed)

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — never string-format SQL
- Passwords verified with `werkzeug.security.check_password_hash` — never compare plain text
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- On failed login: re-render `login.html` with a generic flash message ("Invalid email or password") — do **not** reveal which field was wrong
- On success: store `session["user_id"]` and `session["user_name"]`, then `redirect(url_for("landing"))` (dashboard placeholder until Step 5)
- `/logout` must call `session.clear()` then `redirect(url_for("landing"))`
- Use `methods=["GET", "POST"]` on `/login`; keep `/logout` as GET only

## Definition of done
- [ ] Visiting `GET /login` renders a form with `email` and `password` fields
- [ ] Submitting valid credentials sets `session["user_id"]` and `session["user_name"]` and redirects
- [ ] Submitting an unknown email re-renders the form with a generic error and does not set a session
- [ ] Submitting a correct email but wrong password re-renders the form with the same generic error
- [ ] Submitting with any empty field re-renders the form with an error message
- [ ] Visiting `/logout` clears the session and redirects to the landing page
- [ ] After logout, visiting `/login` shows no logged-in state
- [ ] Navbar shows "Login" / "Register" when logged out and "Logout" when logged in
- [ ] App starts without errors after changes to `app.py`
