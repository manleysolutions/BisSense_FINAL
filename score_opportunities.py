import sqlite3
import json

DB_FILE = "opportunities.db"

# -----------------------
# Simple scoring rules
# -----------------------
def score_opportunity(opp: dict):
    score = 0
    breakdown = []

    # Example rules
    if opp.get("category") and "DAS" in opp["category"].upper():
        score += 50
        breakdown.append("+50 Core discipline: DAS")

    if opp.get("agency") and "Gov" in opp["agency"]:
        score += 25
        breakdown.append("+25 Strategic customer (Gov)")

    if opp.get("budget") and opp["budget"] >= 1000000:
        score += 10
        breakdown.append("+10 Large budget")

    if opp.get("due_date"):
        score += 5
        breakdown.append("+5 Has due date")

    # Default reason/approval
    approval = "Ignore"
    reason = "Does not meet core fit"

    if score >= 75:
        approval = "Select"
        reason = "Strong fit for bidding"
    elif score >= 40:
        approval = "Hold"
        reason = "Moderate fit, requires review"

    return score, approval, reason, breakdown


# -----------------------
# Main scoring routine
# -----------------------
def main():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM opportunities")
    opportunities = cur.fetchall()

    for opp in opportunities:
        opp_dict = dict(opp)  # sqlite3.Row → dict
        score, approval, reason, breakdown = score_opportunity(opp_dict)

        cur.execute("""
            INSERT INTO scores (opportunity_id, score, approval, reason, breakdown)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(opportunity_id) DO UPDATE SET
                score=excluded.score,
                approval=excluded.approval,
                reason=excluded.reason,
                breakdown=excluded.breakdown
        """, (
            opp_dict["id"],
            score,
            approval,
            reason,
            json.dumps(breakdown)
        ))

    conn.commit()
    conn.close()
    print(f"✅ Scored {len(opportunities)} opportunities and updated scores table.")


if __name__ == "__main__":
    main()
