import sqlite3

DB_FILE = "opportunities.db"

conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

# Insert some opportunities
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

# Add approvals for testing
cur.execute("INSERT OR IGNORE INTO approvals (opp_id, approval, reason) VALUES (1, 'Approve', 'Core capability match')")
cur.execute("INSERT OR IGNORE INTO approvals (opp_id, approval, reason) VALUES (2, 'Reject', 'Out of scope')")

conn.commit()
conn.close()
print("✅ Test opportunities inserted")
