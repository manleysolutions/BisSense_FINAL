import sqlite3
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
DB_FILE = "opportunities.db"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    min_score = request.args.get("min_score", default=0, type=int)
    status_filter = request.args.get("status", default="All")

    conn = get_db()
    cur = conn.cursor()

    query = """
        SELECT o.id, o.title, o.agency, o.due_date, o.source,
               COALESCE(s.score, 0) AS score,
               COALESCE(a.decision, 'Pending') AS status
        FROM opportunities o
        LEFT JOIN scores s ON o.id = s.opportunity_id
        LEFT JOIN approvals a ON o.id = a.opportunity_id
        WHERE COALESCE(s.score, 0) >= ?
    """
    params = [min_score]

    if status_filter != "All":
        query += " AND COALESCE(a.decision, 'Pending') = ?"
        params.append(status_filter)

    query += " ORDER BY s.score DESC, o.due_date ASC LIMIT 50"

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()

    return render_template("index.html", rows=rows, min_score=min_score, status_filter=status_filter)

@app.route("/opportunity/<int:opp_id>")
def opportunity_detail(opp_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM opportunities WHERE id=?", (opp_id,))
    opp = cur.fetchone()

    cur.execute("SELECT * FROM scores WHERE opportunity_id=?", (opp_id,))
    score = cur.fetchone()

    cur.execute("SELECT * FROM approvals WHERE opportunity_id=?", (opp_id,))
    approval = cur.fetchone()

    conn.close()
    return render_template("detail.html", opp=opp, score=score, approval=approval)

@app.route("/decision/<int:opp_id>/<decision>", methods=["POST"])
def decision(opp_id, decision):
    reviewer = "Deric"  # static for now
    notes = request.form.get("notes", "")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO approvals (opportunity_id, reviewer, decision, notes, decided_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(opportunity_id) DO UPDATE SET
            reviewer=excluded.reviewer,
            decision=excluded.decision,
            notes=excluded.notes,
            decided_at=CURRENT_TIMESTAMP
    """, (opp_id, reviewer, decision, notes))

    conn.commit()
    conn.close()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True, port=5000)
