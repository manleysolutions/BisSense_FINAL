import sqlite3
import hashlib
from datetime import datetime, timedelta

DB_FILE = "opportunities.db"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def insert_demo_data():
    conn = get_db()
    cur = conn.cursor()

    demo_opps = [
        {
            "title": "Distributed Antenna System Upgrade – Manhattan Office",
            "agency": "USPS",
            "source": "SAM.gov",
            "issue_date": (datetime.today() - timedelta(days=3)).strftime("%Y-%m-%d"),
            "due_date": (datetime.today() + timedelta(days=14)).strftime("%Y-%m-%d"),
            "url": "https://sam.gov/demo1",
            "category": "DAS",
            "budget": 250000
        },
        {
            "title": "Emergency Elevator Phone Retrofit – California",
            "agency": "California State University",
            "source": "State Procurement",
            "issue_date": (datetime.today() - timedelta(days=5)).strftime("%Y-%m-%d"),
            "due_date": (datetime.today() + timedelta(days=25)).strftime("%Y-%m-%d"),
            "url": "https://state.ca.gov/demo2",
            "category": "Emergency Comms",
            "budget": 120000
        },
        {
            "title": "Fire Alarm System Modernization – Houston ISD",
            "agency": "Houston ISD",
            "source": "School District",
            "issue_date": (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "due_date": (datetime.today() + timedelta(days=40)).strftime("%Y-%m-%d"),
            "url": "https://houstonisd.gov/demo3",
            "category": "FACP",
            "budget": 180000
        },
        {
            "title": "Cybersecurity and Network Upgrade – Army Base",
            "agency": "Department of Defense",
            "source": "Army Procurement",
            "issue_date": (datetime.today() - timedelta(days=2)).strftime("%Y-%m-%d"),
            "due_date": (datetime.today() + timedelta(days=20)).strftime("%Y-%m-%d"),
            "url": "https://dod.mil/demo4",
            "category": "Cybersecurity",
            "budget": 400000
        },
        {
            "title": "Neutral Host DAS Deployment – NYC Housing Authority",
            "agency": "NYC Housing Authority",
            "source": "City Bid Portal",
            "issue_date": (datetime.today() - timedelta(days=7)).strftime("%Y-%m-%d"),
            "due_date": (datetime.today() + timedelta(days=10)).strftime("%Y-%m-%d"),
            "url": "https://nyc.gov/demo5",
            "category": "DAS",
            "budget": 300000
        }
    ]

    for opp in demo_opps:
        opp_str = f"{opp['title']}{opp['agency']}{opp['due_date']}"
        opp_hash = hashlib.sha256(opp_str.encode("utf-8")).hexdigest()

        cur.execute("""
            INSERT OR IGNORE INTO opportunities
            (title, agency, source, issue_date, due_date, url, category, budget, hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            opp["title"], opp["agency"], opp["source"], opp["issue_date"],
            opp["due_date"], opp["url"], opp["category"], opp["budget"], opp_hash
        ))

    conn.commit()
    conn.close()
    print("✅ Demo opportunities with budgets inserted successfully.")

if __name__ == "__main__":
    insert_demo_data()
