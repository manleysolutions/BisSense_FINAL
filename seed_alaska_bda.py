# seed_alaska_bda.py
import sqlite3, datetime

DB = "opportunities.db"

item = {
    "title": "ITB 26SWS0820A – Rabinowitz Courthouse BDA/DAS",
    "agency": "Alaska Department of Public Safety",
    "source": "Alaska Online Public Notices",
    "issue_date": "",  # fill if known, e.g. "2025-09-20"
    "due_date": "2025-10-06 14:00 AKT",  # store as text like your schema
    "url": "https://aws.state.ak.us/OnlinePublicNotices",  # replace with exact notice URL if you have it
    "category": "DAS/BDA",
    "budget": None,  # or a float if stated
}

def upsert_opportunity(conn, item):
    cur = conn.cursor()
    # create tables if missing (matches your schema)
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
    # upsert by URL if present, else by (title, agency)
    cur.execute("SELECT id FROM opportunities WHERE url=? OR (title=? AND agency=?)",
                (item["url"], item["title"], item["agency"]))
    row = cur.fetchone()
    if row:
        opp_id = row[0]
        cur.execute("""
            UPDATE opportunities
            SET title=?, agency=?, source=?, issue_date=?, due_date=?, url=?, category=?, budget=?
            WHERE id=?
        """, (item["title"], item["agency"], item["source"], item["issue_date"], item["due_date"],
              item["url"], item["category"], item["budget"], opp_id))
    else:
        cur.execute("""
            INSERT INTO opportunities (title, agency, source, issue_date, due_date, url, category, budget)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (item["title"], item["agency"], item["source"], item["issue_date"], item["due_date"],
              item["url"], item["category"], item["budget"]))
        opp_id = cur.lastrowid

    # optional: seed a quick Bid/No-Bid score (from earlier: 78)
    cur.execute("INSERT INTO scores (opp_id, score) VALUES (?, ?)", (opp_id, 78))
    conn.commit()
    return opp_id

if __name__ == "__main__":
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    opp_id = upsert_opportunity(conn, item)
    print(f"✅ Upserted opportunity ID={opp_id}")
    conn.close()
