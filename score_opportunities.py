import sqlite3
import datetime
from app import auto_decide  # ✅ reuse auto decision logic

DB_FILE = "opportunities.db"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def score_opportunity(row):
    """Very simple scoring model — expand later with more rules."""
    score = 0
    reasons = []

    title = (row["title"] or "").lower()
    agency = (row["agency"] or "").lower()
    desc = (row["description"] or "").lower()

    # Strategic customers
    if any(s in agency for s in [".gov", ".edu", ".mil", "army", "navy", "air force", "usaf", "dod"]):
        score += 15
        reasons.append("+15 Strategic customer (.gov/.edu/.mil)")

    # Match categories (examples)
    if "das" in title or "distributed antenna" in desc:
        score += 20
        reasons.append("+20 Core DAS opportunity")

    if "voip" in title or "pots" in desc or "telephony" in desc:
        score += 15
        reasons.append("+15 POTS/VoIP replacement")

    # Size hints (basic text scan)
    if "100k" in desc or "100,000" in desc:
        score += 10
        reasons.append("+10 Large project size")

    # Competition (heuristic: fewer keywords about “commodity” equipment = better)
    if any(k in desc for k in ["cisco", "dell", "hp", "hardware only"]):
        score -= 10
        reasons.append("-10 Higher competition (commodity IT)")

    # Default boost if empty
    if score == 0:
        reasons.append("No strong match")
    
    return score, "; ".join(reasons)

def main():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT o.*
        FROM opportunities o
        LEFT JOIN scores s ON o.id = s.opportunity_id
        WHERE s.id IS NULL
    """)
    rows = cur.fetchall()

    for row in rows:
        score, reasons = score_opportunity(row)
        cur.execute("""
            INSERT INTO scores (opportunity_id, score, reasons, created_at)
            VALUES (?, ?, ?, ?)
        """, (row["id"], score, reasons, datetime.datetime.utcnow()))
        print(f"✅ Scored opportunity {row['id']}: {score} ({reasons})")

    conn.commit()

    # 🔥 Run auto decision if AUTO_MODE is ON
    auto_decide()
    print("🎯 Scoring complete (auto-decisions applied if enabled).")

if __name__ == "__main__":
    main()
