from app import init_db, ingest_opportunity

init_db()
record = {
    "title": "ITB 26SWS0820A – Bi-Directional Amplifier (BDA) / DAS Installation",
    "agency": "Alaska Department of Public Safety",
    "source": "Alaska Online Public Notices",
    "issue_date": "2025-09-15",
    "due_date": "2025-10-06 14:00 AKT",
    "url": "",  # paste the Online Public Notices URL if you like
    "category": "DAS / In-Building Cellular",
    "budget": None,
    "status": "Open",
    "contacts": "Kelly Pahlau | kelly.pahlau@alaska.gov | (907) 269-8493",
    "submission_method": "Electronic (email) – see ITB",
    "qna_deadline": "",
    "prebid": "None stated",
    "prebid_required": "N/A",
    "set_aside": "None",
    "bonding": "See ITB (likely required)",
    "insurance": "See ITB",
    "scope_summary": "Install public safety BDA/DAS at Rabinowitz Courthouse; provide code-compliant in-building coverage; electronic submission only; virtual opening.",
    "tech_requirements": "Public Safety DAS, BDA, Battery backup, Coverage testing",
    "external_id": "26SWS0820A"
}
opp_id = ingest_opportunity(record, score=85)
print(f"✅ Inserted ITB 26SWS0820A as opportunity ID {opp_id}")
