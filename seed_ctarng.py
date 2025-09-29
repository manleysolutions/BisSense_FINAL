from app import get_db, init_db, evaluate_rfp

def seed_rfp():
    conn = get_db()
    cur = conn.cursor()
    init_db()  # make sure tables exist

    title = "CTARNG Distributed Antenna System (DAS) Project"
    agency = "Connecticut Army National Guard (CTARNG)"
    source = "SAM.gov"
    issue_date = "2025-09-01"
    due_date = "2025-10-01"
    url = "https://sam.gov/opp/db1ede732002d086298132abfdcb5f45/view"
    category = "Telecom / DAS"
    budget = 250000.00

    cur.execute("""
        INSERT INTO opportunities (title, agency, source, issue_date, due_date, url, category, budget)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (title, agency, source, issue_date, due_date, url, category, budget))
    opp_id = cur.lastrowid

    # Evaluate with your scoring logic
    ai_score, reasons = evaluate_rfp(title, agency, category, budget)
    cur.execute("INSERT INTO scores (opp_id, ai_score, human_score) VALUES (?, ?, ?)",
                (opp_id, ai_score, None))

    cur.execute("INSERT INTO approvals (opp_id, status) VALUES (?, ?)", (opp_id, "Pending"))

    conn.commit()
    conn.close()
    print(f"✅ Seeded CTARNG DAS RFP with score {ai_score} ({', '.join(reasons)})")

if __name__ == "__main__":
    seed_rfp()
