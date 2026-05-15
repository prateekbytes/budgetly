import os
import sqlite3
from datetime import datetime, date as date_type
from flask import Flask, render_template, request, redirect, url_for, flash, session
from database.db import get_db, init_db, seed_db
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "spendly-dev-secret")

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("profile"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not all([name, email, password, confirm_password]):
            flash("All fields are required.")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.")
            return render_template("register.html")

        password_hash = generate_password_hash(password, method="pbkdf2:sha256")

        try:
            db = get_db()
            db.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, password_hash),
            )
            db.commit()
            db.close()
        except sqlite3.IntegrityError:
            flash("An account with that email already exists.")
            return render_template("register.html")

        flash("Account created! Please sign in.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("profile"))
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not all([email, password]):
            return render_template("login.html", error="All fields are required.")

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        db.close()

        if user is None or not check_password_hash(user["password_hash"], password):
            return render_template("login.html", error="Invalid email or password.")

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        return redirect(url_for("profile"))

    return render_template("login.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


def _date_filter_clause(date_from, date_to):
    if date_from and date_to:
        return "AND date BETWEEN ? AND ?", (date_from, date_to)
    if date_from:
        return "AND date >= ?", (date_from,)
    if date_to:
        return "AND date <= ?", (date_to,)
    return "", ()


def _build_transactions(user_id, date_from=None, date_to=None):
    clause, params = _date_filter_clause(date_from, date_to)
    db = get_db()
    rows = db.execute(
        f"SELECT date, description, category, amount "
        f"FROM expenses WHERE user_id = ? {clause} ORDER BY date DESC",
        (user_id, *params),
    ).fetchall()
    db.close()
    return [
        {
            "date": datetime.strptime(r["date"], "%Y-%m-%d").strftime("%b %d"),
            "description": r["description"] or "",
            "category": r["category"],
            "amount": f"₹{r['amount']:.2f}",
        }
        for r in rows
    ]


def _build_stats(user_id, date_from=None, date_to=None):
    clause, params = _date_filter_clause(date_from, date_to)
    db = get_db()
    rows = db.execute(
        f"SELECT amount, category FROM expenses WHERE user_id = ? {clause}",
        (user_id, *params),
    ).fetchall()
    db.close()
    if not rows:
        return {"total_spent": "₹0.00", "transaction_count": 0, "top_category": "—"}
    total = sum(r["amount"] for r in rows)
    cat_totals = {}
    for r in rows:
        cat_totals[r["category"]] = cat_totals.get(r["category"], 0) + r["amount"]
    top_category = max(cat_totals, key=cat_totals.get)
    return {
        "total_spent": f"₹{total:.2f}",
        "transaction_count": len(rows),
        "top_category": top_category,
    }


def _build_categories(user_id, date_from=None, date_to=None):
    clause, params = _date_filter_clause(date_from, date_to)
    db = get_db()
    rows = db.execute(
        f"SELECT category, amount FROM expenses WHERE user_id = ? {clause}",
        (user_id, *params),
    ).fetchall()
    db.close()
    cat_totals = {}
    for r in rows:
        cat_totals[r["category"]] = cat_totals.get(r["category"], 0) + r["amount"]
    total = sum(cat_totals.values())
    if total == 0:
        return []
    return sorted(
        [
            {
                "name": cat,
                "amount": f"₹{amt:.2f}",
                "pct": round(amt / total * 100),
            }
            for cat, amt in cat_totals.items()
        ],
        key=lambda x: -cat_totals[x["name"]],
    )


def _parse_date(value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return value
    except (ValueError, TypeError):
        return None


def _start_of_last_n_months(today, n):
    m = today.month - n + 1
    y = today.year
    while m <= 0:
        m += 12
        y -= 1
    return date_type(y, m, 1).isoformat()


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    user_id = session["user_id"]
    db = get_db()
    user_row = db.execute(
        "SELECT name, email, created_at FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    db.close()
    user = {
        "name": user_row["name"],
        "email": user_row["email"],
        "member_since": datetime.strptime(
            user_row["created_at"][:19], "%Y-%m-%d %H:%M:%S"
        ).strftime("%B %d, %Y"),
    }

    date_from = _parse_date(request.args.get("date_from", ""))
    date_to = _parse_date(request.args.get("date_to", ""))

    if date_from and date_to and date_from > date_to:
        flash("Start date must be before end date.")
        date_from = date_to = None

    today = date_type.today()
    presets = {
        "this_month":    {"date_from": today.replace(day=1).isoformat(), "date_to": today.isoformat()},
        "last_3_months": {"date_from": _start_of_last_n_months(today, 3), "date_to": today.isoformat()},
        "last_6_months": {"date_from": _start_of_last_n_months(today, 6), "date_to": today.isoformat()},
    }

    active_preset = None
    for key, p in presets.items():
        if date_from == p["date_from"] and date_to == p["date_to"]:
            active_preset = key
            break

    stats = _build_stats(user_id, date_from, date_to)
    transactions = _build_transactions(user_id, date_from, date_to)
    categories = _build_categories(user_id, date_from, date_to)
    return render_template("profile.html",
        user=user, stats=stats,
        transactions=transactions, categories=categories,
        date_from=date_from, date_to=date_to,
        presets=presets, active_preset=active_preset)


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:_expense_id>/edit")
def edit_expense(_expense_id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:_expense_id>/delete")
def delete_expense(_expense_id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1", port=5001)
