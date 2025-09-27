import os
import sqlite3
import json
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from tabulate import tabulate
import csv
from openpyxl import Workbook

app = Flask(__name__)

DB_FILE = "opportunities.db"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT o.id, o.title, o.agency, o.category, o.due_date,
               s.score, a.decision AS approval, a.reason, s.breakdown
        FROM opportunities o
        LEFT JOIN scores s ON o.id = s.opportunity_id
        LEFT JOIN approvals a ON o.id = a.opportunity_id
    """)
    rows = cur.fetchall()
    return render_template("index.html", rows=rows)

@app.route("/breakdown/<int:opp_id>")
def breakdown(opp_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT breakdown FROM scores WHERE opportunity_id=?", (opp_id,))
    row = cur.fetchone()

    if not row:
        app.logger.warning(f"Breakdown lookup failed: no row for opportunity {opp_id}")
        return jsonify({"error": f"No score record found for opportunity {opp_id}"}), 404

    if not row["breakdown"]:
        app.logger.warning(f"Breakdown empty for opportunity {opp_id}")
        return jsonify({"error": f"Breakdown missing for opportunity {opp_id}"}), 404

    try:
        data = json.loads(row["breakdown"])
    except Exception as e:
        app.logger.error(f"Invalid breakdown JSON for {opp_id}: {e}")
        return jsonify({"error": f"Invalid breakdown format for {opp_id}"}), 500

    return jsonify(data)

@app.route("/export")
def export():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT o.id, o.title, o.agency, o.category, o.due_date,
               s.score, a.decision AS approval, a.reason
        FROM opportunities o
        LEFT JOIN scores s ON o.id = s.opportunity_id
        LEFT JOIN approvals a ON o.id = a.opportunity_id
    """)
    rows = cur.fetchall()

    # Save CSV
    csv_file = "export.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Title", "Agency", "Category", "Due Date", "Score", "Approval", "Reason"])
        for r in rows:
            writer.writerow([r["id"], r["title"], r["agency"], r["category"], r["due_date"], r["score"], r["approval"], r["reason"]])

    # Save XLSX
    wb = Workbook()
    ws = wb.active
    ws.append(["ID", "Title", "Agency", "Category", "Due Date", "Score", "Approval", "Reason"])
    for r in rows:
        ws.append([r["id"], r["title"], r["agency"], r["category"], r["due_date"], r["score"], r["approval"], r["reason"]])
    wb.save("export.xlsx")

    return send_file(csv_file, as_attachment=True)

if __name__ == "__main__":
    from score_opportunities import main as score_main

    # Auto-score DB on startup
    try:
        score_main()
        print("✅ Opportunities scored at startup")
    except Exception as e:
        print("⚠️ Failed to score on startup:", e)

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
