import sqlite3

DB_FILE = "opportunities.db"

def seed_data():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    rfps = [
        {
            "title": "CTARNG Distributed Antenna System (DAS) Project",
            "agency": "Connecticut Army National Guard (CTARNG)",
            "source": "SAM.gov",
            "issue_date": "2025-09-01",
            "due_date": "2025-10-15",
            "url": "https://sam.gov/opp/CTARNG-DAS",
            "category": "Telecommunications",
            "budget": 2500000,
            "budget_published": 2500000,
            "summary": "Install and test a Distributed Antenna System at CTARNG facilities.",
            "scope_of_work": "Provide design, installation, testing, and support of a DAS solution across multiple buildings.",
            "requirements": "DAS coverage across all designated buildings, testing, documentation.",
            "poc": "John Doe, Contract Specialist, john.doe@ct.ng.mil, (860) 555-1234",
            "location": "Hartford, CT",
            "terms": "FAR Part 12 applies. 1-year warranty required.",
            "critical_reqs": "Mandatory site visit scheduled for 2025-09-20.",
            "raw_text": "Sample extracted RFP text for CTARNG DAS.",
            "ai_score": 85,
            "equipment_cost": 1200000,
            "labor_cost": 600000,
            "admin_cost": 200000
        },
        {
            "title": "USPS Digital Transformation – POTS Replacement Pilot",
            "agency": "United States Postal Service (USPS)",
            "source": "SAM.gov",
            "issue_date": "2025-09-10",
            "due_date": "2025-10-20",
            "url": "https://sam.gov/opp/USPS-POTS",
            "category": "Telecom Replacement",
            "budget": 5000000,
            "budget_published": 5000000,
            "summary": "Pilot replacing legacy POTS lines at USPS facilities with VoIP and LTE alternatives.",
            "scope_of_work": "Replace POTS lines at 100 USPS hard locations, including elevators, alarms, and fax machines.",
            "requirements": "POTS replacement, E911 compliance, UPS backup.",
            "poc": "Jane Smith, USPS Procurement, jane.smith@usps.gov, (202) 555-5678",
            "location": "Nationwide (initial pilot in DC, VA, MD)",
            "terms": "Contractor must provide 24/7 support and ensure 99.99% uptime.",
            "critical_reqs": "Contractor must be FedRAMP certified. Mandatory kickoff meeting required.",
            "raw_text": "Sample extracted RFP text for USPS POTS Replacement.",
            "ai_score": 90,
            "equipment_cost": 2500000,
            "labor_cost": 1000000,
            "admin_cost": 500000
        },
        {
            "title": "US Courts Out-of-Band (OOB) Replacement BPA (USCA25R0146)",
            "agency": "Administrative Office of the U.S. Courts",
            "source": "SAM.gov",
            "issue_date": "2025-09-05",
            "due_date": "2025-11-01",
            "url": "https://sam.gov/opp/USCOURTS-OOB",
            "category": "Telecom / OOB Replacement",
            "budget": 20000000,
            "budget_published": 20000000,
            "summary": "BPA for replacing legacy OOB communication systems across US Courts facilities.",
            "scope_of_work": "Provide secure OOB communications hardware and managed services to replace existing systems.",
            "requirements": "OOB replacement hardware, secure VPN, nationwide rollout.",
            "poc": "Michael Johnson, Contracting Officer, michael.johnson@uscourts.gov, (202) 555-9876",
            "location": "Nationwide",
            "terms": "5-year BPA with annual renewals. Must comply with FISMA and NIST 800-53.",
            "critical_reqs": "Contractor must provide FedRAMP Moderate or higher certified solution.",
            "raw_text": "Sample extracted RFP text for US Courts OOB Replacement.",
            "ai_score": 75,
            "equipment_cost": 8000000,
            "labor_cost": 5000000,
            "admin_cost": 2000000
        }
    ]

    for rfp in rfps:
        total_cost = rfp["equipment_cost"] + rfp["labor_cost"] + rfp["admin_cost"]
        suggested_bid = total_cost * 1.25
        profit_margin = ((suggested_bid - total_cost) / total_cost) * 100

        cur.execute("""
            INSERT INTO opportunities (
                title, agency, source, issue_date, due_date, url, category,
                budget, budget_published, summary, scope_of_work, requirements,
                poc, location, terms, critical_reqs, raw_text,
                ai_score, human_score, reasons, status,
                equipment_cost, labor_cost, admin_cost, total_cost,
                suggested_bid, profit_margin
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rfp["title"], rfp["agency"], rfp["source"], rfp["issue_date"], rfp["due_date"],
            rfp["url"], rfp["category"], rfp["budget"], rfp["budget_published"], rfp["summary"],
            rfp["scope_of_work"], rfp["requirements"], rfp["poc"], rfp["location"], rfp["terms"],
            rfp["critical_reqs"], rfp["raw_text"], rfp["ai_score"], None, "Seeded data", "Pending",
            rfp["equipment_cost"], rfp["labor_cost"], rfp["admin_cost"], total_cost,
            suggested_bid, profit_margin
        ))

    conn.commit()
    conn.close()
    print("✅ Phase 2 RFP data seeded successfully.")

if __name__ == "__main__":
    seed_data()
