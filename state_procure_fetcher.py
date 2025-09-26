import requests
import sqlite3
import time
from bs4 import BeautifulSoup
import re

DB_FILE = "opportunities.db"
KEYWORDS = [
    "DAS", "Distributed Antenna System", "Neutral Host", "Booster",
    "VOIP", "Elevator Phone Service", "Fire Alarm Monitoring",
    "5G", "Private Networking", "Structured Cabling", "IT Consulting"
]

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def log_event(action, details, outcome="ok", actor="state_fetcher"):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO events (actor, action, details, outcome) VALUES (?,?,?,?)",
        (actor, action, details, outcome)
    )
    conn.commit()
    conn.close()

def parse_state_site(url):
    """
    Example scraping: fetch the state procurement listing HTML, find links, titles, dates.
    This needs to be customized per portal.
    """
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    items = []
    # This is heuristic: find <a> tags with “RFP” or “Request for Proposal”
    for a in soup.find_all("a", href=True):
        text = a.get_text().strip()
        href = a["href"]
        if re.search(r"\bRFP\b|\bRequest for Proposal\b", text, re.IGNORECASE):
            # full URL
            link = href if href.startswith("http") else (url.rstrip("/") + "/" + href.lstrip("/"))
            items.append({
                "title": text,
                "url": link
            })
    return items

def keyword_filter(item):
    title = item.get("title", "")
    for kw in KEYWORDS:
        if kw.lower() in title.lower():
            return True
    return False

def upsert_state_opportunity(item, source="StatePortal"):
    conn = get_db()
    cur = conn.cursor()

    external_id = item.get("url", "")
    title = item.get("title", "")
    agency = source
    issue_date = None
    due_date = None
    naics = None
    keywords = title  # store title as “keywords” field

    # Insert / dedupe via external_id
    cur.execute(
        "INSERT OR IGNORE INTO opportunities (external_id, title, agency, source, issue_date, due_date, url, naics, keywords, status) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (external_id, title, agency, source, issue_date, due_date, external_id, naics, keywords, "new")
    )

    conn.commit()
    conn.close()

def run_state_fetch():
    # Example: Nebraska procurement site (you’ll replace with your actual target)
    target_url = "https://das.nebraska.gov/materiel/bid-opportunities.html"
    try:
        items = parse_state_site(target_url)
        matched = [it for it in items if keyword_filter(it)]
        inserted = 0
        for it in matched:
            upsert_state_opportunity(it)
            inserted += 1
        log_event("state_fetch", f"Processed {len(items)} items, matched {inserted}", "success")
        print(f"✅ State fetch: matched & inserted {inserted}")
    except Exception as e:
        log_event("state_fetch", str(e), "error")
        print("❌ State fetch error:", e)

if __name__ == "__main__":
    run_state_fetch()
