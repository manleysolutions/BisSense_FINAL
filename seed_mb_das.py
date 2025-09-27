import sqlite3, datetime

DB_FILE = "opportunities.db"

opportunity = {
    "external_id": "MBUSD-DAS-2025",
    "title": "RFP #2025.IT01- DISTRIBUTED ANTENNA SYSTEM (DAS)",
    "agency": "Manhattan Beach Unified School District",
    "source": "OpenMarket",
    "issue_date": "2025-05-05",
    "due_date": "2025-06-01",
    "url": "https://4.files.edl.io/958d/05/05/25/213217-8d467f8c-dd5a-4903-b141-61825e3b3451.pdf",
    "naics": "517919",  # Other Telecommunications
    "keywords": "DAS, distributed antenna system, neutral host, BDA",
    "est_value": "Unknown",
    "status": "Open",
    "description": "The Manhattan Beach Unified School District is requesting proposals for the design and implementation of a Distributed Antenna System (DAS) for enhanced wireless coverage.",
    "category": "Distributed Antenna Systems (DAS)",
    "category_weight": 10,
}

def insert_and_score():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Insert or replace the opportunity
    cur.execute("""
        INSERT OR REPLACE INTO opportunities (
            id, external_id, title, agency, source, issue_date, due_date,
            url, naics, keywords, est_value, status, description,
            category, category_weight
        ) VALUES (
            (SELECT id FROM opportunities WHERE source=? AND external_id=?),
            ?,?,?,?,?,?,?,?,?,?,?,?,?,?
        )
    """, (
        opportunity["source"], opportunity["external_id"],  # lookup key
        opportunity["external_id"], opportunity["title"], opportunity["agency"],
        opportunity["source"], opportunity["issue_date"], opportunity["due_date"],
        opportunity["url"], opportunity["naics"], opportunity["keywords"],
        opportunity["est_value"], opportunity["status"], opportunity["description"],
        opportunity["category"], opportunity["category_weight"]
    ))

    opp_id = cur.lastrowid
    print(f"✅ Inserted/Updated {opportunity['title']} (ID={opp_id})")

    # Score logic
    score = 0
    reasons = []

    if "DAS" in opportunity["category"]:
        score += 50
        reasons.append("+50 Core discipline: DAS")

    if any(word in opportunity["agency"].lower() for word in ["school", "district", "city", "county", "government"]):
        score += 25
        reasons.append("+25 Strategic customer (Gov/Edu)")

    try:
        due = datetime.datetime.strptime(opportunity["due_date"], "%Y-%m-%d")
        days_left = (due - datetime.datetime.now()).days
        if days_left >= 20:
            score += 10
            reasons.append(f"+10 Ample time to respond ({days_left} days left)")
    except Exception:
        pass

    # Clear old score if exists
    cur.execute("DELETE FROM scores WHERE opportunity_id=?", (opp_id,))
    cur.execute("""
        INSERT INTO scores (opportunity_id, score, reasons, created_at)
        VALUES (?, ?, ?, ?)
    """, (opp_id, score, "; ".join(reasons), datetime.datetime.now(datetime.UTC)))

    # Insert approval (auto Select to Bid)
    cur.execute("DELETE FROM approvals WHERE opportunity_id=?", (opp_id,))
    cur.execute("""
        INSERT INTO approvals (opportunity_id, reviewer, decision, notes, decided_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        opp_id, "System", "Select to Bid",
        "Auto-approved because DAS project matches core discipline and strategic fit",
        datetime.datetime.now(datetime.UTC)
    ))

    conn.commit()
    conn.close()

    print(f"🎯 Scored {opportunity['title']} with {score} points")
    for r in reasons:
        print("   -", r)
    print("✅ Auto-marked as Select to Bid")

if __name__ == "__main__":
    insert_and_score()
