import sqlite3
from flask import Flask, render_template, request, redirect, url_for
import datetime

app = Flask(__name__)
DB_FILE = "opportunities.db"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# --- Helpers ---
def get_auto_mode():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    conn.commit()
    cur.execute("SELECT value FROM settings WHERE key='AUTO_MODE'")
    row = cur.fetchone()
    return row and row["value"] == "1"

def set_auto_mode(enabled: bool):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("AUTO_MODE", "1" if enabled else "0"))
    conn.commit()

# --- Routes ---
@app.route("/", methods=["GET"])
def index():
    min_score = int(request.args.get("min_score", 0))
    status_filter = request.args.get("status", "All")

    conn = get_db()
    cur = conn.cursor()

    query = """
        SELECT o.id, o.title, o.agency, o.due_date, o.source,
               IFNULL(s.score, 0) AS score,
               IFNULL(a.decision, 'Pending') AS status,
               a.reviewer, a.decided_at, a.notes
        FROM opportunities o
        LEFT JOIN scores s ON o.id = s.opportunity_id
        LEFT JOIN approvals a ON o.id = a.opportunity_id
        WHERE s.score >= ?
    """
    params = [min_score]

    if status_filter != "All":
        query += " AND IFNULL(a.decision, 'Pending') = ?"
        params.append(status_filter)

    query += " ORDER BY s.score DESC, o.due_date ASC"

    rows = cur.execute(query, params).fetchall()

    return render_template("index.html",
                           rows=rows,
                           min_score=min_score,
                           status_filter=status_filter,
                           auto_mode=get_auto_mode())

@app.route("/decision/<int:opp_id>/<string:decision>", methods=["POST"])
def decision(opp_id, decision):
    reviewer = "Deric"  # You can later map to logged-in user
    notes = request.form.get("notes", "")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO approvals (opportunity_id, reviewer, decision, notes, decided_at)
        VALUES (?, ?, ?, ?, ?)
    """, (opp_id, reviewer, decision, notes, datetime.datetime.utcnow()))
    conn.commit()
    return redirect(url_for("index"))

@app.route("/toggle_auto", methods=["POST"])
def toggle_auto():
    current = get_auto_mode()
    set_auto_mode(not current)
    return redirect(url_for("index"))

# --- Auto Decision Logic ---
def auto_decide():
    """Run this after scoring to auto-approve/reject when AUTO_MODE is on."""
    if not get_auto_mode():
        return

    conn = get_db()
    cur = conn.cursor()

    # Get all opportunities without a decision
    cur.execute("""
        SELECT o.id, o.title, IFNULL(s.score,0) as score
        FROM opportunities o
        LEFT JOIN scores s ON o.id = s.opportunity_id
        LEFT JOIN approvals a ON o.id = a.opportunity_id
        WHERE a.decision IS NULL
    """)
    rows = cur.fetchall()

    for row in rows:
        opp_id = row["id"]
        score = row["score"]
        if score >= 50:
            decision, notes = "Approved", f"Auto-approved (score {score})"
        elif 20 <= score < 50:
            decision, notes = "Hold", f"Auto-hold (score {score})"
        else:
            decision, notes = "Rejected", f"Auto-rejected (score {score})"

        cur.execute("""
            INSERT OR REPLACE INTO approvals (opportunity_id, reviewer, decision, notes, decided_at)
            VALUES (?, ?, ?, ?, ?)
        """, (opp_id, "AUTO", decision, notes, datetime.datetime.utcnow()))

    conn.commit()

if __name__ == "__main__":
    app.run(debug=True)
