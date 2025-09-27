import os
import sqlite3
import random
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

DB_FILE = "opportunities.db"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    # Opportunities table
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
            budget REAL
        )
    """)

    # Scores table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opp_id INTEGER,
            score INTEGER
        )
    """)

    # Approvals table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opp_id INTEGER UNIQUE,
            approval TEXT,
            reason TEXT
        )
    """)

    conn.commit()
    conn.close()

def seed_demo_data():
    conn = get_db()
    cur = conn.cursor()

    # Check if opportunities already exist
    cur.execute("SELECT COUNT(*) FROM opportunities")
    count = cur.fetchone()[0]

    if count == 0:
        print("🌱 Seeding demo opportunities...")
        opportunities = [
            ("Distributed Antenna System (DAS)", "USPS", "SAM.gov", "2025-09-01", "2025-09-30", "http://example.com/das", "IT", 500000),
            ("Wi-Fi Modernization", "DOE", "SAM.gov", "2025-09-10", "2025-10-10", "http://example.com/wifi", "IT", 250000),
            ("Cybersecurity Tools", "DHS", "BidPrime", "2025-09-15", "2025-10-20", "http://example.com/cyber", "Cyber", 750000),
        ]

        for opp in opportunities:
            cur.execute("""
                INSERT INTO opportunities (title, agency, source, issue_date, due_date, url, category, budget)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, opp)

        # Insert example approvals
        cur.execute("INSERT OR IGNORE INTO approvals (opp_id, approval, reason) VALUES (1, 'Approve', 'Core capability match')")
        cur.execute("INSERT OR IGNORE INTO approvals (opp_id, approval, reason) VALUES (2, 'Reject', 'Out of scope')")

        # Insert random demo scores
        for opp_id in range(1, 4):
            score = random.choice([40, 55, 70, 85, 90])
            cur.execute("INSERT INTO scores (opp_id, score) VALUES (?, ?)", (opp_id, score))

        conn.commit()
        print("✅ Demo opportunities & scores seeded")

    conn.close()

@app.route("/")
def index():
    conn = get_db()
    cur = conn.cursor()

    # Query opportunities with score + approval info
    cur.execute("""
        SELECT o.id, o.title, o.agency, o.source, o.issue_date, o.due_date,
               o.url, o.category, o.budget,
               IFNULL(s.score, 0) AS score,
               IFNULL(a.approval, 'Ignore') AS approval,
               IFNULL(a.reason, '') AS reason
        FROM opportunities o
        LEFT JOIN scores s ON o.id = s.opp_id
        LEFT JOIN approvals a ON o.id = a.opp_id
        ORDER BY o.due_date ASC
    """)
    opportunities = cur.fetchall()

    # Stats bar
    cur.execute("SELECT COUNT(*) FROM opportunities")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM approvals WHERE approval='Approve'")
    approved = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM approvals WHERE approval='Reject'")
    rejected = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM approvals WHERE approval='Ignore'")
    ignored = cur.fetchone()[0]

    conn.close()

    return render_template(
        "index.html",
        opportunities=opportunities,
        stats={"total": total, "approved": approved, "rejected": rejected, "ignored": ignored}
    )

@app.route("/approve/<int:opp_id>/<action>", methods=["POST"])
def approve(opp_id, action):
    reason = request.form.get("reason", "")
    conn = get_db()
    cur = conn.cursor()

    # Ensure approvals table exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opp_id INTEGER UNIQUE,
            approval TEXT,
            reason TEXT
        )
    """)

    # Upsert approval
    cur.execute("""
        INSERT INTO approvals (opp_id, approval, reason)
        VALUES (?, ?, ?)
        ON CONFLICT(opp_id) DO UPDATE SET approval=excluded.approval, reason=excluded.reason
    """, (opp_id, action, reason))

    conn.commit()
    conn.close()
    return redirect(url_for("index"))

if __name__ == "__main__":
    init_db()
    seed_demo_data()  # 👈 Auto-seed if DB is empty
    app.run(debug=True, host="0.0.0.0", port=5000)
