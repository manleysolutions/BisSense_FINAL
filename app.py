import os
import sqlite3
import threading
import schedule
import time
import subprocess
from flask import Flask, render_template, g

app = Flask(__name__)

DB_FILE = "opportunities.db"

# === Database Connection ===
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_FILE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()

# === Scoring Runner ===
def run_scoring():
    try:
        print("⚙️ [BidSense] Running scoring engine...")
        result = subprocess.run(
            ["python", "score_opportunities.py"],
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ [BidSense] Scoring completed successfully.")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("❌ [BidSense] Scoring failed.")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)

def schedule_scoring():
    interval = int(os.getenv("SCORE_INTERVAL_HOURS", "6"))
    print(f"⏱️ [BidSense] Scheduling scoring every {interval} hour(s).")
    schedule.every(interval).hours.do(run_scoring)
    while True:
        schedule.run_pending()
        time.sleep(60)

# === Routes ===
@app.route("/")
def index():
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT o.id, o.title, o.agency, o.source, o.issue_date, o.due_date,
               s.score, s.breakdown, s.updated_at,
               a.approval
        FROM opportunities o
        LEFT JOIN scores s ON o.id = s.opp_id
        LEFT JOIN approvals a ON o.id = a.opp_id
        ORDER BY o.due_date ASC
    """)
    opportunities = cur.fetchall()
    return render_template("index.html", opportunities=opportunities)

# === Startup Hooks ===
if __name__ == "__main__":
    # Run once immediately
    run_scoring()

    # Start background scheduler thread
    scheduler_thread = threading.Thread(target=schedule_scoring, daemon=True)
    scheduler_thread.start()

    # Start Flask
    print("🚀 [BidSense] Flask app starting at http://127.0.0.1:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
