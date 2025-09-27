import sqlite3
import datetime

DB_FILE = "opportunities.db"

def score_opportunity(row):
    """
    Phase 2 scoring logic
    """
    title = (row["title"] or "").lower()
    desc = (row["description"] or "").lower()
    category = row["category"] or "Uncategorized"

    score = 0
    reasons = []

    # --- Base category weighting ---
    if category != "Uncategorized":
        score += row["category_weight"] or 0
        reasons.append(f"+{row['category_weight']} {category}")

    # --- Priority verticals (Gov, Edu, Mil) ---
    if any(ext in (row["url"] or "").lower() for ext in [".gov", ".edu", ".mil"]):
        score += 15
        reasons.append("+15 Strategic customer (.gov/.edu/.mil)")

    # --- DAS / POTS replacement priority ---
    if "das" in title or "distributed antenna" in title or "pots" in title or "analog line" in title:
        score += 20
        reasons.append("+20 Core discipline (DAS / POTS replacement)")

    # --- Competition heuristic ---
    if any(word in title for word in ["cisco", "dell", "hp", "equipment"]):
        score -= 10
        reasons.append("-10 High competition (commodity IT)")
    else:
        score += 5
        reasons.append("+5 Lower competition")

    # --- Margin / Labor vs Equipment ---
    if any(word in title for word in ["install", "installation", "integration", "maintenance", "upgrade"]):
        score += 10
        reasons.append("+10 Labor-driven (good margins)")
    if any(word in title for word in ["purchase", "supply", "equipment", "hardware"]):
        score -= 5
        reasons.append("-5 Equipment-heavy (lower margins)")

    # --- Effort heuristic ---
    if any(word in desc for word in ["sqft", "square feet", "100k"]):
        score += 10
        reasons.append("+10 Large project scale (good fit)")
    if "small" in desc or "pilot" in desc:
        score -= 5
        reasons.append("-5 Small project / pilot")

    # --- Due date buffer ---
    due = row["due_date"] or ""
    if due:
        try:
            due_date = datetime.datetime.strptime(due, "%Y-%m-%d")
            days_left = (due_date - datetime.datetime.utcnow()).days
            if days_left >= 20:
                score += 10
                reasons.append("+10 Long runway (20+ days to bid)")
            elif days_left >= 5:
                score += 5
                reasons.append("+5 Adequate runway")
            else:
                score -= 10
                reasons.append("-10 Very short runway (<5 days)")
        except Exception:
            pass

    # --- Seasonal penalty ---
    month = datetime.datetime.utcnow().month
    if "antenna" in title or "roof" in desc:
        if month in [12, 1, 2, 7, 8]:
            score -= 5
            reasons.append("-5 Seasonal risk (roof work)")

    # --- Normalize ---
    if score < 0:
        score = 0

    return score, "; ".join(reasons)


def main():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM opportunities")
    rows = cur.fetchall()

    for row in rows:
        opp_id = row["id"]
        score, reasons = score_opportunity(row)

        # delete old scores for this opportunity (dedup)
        cur.execute("DELETE FROM scores WHERE opportunity_id = ?", (opp_id,))

        cur.execute("""
            INSERT INTO scores (opportunity_id, score, reasons, created_at)
            VALUES (?, ?, ?, ?)
        """, (opp_id, score, reasons, datetime.datetime.utcnow()))

        print(f"✅ Scored opportunity {opp_id}: {score} ({row['title']})")

    conn.commit()
    conn.close()
    print("🎯 Phase 2 scoring complete (deduped).")

if __name__ == "__main__":
    main()
