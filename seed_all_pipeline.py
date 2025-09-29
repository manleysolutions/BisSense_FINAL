# seed_all_pipeline.py
import sqlite3

DB_FILE = "opportunities.db"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def ingest_opportunity(item, score=None):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO opportunities 
        (title, agency, source, issue_date, due_date, url, category, budget, status,
         contacts, submission_method, qna_deadline, prebid, prebid_required, set_aside,
         bonding, insurance, scope_summary, tech_requirements)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        item.get("title"),
        item.get("agency"),
        item.get("source"),
        item.get("issue_date"),
        item.get("due_date"),
        item.get("url"),
        item.get("category"),
        item.get("budget"),
        item.get("status"),
        item.get("contacts"),
        item.get("submission_method"),
        item.get("qna_deadline"),
        item.get("prebid"),
        item.get("prebid_required"),
        item.get("set_aside"),
        item.get("bonding"),
        item.get("insurance"),
        item.get("scope_summary"),
        item.get("tech_requirements")
    ))
    opp_id = cur.lastrowid

    if score is not None:
        cur.execute("INSERT INTO scores (opp_id, score) VALUES (?, ?)", (opp_id, score))

    conn.commit()
    conn.close()
    return opp_id


rfps = [
    # --- DAS ---
    {
        "title": "Neutral Host DAS – Austin Convention Center (RFQS 8200 PLS4005)",
        "agency": "City of Austin Convention Center Department",
        "source": "City of Austin Procurement",
        "issue_date": "2025-07-15",
        "due_date": "2025-09-11 17:00 CST",
        "url": "https://financeonline.austintexas.gov/vss/Advantage",
        "category": "DAS / Neutral Host / In-Building Cellular",
        "budget": 2000000,
        "contacts": "Patricia Sustaita | patricia.sustaita@austintexas.gov | (512) 978-1708",
        "submission_method": "Portal",
        "qna_deadline": "",
        "prebid": "2025-08-05",
        "prebid_required": "Optional",
        "set_aside": "None",
        "bonding": "Not Mentioned",
        "insurance": "Required",
        "status": "Open",
        "score": 65,
        "scope_summary": "Design, deploy, and maintain a neutral host DAS across the Austin Convention Center supporting multiple carriers.",
        "tech_requirements": "DAS / Neutral Host, Multi-Carrier, LTE/5G Ready"
    },
    {
        "title": "Neutral DAS – US Holocaust Memorial Museum (95476725R1060)",
        "agency": "US Holocaust Memorial Museum",
        "source": "SAM.gov",
        "issue_date": "2025-07-01",
        "due_date": "2025-08-01 12:00 EST",
        "url": "https://sam.gov/opp/95476725R1060",
        "category": "DAS / Neutral Host / In-Building Cellular",
        "budget": None,
        "contacts": "US HMM Contracting Office",
        "submission_method": "Portal",
        "qna_deadline": "2025-07-15",
        "prebid": "",
        "prebid_required": "N/A",
        "set_aside": "None",
        "bonding": "Required",
        "insurance": "Required",
        "status": "Closed",
        "score": 55,
        "scope_summary": "Procurement of a distributed antenna system (DAS) for in-building coverage within the museum.",
        "tech_requirements": "DAS / Neutral Host, LTE/5G Cellular Backhaul"
    },

    # --- POTS / Analog ---
    {
        "title": "Indiana University Analog (POTS) Replacement – TEC-1823-2026",
        "agency": "Indiana University",
        "source": "University Procurement",
        "issue_date": "2025-08-15",
        "due_date": "2025-09-15",
        "url": "https://iu.edu/procurement/TEC-1823-2026",
        "category": "POTS Replacement / Analog Modernization",
        "budget": None,
        "contacts": "Procurement Office | purchasing@iu.edu",
        "submission_method": "Portal",
        "qna_deadline": "2025-08-28",
        "prebid": "",
        "prebid_required": "N/A",
        "set_aside": "None",
        "bonding": "Not Mentioned",
        "insurance": "Required",
        "status": "Closed",
        "score": 70,
        "scope_summary": "Replace legacy POTS lines at Indiana University with modern cellular/ATA alternatives.",
        "tech_requirements": "POTS / Analog Line Conversion, ATA Replacement"
    },
    {
        "title": "SCH POTS2025-PH1 – School City of Hammond POTS Replacement",
        "agency": "School City of Hammond, IN",
        "source": "BidNet",
        "issue_date": "2025-04-10",
        "due_date": "2025-05-09",
        "url": "https://www.bidnetdirect.com/indiana/sch-hammond",
        "category": "POTS Replacement / Elevator / Alarm",
        "budget": None,
        "contacts": "Facilities Office",
        "submission_method": "Portal",
        "qna_deadline": "2025-04-25",
        "prebid": "2025-04-20",
        "prebid_required": "Optional",
        "set_aside": "None",
        "bonding": "Required",
        "insurance": "Required",
        "status": "Closed",
        "score": 70,
        "scope_summary": "Conversion of elevator and emergency POTS lines across district buildings to cellular ATA solutions.",
        "tech_requirements": "POTS / Analog Line Conversion, Elevator/Fire/Fax Support"
    },
    {
        "title": "Licking Valley Schools – Telephone / IP System Replacement",
        "agency": "Licking Valley Local Schools, OH",
        "source": "District Procurement",
        "issue_date": "2025-02-28",
        "due_date": "2025-03-14",
        "url": "https://www.lickingvalley.k12.oh.us",
        "category": "VoIP Modernization + Analog Line Conversion",
        "budget": None,
        "contacts": "IT Director",
        "submission_method": "Physical",
        "qna_deadline": "2025-03-07",
        "prebid": "",
        "prebid_required": "N/A",
        "set_aside": "None",
        "bonding": "Not Mentioned",
        "insurance": "Required",
        "status": "Closed",
        "score": 60,
        "scope_summary": "Replacement of school phone systems with VoIP, including migration of ~10 analog devices.",
        "tech_requirements": "VoIP Modernization, POTS / Analog Line Conversion"
    },
    {
        "title": "Poquoson City Public Schools – Phone System Replacement (SBO-25-003)",
        "agency": "Poquoson City Public Schools, VA",
        "source": "Public Purchase",
        "issue_date": "2025-05-10",
        "due_date": "2025-06-06",
        "url": "https://www.publicpurchase.com",
        "category": "VoIP + Analog Line Support (Elevator, Fax, Alarm)",
        "budget": None,
        "contacts": "Procurement Office",
        "submission_method": "Portal",
        "qna_deadline": "2025-05-20",
        "prebid": "",
        "prebid_required": "N/A",
        "set_aside": "None",
        "bonding": "Required",
        "insurance": "Required",
        "status": "Closed",
        "score": 65,
        "scope_summary": "Replace phone system with VoIP while ensuring analog support for elevators, fax, and fire alarm lines.",
        "tech_requirements": "VoIP Modernization, Elevator/Fire/Fax Support"
    },
    {
        "title": "Tampa – Analog Phone Line Replacement (RFP #25-P-00272)",
        "agency": "City of Tampa, FL",
        "source": "City Procurement",
        "issue_date": "2025-09-10",
        "due_date": "2025-09-24",
        "url": "https://www.tampagov.net",
        "category": "Analog Line Replacement / POTS Modernization",
        "budget": None,
        "contacts": "City Procurement | purchasing@tampagov.net",
        "submission_method": "Portal",
        "qna_deadline": "2025-09-17",
        "prebid": "",
        "prebid_required": "N/A",
        "set_aside": "None",
        "bonding": "Required",
        "insurance": "Required",
        "status": "Open",
        "score": 55,
        "scope_summary": "Replace remaining analog phone lines in city facilities with modern cellular/ATA-based solutions.",
        "tech_requirements": "POTS / Analog Line Conversion, ATA Replacement"
    }
]

for item in rfps:
    opp_id = ingest_opportunity(item, score=item["score"])
    print(f"✅ Inserted/Updated: {item['title']} (ID={opp_id}, Status={item['status']}, Score={item['score']})")
