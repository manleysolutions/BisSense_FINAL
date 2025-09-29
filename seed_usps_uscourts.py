from app import get_db, init_db, evaluate_rfp

def seed_rfp(title, agency, source, issue_date, due_date, url, category, budget):
    conn = get_db()
    cur = conn.cursor()
    init_db()

    cur.execute("""
        INSERT INTO opportunities (title, agency, source, issue_date, due_date, url, category, budget)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (title, agency, source, issue_date, due_date, url, category, budget))
    opp_id = cur.lastrowid

    ai_score, reasons = evaluate_rfp(title, agency, category, budget)
    cur.execute("INSERT INTO scores (opp_id, ai_score, human_score) VALUES (?, ?, ?)",
                (opp_id, ai_score, None))
    cur.execute("INSERT INTO approvals (opp_id, status) VALUES (?, ?)", (opp_id, "Pending"))

    conn.commit()
    conn.close()
    print(f"✅ Seeded {title} with score {ai_score} ({', '.join(reasons)})")

if __name__ == "__main__":
    # USPS POTS Replacement Pilot
    seed_rfp(
        title="USPS Digital Transformation – POTS Replacement Pilot",
        agency="United States Postal Service (USPS)",
        source="Internal Pilot / SAM.gov",
        issue_date="2025-09-15",
        due_date="2025-10-15",
        url="https://about.usps.com/what-we-are-doing/modernization",  # placeholder ref
        category="Telecom / POTS Replacement",
        budget=5000000.0
    )

    # US Courts OOB Replacement BPA
    seed_rfp(
        title="US Courts Out-of-Band (OOB) Replacement BPA (USCA25R0146)",
        agency="Administrative Office of the U.S. Courts",
        source="SAM.gov",
        issue_date="2025-08-01",
        due_date="2025-10-31",
        url="https://sam.gov/opp/USCA25R0146/view",
        category="Network / OOB",
        budget=2000000.0
    )
