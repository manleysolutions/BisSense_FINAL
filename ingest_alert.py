# ingest_alert.py
import sqlite3
from datetime import datetime

DB_FILE = "opportunities.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
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
            budget REAL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opp_id INTEGER,
            score INTEGER
        )
    """)
    conn.commit()
    conn.close()

def ingest_opportunity(item, score=None):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Check if already exists (by URL or title/agency combo)
    cur.execute("""
        SELECT id FROM opportunities
        WHERE url=? OR (title=? AND agency=?)
    """, (item["url"], item["title"], item["agency"]))
    row = cur.fetchone()

    if row:
        opp_id = row[0]
        cur.execute("""
            UPDATE opportunities
            SET title=?, agency=?, source=?, issue_date=?, due_date=?, url=?, category=?, budget=?
            WHERE id=?
        """, (
            item["title"], item["agency"], item["source"], item.get("issue_date",""),
            item.get("due_date",""), item["url"], item.get("category",""),
            item.get("budget"), opp_id
        ))
    else:
        cur.execute("""
            INSERT INTO opportunities (title, agency, source, issue_date, due_date, url, category, budget)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item["title"], item["agency"], item["source"], item.get("issue_date",""),
            item.get("due_date",""), item["url"], item.get("category",""),
            item.get("budget")
        ))
        opp_id = cur.lastrowid

    if score is not None:
        cur.execute("INSERT INTO scores (opp_id, score) VALUES (?, ?)", (opp_id, score))

    conn.commit()
    conn.close()
    return opp_id

if __name__ == "__main__":
    init_db()
    # Example test
    test_item = {
        "title": "ITB 26SWS0820A – Rabinowitz Courthouse BDA/DAS",
        "agency": "Alaska Department of Public Safety",
        "source": "Alaska Online Public Notices",
        "issue_date": "2025-09-20",
        "due_date": "2025-10-06 14:00 AKT",
        "url": "https://aws.state.ak.us/OnlinePublicNotices",
        "category": "DAS/BDA",
        "budget": None
    }
    opp_id = ingest_opportunity(test_item, score=78)
    print(f"✅ Opportunity ingested with ID={opp_id}")
