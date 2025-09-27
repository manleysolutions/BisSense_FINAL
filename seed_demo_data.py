import sqlite3
import subprocess

DB_FILE = "opportunities.db"

demo_opps = [
    {
        "title": "City Hospital Distributed Antenna System Upgrade",
        "agency": "City of Springfield",
        "source": "sam.gov",
        "issue_date": "2025-08-10",
        "due_date": "2025-09-30",
        "url": "https://sam.gov/opp/12345",
        "category": "das",
        "budget": 500000,
    },
    {
        "title": "County Courthouse POTS Replacement Project",
        "agency": "County of Riverside",
        "source": "sam.gov",
        "issue_date": "2025-07-15",
        "due_date": "2025-09-20",
        "url": "https://sam.gov/opp/67890",
        "category": "pots",
        "budget": 200000,
    },
    {
        "title": "Transit Authority Emergency Elevator Phones",
        "agency": "Metro Transit Authority",
        "source": "sam.gov",
        "issue_date": "2025-07-22",
        "due_date": "2025-10-15",
        "url": "https://sam.gov/opp/54321",
        "category": "emergency comms",
        "budget": 150000,
    },
    {
        "title": "Statewide Cybersecurity Network Upgrade",
        "agency": "State of California",
        "source": "sam.gov",
        "issue_date": "2025-08-01",
        "due_date": "2025-09-28",
        "url": "https://sam.gov/opp/99887",
        "category": "cybersecurity",
        "budget": 750000,
    },
    {
        "title": "Public Schools VOIP and Unified Communications Deployment",
        "agency": "District of Columbia Public Schools",
        "source": "sam.gov",
        "issue_date": "2025-07-29",
        "due_date": "2025-09-25",
        "url": "https://sam.gov/opp/33442",
        "category": "voip",
        "budget": 300000,
    },
]

def insert_demo_data():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # 🔥 Clear previous demo data before inserting
    cur.execute("DELETE FROM opportunities WHERE source = 'sam.gov'")

    for opp in demo_opps:
        cur.execute("""
            INSERT OR IGNORE INTO opportunities
            (title, agency, source, issue_date, due_date, url, category, budget)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            opp["title"],
            opp["agency"],
            opp["source"],
            opp["issue_date"],
            opp["due_date"],
            opp["url"],
            opp["category"],
            opp["budget"],
        ))

    conn.commit()
    conn.close()
    print(f"✅ Inserted {len(demo_opps)} new demo opportunities (old demo data cleared).")

if __name__ == "__main__":
    insert_demo_data()

    print("⚙️  Running scoring engine...")
    try:
        subprocess.check_call(["python", "score_opportunities.py"])
    except subprocess.CalledProcessError as e:
        print(f"❌ Scoring failed: {e}")
