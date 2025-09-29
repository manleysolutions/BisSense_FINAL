import sqlite3
from app import ingest_opportunity, init_db, get_db

# ✅ Ensure DB initialized
init_db()

# --------------------------
# Master RFP Opportunity Data
# --------------------------
opportunities = [
    # -------------------
    # ✅ DAS Opportunities
    # -------------------
    {
        "title": "Neutral DAS – US Holocaust Memorial Museum (95476725R1060)",
        "agency": "US Holocaust Memorial Museum",
        "source": "SAM.gov",
        "issue_date": "2025-08-01",
        "due_date": "2025-08-01 12:00 EST",
        "url": "https://sam.gov/opp/95476725R1060",
        "category": "DAS / Neutral Host / In-Building Cellular",
        "budget": None,
        "status": "Open",
        "contacts": "Contracts Dept | contracts@ushmm.gov | 202-555-0145",
        "submission_method": "SAM.gov",
        "qna_deadline": "2025-07-15",
        "prebid": "Virtual Pre-bid",
        "prebid_required": "Optional",
        "set_aside": "None",
        "bonding": "Not Mentioned",
        "insurance": "Required",
        "scope_summary": "Procurement of a distributed antenna system (DAS) for in-building coverage within USHMM facilities.",
        "tech_requirements": "DAS, Neutral Host, Public Safety",
        "external_id": "95476725R1060"
    },
    {
        "title": "Neutral Host DAS – Austin Convention Center (RFQS 8200 PLS4005)",
        "agency": "City of Austin Convention Center Department",
        "source": "BidNet",
        "issue_date": "2025-09-11",
        "due_date": "2025-09-11 17:00 CST",
        "url": "https://austintexas.gov/bid/8200PLS4005",
        "category": "DAS / Neutral Host / In-Building Cellular",
        "budget": None,
        "status": "Open",
        "contacts": "Purchasing Office | purchasing@austin.gov | 512-974-2000",
        "submission_method": "BidNet",
        "qna_deadline": "2025-09-05",
        "prebid": "Pre-bid Meeting – Austin Convention Center",
        "prebid_required": "Mandatory",
        "set_aside": "None",
        "bonding": "Required",
        "insurance": "Required",
        "scope_summary": "Design, deploy, and maintain a neutral host DAS across the Austin Convention Center facilities.",
        "tech_requirements": "DAS, Neutral Host, LTE/5G, Public Safety",
        "external_id": "RFQS8200PLS4005"
    },

    # -------------------------
    # ✅ POTS Replacement Opps
    # -------------------------
    {
        "title": "Indiana University Analog (POTS) Replacement – TEC-1823-2026",
        "agency": "Indiana University",
        "source": "University Procurement",
        "issue_date": "2025-08-15",
        "due_date": "2025-09-15",
        "url": "https://iu.edu/bid/TEC1823-2026",
        "category": "POTS Replacement / Analog Modernization",
        "budget": None,
        "status": "Open",
        "contacts": "IU Procurement | procurement@iu.edu | 812-555-8899",
        "submission_method": "University Portal",
        "qna_deadline": "2025-08-25",
        "prebid": "Optional Pre-bid",
        "prebid_required": "Optional",
        "set_aside": "None",
        "bonding": "Required",
        "insurance": "Required",
        "scope_summary": "Replace legacy POTS lines at Indiana University with cellular-based POTS replacement solutions for alarms, elevators, and fax machines.",
        "tech_requirements": "Cellular POTS, FXS/ATA, Battery Backup",
        "external_id": "TEC1823-2026"
    },
    {
        "title": "Poquoson City Public Schools – Phone System Replacement (SBO-25-003)",
        "agency": "Poquoson City Public Schools, VA",
        "source": "BidNet",
        "issue_date": "2025-05-20",
        "due_date": "2025-06-06",
        "url": "https://poquoson.k12.va.us/bids/SBO-25-003",
        "category": "VoIP + Analog Line Support (Elevator, Fax, Alarm)",
        "budget": None,
        "status": "Closed",
        "contacts": "IT Dept | it@poquoson.k12.va.us | 757-868-3000",
        "submission_method": "BidNet",
        "qna_deadline": "2025-05-30",
        "prebid": "On-site Pre-bid Meeting",
        "prebid_required": "Mandatory",
        "set_aside": "Small Business",
        "bonding": "Required",
        "insurance": "Required",
        "scope_summary": "Replace phone system with VoIP while ensuring analog support for elevators, fax, and alarms.",
        "tech_requirements": "POTS Replacement, VoIP, ATA, Alarm Support",
        "external_id": "SBO-25-003"
    },

    # -------------------------
    # ✅ Closed / Historical Matches
    # -------------------------
    {
        "title": "Licking Valley Schools – Telephone / IP System Replacement",
        "agency": "Licking Valley Local Schools, OH",
        "source": "District Procurement",
        "issue_date": "2025-03-01",
        "due_date": "2025-03-14",
        "url": "",
        "category": "VoIP Modernization + Analog Line Conversion",
        "budget": None,
        "status": "Closed",
        "contacts": "Tech Services | tech@lvschools.org | 740-555-1212",
        "submission_method": "Physical",
        "qna_deadline": None,
        "prebid": "Optional Pre-bid",
        "prebid_required": "Optional",
        "set_aside": "None",
        "bonding": "Required",
        "insurance": "Required",
        "scope_summary": "Replacement of school phone systems with VoIP, including migration of ~10 analog alarm/fax lines.",
        "tech_requirements": "VoIP, Analog Line Conversion",
        "external_id": "TEC-2025-LV"
    },
    {
        "title": "School City of Hammond POTS Replacement – SCH POTS2025-PH1",
        "agency": "School City of Hammond, IN",
        "source": "District Procurement",
        "issue_date": "2025-05-01",
        "due_date": "2025-05-09",
        "url": "",
        "category": "POTS Replacement / Elevator / Alarm",
        "budget": None,
        "status": "Closed",
        "contacts": "Facilities Office | facilities@hammondschools.org | 219-555-8877",
        "submission_method": "Physical",
        "qna_deadline": None,
        "prebid": "On-site",
        "prebid_required": "Mandatory",
        "set_aside": "None",
        "bonding": "Required",
        "insurance": "Required",
        "scope_summary": "Conversion of elevator and emergency POTS lines across district buildings to cellular replacements.",
        "tech_requirements": "Cellular POTS, ATA, Alarm Line Support",
        "external_id": "SCH-PH1-2025"
    }
]

# --------------------------
# Insert with dedup safeguard
# --------------------------
def seed_data():
    conn = get_db()
    cur = conn.cursor()

    for item in opportunities:
        cur.execute("SELECT 1 FROM opportunities WHERE external_id=?", (item["external_id"],))
        if cur.fetchone():
            print(f"⚠️ Skipped duplicate: {item['title']} ({item['external_id']})")
            continue
        try:
            opp_id = ingest_opportunity(item, score=70)
            print(f"✅ Inserted {item['title']} (ID={opp_id})")
        except Exception as e:
            print(f"❌ Error inserting {item['title']}: {e}")

    conn.close()

if __name__ == "__main__":
    seed_data()
