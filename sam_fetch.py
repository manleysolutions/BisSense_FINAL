import os
import time
import json
import requests
import sqlite3
from datetime import datetime, timedelta, timezone

DB_FILE = "opportunities.db"
SAM_API_KEY = "0cGGojN1E9aR8PGs2GbAvgeIVqxQnjlFZwPBIS1w"  # your key
BASE_URL = "https://api.sam.gov/prod/opportunities/v1/search"


def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def log_event(action, details, outcome="ok", actor="system"):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO events (actor, action, details, outcome) VALUES (?,?,?,?)",
        (actor, action, details, outcome),
    )
    conn.commit()
    conn.close()


def fetch_sam_opportunities(days_back=30, limit=10):
    """Fetch opportunities from SAM.gov within date range."""
    params = {
        "api_key": SAM_API_KEY,
        "postedFrom": (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime(
            "%m/%d/%Y"
        ),
        "postedTo": datetime.now(timezone.utc).strftime("%m/%d/%Y"),
        "ptype": "o",
        "limit": limit,
        "offset": 0,
    }

    print("DEBUG: Fetching from SAM.gov with params:", params)

    try:
        resp = requests.get(BASE_URL, params=params, timeout=30)
        print("DEBUG: HTTP status:", resp.status_code)

        if resp.status_code == 200:
            return resp.json()
        else:
            print("DEBUG: Response text:", resp.text[:500])
            log_event("fetch", f"HTTP {resp.status_code}", "error")
            return None
    except Exception as e:
        log_event("fetch", str(e), "error")
        print("❌ Exception:", str(e))
        return None


def upsert_opportunity(op, source="SAM.gov"):
    conn = get_db()
    cur = conn.cursor()

    external_id = op.get("noticeId", "")
    title = op.get("title", "")
    agency = op.get("agency", "")
    url = op.get("uiLink", "")
    issue_date = op.get("publishDate", "")
    due_date = op.get("responseDeadLine", "")
    naics = op.get("naics", "")
    keywords = ",".join(op.get("keywords", [])) if op.get("keywords") else ""
    est_value = None

    # Cache payload
    cur.execute(
        "INSERT OR REPLACE INTO sam_cache (external_id, payload_json) VALUES (?,?)",
        (external_id, json.dumps(op)),
    )

    # Dedup insert
    cur.execute(
        """
        INSERT OR IGNORE INTO opportunities
        (external_id, title, agency, source, issue_date, due_date, url, naics, keywords, est_value, status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            external_id,
            title,
            agency,
            source,
            issue_date,
            due_date,
            url,
            naics,
            keywords,
            est_value,
            "new",
        ),
    )

    conn.commit()
    conn.close()


def run_fetch():
    data = fetch_sam_opportunities()
    if not data:
        log_event("fetch", "No data returned", "fail")
        print("❌ No data returned from API")
        return

    print("DEBUG: Top-level JSON keys:", list(data.keys()))

    results = data.get("opportunitiesData", [])
    print("DEBUG: opportunitiesData length:", len(results))

    if not results:
        print("DEBUG: Raw JSON sample:", json.dumps(data, indent=2)[:1000])
        log_event("fetch", "Zero results returned", "empty")
        return

    inserted = 0
    for op in results:
        upsert_opportunity(op)
        inserted += 1

    log_event("fetch", f"Inserted {inserted} opportunities", "success")
    print(f"✅ Fetch complete. Inserted {inserted} opportunities.")


if __name__ == "__main__":
    run_fetch()
