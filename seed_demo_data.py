import sqlite3
import hashlib
import datetime
import subprocess
import sys
import os

DB_FILE = "opportunities.db"

# Demo opportunities
demo_opps = [
    {
        "title": "Distributed Antenna System Upgrade – CTARNG Groton Facility",
        "agency": "Connecticut Army National Guard",
        "source": "SAM.gov",
        "issue_date": "2025-08-01",
        "due_date": "2025-10-25",
        "url": "https://sam.gov/opp/ctarng-das",
        "category": "DAS",
        "budget": 750000
    },
    {
        "title": "POTS Replacement for USPS Regional Facilities",
        "agency": "United States Postal Service",
        "source": "OpenMarket",
        "issue_date": "2025-07-15",
        "due_date": "2025-10-26",
        "url": "https://usps.gov/rfp/pots-replacement",
        "category": "POTS/Telephony",
        "budget": 1200000
    },
    {
        "title": "Elevator Emergency Phone Modernization – NYC DOE",
        "agency": "New York City Department of Education",
        "source": "NYC Bids",
        "issue_date": "2025-09-01",
        "due_date": "2025-10-10",
        "url": "https://nyc.gov/rfp/elevator-emergency-phone",
        "category": "Elevators/Emergency Phones",
        "budget": 450000
    },
    {
        "title": "Fire Alarm Monitoring & Remote Supervision – Houston ISD",
        "agency": "Houston Independent School District",
        "source": "OpenMarket",
        "issue_date": "2025-08-10",
        "due_date": "2025-10-05",
        "url": "https://houstonisd.org/rfp/fire-alarm",
        "category": "Fire Alarm Monitoring",
        "budget": 300000
    },
    {
        "title": "Private 5G Network Deployment – Veterans Affairs Hospitals",
        "agency": "Department of Veterans Affairs",
        "source": "SAM.gov",
        "issue_date": "2025-09-01",
        "due_date": "2025-11-01",
        "url": "https://sam.gov/opp/va-5g-network",
        "category": "5G/Private Networks",
        "budget": 2500000
    },
    {
        "title": "Structured Cabling Refresh – California State University",
        "agency": "California State University",
        "source": "Google CSE",
        "issue_date": "2025-08-12",
        "due_date": "2025-10-09",
        "url": "https://calstate.edu/rfp/cabling-refresh",
        "category": "Structured Cabling",
        "budget": 600000
    },
    {
        "title": "IT Consulting BPA – USDA",
        "agency": "U.S. Department of Agriculture",
        "source": "SAM.gov",
        "issue_date": "2025-09-05",
        "due_date": "2025-10-27",
        "url": "https://sam.gov/opp/usda-it-consulting",
        "category": "IT Consulting",
        "budget": 500000
    },
    {
        "title": "Healthcare IoT Monitoring System – Cleveland Clinic",
        "agency": "Cleveland Clinic",
        "source": "OpenMarket",
        "issue_date": "2025-08-15",
        "due_date": "2025-10-25",
        "url": "https://clevelandclinic.org/rfp/healthcare-iot",
        "category": "Healthcare Tech",
        "budget": 950000
    },
    {
        "title": "Cybersecurity Operations Center Expansion – DHS",
        "agency": "Department of Homeland Security",
        "source": "SAM.gov",
        "issue_date": "2025-09-10",
        "due_date": "2025-11-10",
        "url": "https://sam.gov/opp/dhs-cyber-ops",
        "category": "Military & Defense",
        "budget": 5000000
    },
    {
        "title": "Burglar Alarm System Upgrade – Chicago Public Schools",
        "agency": "Chicago Public Schools",
        "source": "Chicago Bids",
        "issue_date": "2025-08-25",
        "due_date": "2025-10-08",
        "url": "https://cps.edu/rfp/burglar-alarm",
        "category": "Security Systems",
        "budget": 200000
    }
]

def insert_demo_data():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Ensure opportunities schema has 'hash'
    cur.execute("PRAGMA table_info(opportunities)")
    cols = [r[1] for r in cur.fetchall()]
    if "hash" not in cols:
        raise RuntimeError("opportunities table missing 'hash' column. Run migrate_opportunities_fix.py first.")

    inserted = 0
    for opp in demo_opps:
        hash_input = (opp["title"] + opp["agency"] + opp["due_date"]).encode("utf-8")
        opp_hash = hashlib.sha256(hash_input).hexdigest()

        cur.execute("""
            INSERT OR IGNORE INTO opportunities 
            (title, agency, source, issue_date, due_date, url, category, budget, hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            opp["title"], opp["agency"], opp["source"], opp["issue_date"],
            opp["due_date"], opp["url"], opp["category"], opp["budget"], opp_hash
        ))
        if cur.rowcount:
            inserted += 1

    conn.commit()
    conn.close()
    print(f"✅ Inserted {inserted} new demo opportunities (duplicates ignored).")

def auto_score():
    print("⚙️  Running scoring engine...")
    py = sys.executable or "python"
    try:
        subprocess.check_call([py, "score_opportunities.py"])
        print("✅ Scoring complete.")
    except subprocess.CalledProcessError as e:
        print("❌ Scoring failed:", e)

if __name__ == "__main__":
    insert_demo_data()
    auto_score()
