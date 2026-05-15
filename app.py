import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from database.db import get_db, init_db, seed_db
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "spendly-dev-secret"

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


def _build_transactions(user_id):
    db = get_db()
    rows = db.execute(
        "SELECT date, description, category, amount "
        "FROM expenses WHERE user_id = ? ORDER BY date DESC",
        (user_id,),
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


def _build_stats(user_id):
    db = get_db()
    rows = db.execute(
        "SELECT amount, category FROM expenses WHERE user_id = ?",
        (user_id,),
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


def _build_categories(user_id):
    db = get_db()
    rows = db.execute(
        "SELECT category, amount FROM expenses WHERE user_id = ?",
        (user_id,),
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
    stats = _build_stats(user_id)
    transactions = _build_transactions(user_id)
    categories = _build_categories(user_id)
    return render_template("profile.html",
        user=user, stats=stats,
        transactions=transactions, categories=categories)


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
    app.run(debug=True, port=5001)
