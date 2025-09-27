import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)
DB_FILE = "opportunities.db"


# -----------------------------
# Database Helpers
# -----------------------------
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def migrate_opportunities():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            agency TEXT,
            source TEXT,
            issue_date TEXT,
            due_date TEXT,
            url TEXT,
            category TEXT,
            budget REAL,
            hash TEXT UNIQUE
        )
    """)
    conn.commit()
    conn.close()
    print("✅ Migration complete: opportunities table created/verified.")


def migrate_approvals():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opp_id INTEGER NOT NULL,
            approval TEXT DEFAULT 'Ignore',
            reason TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (opp_id) REFERENCES opportunities(id)
        )
    """)
    conn.commit()
    conn.close()
    print("✅ Migration complete: approvals table created/verified.")


# -----------------------------
# Auto-run migrations at startup
# -----------------------------
migrate_opportunities()
migrate_approvals()


# -----------------------------
# Routes
# -----------------------------
@app.route("/")
def index():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT o.id, o.title, o.agency, o.source, o.issue_date, o.due_date,
               o.url, o.category, o.budget,
               IFNULL(s.score, 0) AS score,
               a.approval, a.reason
        FROM opportunities o
        LEFT JOIN scores s ON o.id = s.opp_id
        LEFT JOIN approvals a ON o.id = a.opp_id
        ORDER BY o.due_date ASC
    """)
    opportunities = cur.fetchall()
    conn.close()
    return render_template("index.html", opportunities=opportunities)


@app.route("/approve/<int:opp_id>/<action>")
def approve(opp_id, action):
    reason = request.args.get("reason", "")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO approvals (opp_id, approval, reason)
        VALUES (?, ?, ?)
        ON CONFLICT(opp_id) DO UPDATE SET
            approval = excluded.approval,
            reason = excluded.reason,
            updated_at = CURRENT_TIMESTAMP
    """, (opp_id, action, reason))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/api/opportunities")
def api_opportunities():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM opportunities")
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(rows)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

