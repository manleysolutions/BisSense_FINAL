import os
import sqlite3
import json
from flask import Flask, render_template, jsonify, send_file, request
from tabulate import tabulate
from openpyxl import Workbook
from datetime import datetime

app = Flask(__name__)

DB_FILE = "opportunities.db"

# ---------------------------
# Database Helpers
# ---------------------------
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    # opportunities table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            agency TEXT,
            category TEXT,
            due_date TEXT,
            url TEXT
        )
    """)
    # scores table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opportunity_id INTEGER UNIQUE,
            score REAL,
            breakdown TEXT,
            updated_at TEXT
        )
    """)
    # approvals table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opportunity_id INTEGER UNIQUE,
            decision TEXT,
            reason TEXT,
            decided_at TEXT
        )
    """)
    conn.commit()

# ---------------------------
# Demo Seeding
# ---------------------------
def seed_demo_data():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as cnt FROM opportunities")
    row = cur.fetchone()
    if row["cnt"] == 0:
        print("🌱 Seeding demo opportunities...")
        demo_data = [
            ("RFP #2025.IT01- DISTRIBUTED ANTENNA SYSTEM (DAS)", "Manhattan Beach Unified School District", "Distributed Antenna Systems (DAS)", "2025-06-01", "https://example.com/mbusd-das"),
            ("RFP #2025.POTS01- POTS LINE REPLACEMENT", "USPS Northeast Region", "POTS Replacement", "2025-07-15", "https://example.com/usps-pots"),
            ("RFP #2025.ELEV01- ELEVATOR EMERGENCY PHONE SYSTEM", "NYC Housing Authority", "Elevator Safety", "2025-08-30", "https://example.com/nycha-elevator"),
        ]
        cur.executemany("""
            INSERT INTO opportunities (title, agency, category, due_date, url)
            VALUES (?, ?, ?, ?, ?)
        """, demo_data)
        conn.commit()
        print("✅ Demo opportunities inserted.")
    else:
        print("ℹ️ Opportunities table already has data — skipping demo seed.")

# ---------------------------
# Routes
# ---------------------------
@app.route("/")
def index():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT o.id, o.title, o.agency, o.category, o.due_date, o.url,
               s.score, s.breakdown,
               a.decision, a.reason
        FROM opportunities o
        LEFT JOIN scores s ON o.id = s.opportunity_id
        LEFT JOIN approvals a ON o.id = a.opportunity_id
        ORDER BY o.id DESC
    """)
    rows = cur.fetchall()
    return render_template("index.html", opportunities=rows)

@app.route("/breakdown/<int:opp_id>")
def breakdown(opp_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT breakdown FROM scores WHERE opportunity_id=?", (opp_id,))
    row = cur.fetchone()
    if row and row["breakdown"]:
        try:
            breakdown = json.loads(row["breakdown"])
        except Exception:
            breakdown = {"raw": row["breakdown"]}
        return jsonify(breakdown)
    return jsonify({"error": "No breakdown available"}), 404

@app.route("/export")
def export():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT o.id, o.title, o.agency, o.category, o.due_date,
               s.score, a.decision, a.reason
        FROM opportunities o
        LEFT JOIN scores s ON o.id = s.opportunity_id
        LEFT JOIN approvals a ON o.id = a.opportunity_id
        ORDER BY o.id DESC
    """)
    rows = cur.fetchall()

    wb = Workbook()
    ws = wb.active
    ws.title = "Opportunities"
    ws.append(["ID", "Title", "Agency", "Category", "Due Date", "Score", "Decision", "Reason"])
    for row in rows:
        ws.append([
            row["id"], row["title"], row["agency"], row["category"],
            row["due_date"], row["score"], row["decision"], row["reason"]
        ])
    filename = "export.xlsx"
    wb.save(filename)
    return send_file(filename, as_attachment=True)

# ---------------------------
# Main Entrypoint
# ---------------------------
if __name__ == "__main__":
    init_db()
    if os.environ.get("DEMO_MODE", "false").lower() == "true":
        seed_demo_data()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
