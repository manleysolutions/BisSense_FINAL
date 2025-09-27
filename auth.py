# auth.py
import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

DB_FILE = "opportunities.db"
auth_bp = Blueprint("auth", __name__)

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# ---- Register ---------------------------------------------------------------
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"].lower().strip()
        phone = request.form["phone"]
        password = request.form["password"]
        subscription = request.form.get("subscription", "demo")
        created_at = datetime.utcnow().isoformat()

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE email=?", (email,))
        if cur.fetchone():
            flash("Email already registered. Please log in.", "warning")
            return redirect(url_for("auth.login"))

        pw_hash = generate_password_hash(password)

        cur.execute("""
            INSERT INTO users (name, email, phone, password_hash, role, subscription, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, email, phone, pw_hash, "user", subscription, created_at))

        conn.commit()
        conn.close()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")

# ---- Login ------------------------------------------------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].lower().strip()
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["role"] = user["role"]
            session["subscription"] = user["subscription"]

            flash(f"Welcome {user['name']}!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid credentials. Please try again.", "danger")

    return render_template("login.html")

# ---- Logout -----------------------------------------------------------------
@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
