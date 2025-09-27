import os
import sqlite3
from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from tabulate import tabulate
from openpyxl import Workbook
from datetime import datetime

# Blueprints
from uploads_bp import uploads_bp

DB_FILE = "opportunities.db"

app = Flask(__name__)
app.secret_key = "super-secret-key"  # TODO: replace with env var in prod

# Register blueprints
app.register_blueprint(uploads_bp)

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT o.id, o.title, o.agency, o.source, o.issue_date, o.due_date,
               o.url, o.category, o.budget,
               s.score, s.breakdown, a.decision, a.reason
        FROM opportunities o
        LEFT JOIN scores s ON o.id = s.opportunity_id
        LEFT JOIN approvals a ON o.id = a.opportunity_id
        ORDER BY o.due_date ASC
    """)
    opportunities = cur.fetchall()
    conn.close()
    return render_template("index.html", opportunities=opportunities)

@app.route("/export")
def export():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT o.title, o.agency, o.source, o.issue_date, o.due_date,
               o.url, o.category, o.budget, s.score, a.decision
        FROM opportunities o
        LEFT JOIN scores s ON o.id = s.opportunity_id
        LEFT JOIN approvals a ON o.id = a.opportunity_id
        ORDER BY o.due_date ASC
    """)
    rows = cur.fetchall()
    conn.close()

    wb = Workbook()
    ws = wb.active
    ws.title = "Opportunities"

    headers = ["Title", "Agency", "Source", "Issue Date", "Due Date",
               "URL", "Category", "Budget", "Score", "Decision"]
    ws.append(headers)

    for row in rows:
        ws.append([row["title"], row["agency"], row["source"], row["issue_date"],
                   row["due_date"], row["url"], row["category"], row["budget"],
                   row["score"], row["decision"]])

    fname = f"opportunities_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.xlsx"
    wb.save(fname)
    return send_file(fname, as_attachment=True)

@app.route("/approve/<int:opp_id>", methods=["POST"])
def approve(opp_id):
    decision = request.form.get("decision")
    reason = request.form.get("reason", "")
    now = datetime.utcnow().isoformat()

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO approvals(opportunity_id, decision, reason, decided_at)
        VALUES(?,?,?,?)
        ON CONFLICT(opportunity_id) DO UPDATE SET
            decision=excluded.decision,
            reason=excluded.reason,
            decided_at=excluded.decided_at
    """, (opp_id, decision, reason, now))
    conn.commit()
    conn.close()

    flash(f"Opportunity {opp_id} updated to '{decision}'.", "success")
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
