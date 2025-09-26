import os
import json
import sqlite3
import hashlib
from datetime import datetime

DB_FILE = "opportunities.db"

DEFAULT_KEYWORDS = [
    "DAS", "Distributed Antenna System", "Neutral Host", "Booster", "BDA", "ERRCS",
    "POTS replacement", "VoIP", "Elevator Phone", "Fire Alarm", "Monitoring",
    "5G", "Private LTE", "CBRS", "Private Networking",
    "Structured Cabling", "Fiber", "Small Cell",
    "IT Consulting", "Telecom", "Wireless"
]

DEFAULT_NAICS = [
    "517311", "517312", "517919", "517410",
    "238210", "541330", "541512", "541513", "541618"
]

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def log_event(action, details, outcome="ok", actor="system"):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO events (actor, action, details, outcome) VALUES (?,?,?,?)",
        (actor, action, details, outcome)
    )
    conn.commit()
    conn.close()

def ensure_schema_upgrade():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS source_cache (
        source TEXT,
        external_id TEXT,
        payload_json TEXT,
        fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (source, external_id)
    )
    """)
    cur.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_opps_source_external
    ON opportunities(source, external_id)
    """)
    conn.commit()
    conn.close()

def load_keywords():
    if os.path.exists("keywords.json"):
        with open("keywords.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_KEYWORDS

def load_naics():
    if os.path.exists("naics.json"):
        with open("naics.json", "r", encoding="utf-8") as f:
            return [str(x) for x in json.load(f)]
    return DEFAULT_NAICS

def normalize_external_id(source: str, url: str = "", title: str = "") -> str:
    base = (url or "") + "::" + (title or "")
    if not base.strip():
        base = f"{source}::{datetime.utcnow().isoformat()}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:32]

def upsert_cache(source: str, external_id: str, payload_json: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    INSERT OR REPLACE INTO source_cache (source, external_id, payload_json)
    VALUES (?,?,?)
    """, (source, external_id, payload_json))
    conn.commit()
    conn.close()

def upsert_opportunity(op: dict):
    """
    op keys:
      source, external_id, title, agency, issue_date, due_date, url,
      naics, keywords, est_value, status
    """
    required = ["source", "title"]
    for r in required:
        if r not in op:
            raise ValueError(f"Missing required field: {r}")

    external_id = op.get("external_id") or normalize_external_id(op["source"], op.get("url",""), op.get("title",""))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    INSERT OR IGNORE INTO opportunities
    (external_id, title, agency, source, issue_date, due_date, url, naics, keywords, est_value, status)
    VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (
        external_id,
        op.get("title"),
        op.get("agency"),
        op.get("source"),
        op.get("issue_date"),
        op.get("due_date"),
        op.get("url"),
        op.get("naics"),
        op.get("keywords"),
        op.get("est_value"),
        op.get("status", "new")
    ))
    conn.commit()
    conn.close()
    return external_id
