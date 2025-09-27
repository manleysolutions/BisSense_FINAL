#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BidSense — Phase 2 Scoring (Evaluate + Polish)
- CTARNG-calibrated weights
- Financial filters (budget, sqft, due window, cash-flow risk)
- Competition heuristics (commodity vs specialized; pre-qual/brand lock)
- Optional profit projection using vendor baselines (if present)
- Robust to partial opportunity rows (missing cols default to None)
- Writes detailed breakdown JSON to `scores`
- Auto-updates `approvals` per thresholds with reason

Schema expectations (created if missing):
  opportunities(id INTEGER PK, title, agency, source, issue_date, due_date, url,
                category, category_weight, budget, sqft, customer_type, description, notes)
  scores(opportunity_id UNIQUE, score, breakdown, updated_at)
  approvals(opportunity_id UNIQUE, decision, reason, decided_at)

External, optional files:
  scoring_config.json           -> override weights/thresholds
  data/vendors_baseline.json    -> cost/markup baselines for profit calc
"""

import os
import json
import math
import sqlite3
from datetime import datetime, timedelta

DB_FILE = os.environ.get("BIDSENSE_DB", "opportunities.db")
CONFIG_FILE = os.environ.get("BIDSENSE_SCORING_CONFIG", "scoring_config.json")
VENDOR_BASELINE_FILE = os.environ.get("BIDSENSE_VENDOR_BASELINES", os.path.join("data", "vendors_baseline.json"))

# -----------------------------
# Defaults (override via CONFIG)
# -----------------------------
DEFAULT_CFG = {
    "ctarng_anchor": {
        # Target score band for “core + strategic” like CTARNG DAS
        "min": 70, "max": 90
    },
    "weights": {
        "base": 0,
        "category_core_bonus": 30,      # DAS / RTL / POTS-replacement
        "strategic_customer_bonus": 20, # .gov/.edu/.mil or Government/Education/Military
        "less_competition_bonus": 10,   # heuristic bump if signals show niche/specialized
        "commodity_penalty": -25,       # commodity IT (laptops, printers, generic routers)
        "brandlock_penalty": -15,       # “brand X only”, “pre-qualified list”, sole source
        "due_window_good": 10,          # >= 20 days to due date
        "due_window_rush": -10,         # < 10 days to due date
        "budget_big_bonus": 25,         # budget >= 250k or sqft >= 100k
        "budget_small_penalty": -10,    # budget < 25k
        "cashflow_gov_bonus": 15,       # Gov/Edu/Mil
        "cashflow_enterprise_bonus": 5, # Healthcare / Enterprise (safer than startup)
        "profit_strong_bonus": 10,      # margin >= 25%
        "profit_thin_penalty": -10      # margin < 10%
    },
    "thresholds": {
        "auto_select": 70, # >= → Select to Bid
        "hold_min": 50     # [50..69] → Hold; else Ignore
    },
    "core_categories": ["DAS", "RTL", "POTS", "POTS/Telephony", "Elevators/Emergency Phones", "Fire Alarm Monitoring"],
    "commodity_keywords": [
        "laptop","notebook","desktop","printer","toner","monitor","keyboard","mouse",
        "chromebook","pc refresh","end user device","office supplies","copier"
    ],
    "brandlock_keywords": [
        "sole source","only brand","brand x only","pre-qualified vendor","prequalified vendor",
        "authorized reseller only","incumbent only","must be OEM"
    ],
    "less_competition_positive": [
        "distributed antenna system","public safety das","bdas","bi-directional amplifier",
        "pots replacement","fxs","analog lines replacement","emergency phone","elevator phone",
        "fire alarm communicator","ng911","lmr","rf engineering","lmr600","lmr400"
    ],
    "auto_approval_rules": [
        # Example: keep the Manhattan Beach USD DAS demo behavior
        {"match_title": "Manhattan Beach", "match_category": "DAS", "decision": "Select to Bid", "reason": "Demo rule: MBUSD DAS auto-select"}
    ],
    "due_window_days_good": 20,
    "due_window_days_rush": 10,
    "big_job_budget_min": 250000,
    "big_job_sqft_min": 100000,
    "small_job_budget_max": 25000
}

# -----------------------------
# Utilities
# -----------------------------
def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_tables(conn):
    cur = conn.cursor()
    # Create scores
    cur.execute("""
    CREATE TABLE IF NOT EXISTS scores (
        opportunity_id INTEGER PRIMARY KEY,
        score REAL,
        breakdown TEXT,
        updated_at TEXT
    )
    """)
    # Create approvals
    cur.execute("""
    CREATE TABLE IF NOT EXISTS approvals (
        opportunity_id INTEGER PRIMARY KEY,
        decision TEXT,         -- 'Select to Bid' | 'Hold' | 'Ignore'
        reason TEXT,
        decided_at TEXT
    )
    """)
    conn.commit()

def load_json_if_exists(path, default=None):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default

def merged_config():
    cfg = json.loads(json.dumps(DEFAULT_CFG))  # deep copy
    user = load_json_if_exists(CONFIG_FILE, {})
    if isinstance(user, dict):
        # shallow/partial merge adequate for our keys
        for k, v in user.items():
            if isinstance(v, dict) and k in cfg and isinstance(cfg[k], dict):
                cfg[k].update(v)
            else:
                cfg[k] = v
    return cfg

def fields(row):
    """Return dict of row with missing keys defaulting to None (robust to missing columns)."""
    d = {k: row[k] for k in row.keys()}
    # Ensure expected keys exist
    for k in ["id","title","agency","source","issue_date","due_date","url",
              "category","category_weight","budget","sqft","customer_type","description","notes","keywords"]:
        d.setdefault(k, None)
    return d

def parse_float(x):
    try:
        if x is None: return None
        if isinstance(x, (int,float)): return float(x)
        s = str(x).replace("$","").replace(",","").strip()
        return float(s) if s else None
    except Exception:
        return None

def parse_int(x):
    try:
        if x is None: return None
        if isinstance(x, (int,float)): return int(x)
        s = str(x).replace(",","").strip()
        return int(s) if s else None
    except Exception:
        return None

def parse_date(s):
    """Try several common formats; return datetime or None."""
    if not s:
        return None
    if isinstance(s, (datetime,)):
        return s
    if isinstance(s, (int,float)):
        # epoch?
        try: return datetime.fromtimestamp(float(s))
        except Exception: pass
    txt = str(s).strip()
    fmts = [
        "%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y",
        "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ"
    ]
    for f in fmts:
        try:
            return datetime.strptime(txt, f)
        except Exception:
            continue
    # last resort: try to pull digits
    try:
        return datetime.fromisoformat(txt)
    except Exception:
        return None

def days_until(due_dt):
    if not due_dt:
        return None
    today = datetime.now()
    return (due_dt - today).days

def text_blob(d):
    parts = []
    for k in ("title","agency","source","description","notes","keywords"):
        v = d.get(k)
        if v: parts.append(str(v))
    return " ".join(parts).lower()

def contains_any(txt, keywords):
    return any(kw.lower() in txt for kw in keywords)

def strategic_customer(d):
    # Signal from customer_type or domains in agency/source
    ct = (d.get("customer_type") or "").lower()
    if ct in ("government","gov","education","edu","military","federal","state","local"):
        return True
    ag = (d.get("agency") or "").lower()
    src = (d.get("source") or "").lower()
    for needle in (".gov",".edu",".mil","county","city of","unified school","school district","usd","state of ","department of"):
        if needle in ag or needle in src:
            return True
    return False

def category_is_core(d, core_categories):
    cat = (d.get("category") or "").strip().upper()
    for c in core_categories:
        if c.upper() in cat:
            return True
    # heuristic: title mentions
    t = (d.get("title") or "").lower()
    if "distributed antenna" in t or "das" in t or "pots" in t or "elevator" in t or "fire alarm" in t:
        return True
    return False

def load_vendor_baselines():
    data = load_json_if_exists(VENDOR_BASELINE_FILE, None)
    # Example structure:
    # {
    #   "DAS": {"baseline_cost_per_sqft": 4.50, "markup": 1.35},
    #   "RTL": {"baseline_cost_per_line": 120, "markup": 1.50}
    # }
    return data or {}

def estimate_profit(d, baselines):
    """Return (revenue, cost, margin_ratio) or (None,None,None) if insufficient data."""
    category = (d.get("category") or "").upper()
    budget = parse_float(d.get("budget"))
    sqft   = parse_int(d.get("sqft"))
    # Choose a baseline family
    base = None
    for key in baselines.keys():
        if key.upper() in category:
            base = baselines[key]
            break
    if not base:
        # try heuristics
        if "DAS" in category:
            base = {"baseline_cost_per_sqft": 4.50, "markup": 1.35}
        elif "RTL" in category or "POTS" in category:
            base = {"baseline_cost_per_line": 120, "markup": 1.50}
        else:
            return (None, None, None)

    markup = float(base.get("markup", 1.35))

    # If explicit budget exists, assume that's the revenue;
    # otherwise estimate from sqft if possible.
    if budget and budget > 0:
        revenue = budget
        # Reverse-engineer an implied cost if we have a typical markup
        cost = revenue / markup if markup > 1.0 else revenue * 0.8
    elif sqft and "baseline_cost_per_sqft" in base:
        unit = float(base["baseline_cost_per_sqft"])
        cost = unit * sqft
        revenue = cost * markup
    else:
        return (None, None, None)

    if revenue <= 0 or cost <= 0:
        return (None, None, None)

    margin_ratio = (revenue - cost) / revenue
    return (revenue, cost, margin_ratio)

# -----------------------------
# Scoring Core
# -----------------------------
def score_row(d, cfg, baselines):
    w = cfg["weights"]
    text = text_blob(d)

    breakdown = []
    score = w["base"]

    # Core category bonus (CTARNG-style anchor)
    is_core = category_is_core(d, cfg["core_categories"])
    if is_core:
        score += w["category_core_bonus"]
        breakdown.append(["category_core_bonus", w["category_core_bonus"]])

    # Strategic customer bonus
    is_strategic = strategic_customer(d)
    if is_strategic:
        score += w["strategic_customer_bonus"]
        breakdown.append(["strategic_customer_bonus", w["strategic_customer_bonus"]])

    # Competition heuristics
    if contains_any(text, cfg["commodity_keywords"]):
        score += w["commodity_penalty"]
        breakdown.append(["commodity_penalty", w["commodity_penalty"]])
    if contains_any(text, cfg["brandlock_keywords"]):
        score += w["brandlock_penalty"]
        breakdown.append(["brandlock_penalty", w["brandlock_penalty"]])
    if contains_any(text, cfg["less_competition_positive"]):
        score += w["less_competition_bonus"]
        breakdown.append(["less_competition_bonus", w["less_competition_bonus"]])

    # Financial filters
    due_dt = parse_date(d.get("due_date"))
    days = days_until(due_dt) if due_dt else None
    if days is not None:
        if days >= cfg["due_window_days_good"]:
            score += w["due_window_good"]
            breakdown.append(["due_window_good", w["due_window_good"]])
        elif days < cfg["due_window_days_rush"]:
            score += w["due_window_rush"]
            breakdown.append(["due_window_rush", w["due_window_rush"]])

    budget = parse_float(d.get("budget"))
    sqft = parse_int(d.get("sqft"))
    if budget is not None and budget >= cfg["big_job_budget_min"]:
        score += w["budget_big_bonus"]
        breakdown.append(["budget_big_bonus", w["budget_big_bonus"]])
    if sqft is not None and sqft >= cfg["big_job_sqft_min"]:
        score += w["budget_big_bonus"]
        breakdown.append(["sqft_big_bonus", w["budget_big_bonus"]])
    if budget is not None and budget < cfg["small_job_budget_max"]:
        score += w["budget_small_penalty"]
        breakdown.append(["budget_small_penalty", w["budget_small_penalty"]])

    # Cash-flow risk by customer type
    ct = (d.get("customer_type") or "").lower()
    if ct in ("government","gov","education","edu","military","federal","state","local","county","city"):
        score += w["cashflow_gov_bonus"]
        breakdown.append(["cashflow_gov_bonus", w["cashflow_gov_bonus"]])
    elif ct in ("enterprise","healthcare","hospital","payer","provider"):
        score += w["cashflow_enterprise_bonus"]
        breakdown.append(["cashflow_enterprise_bonus", w["cashflow_enterprise_bonus"]])

    # Profit projection (if baselines present or inferable)
    revenue, cost, margin_ratio = estimate_profit(d, baselines)
    profit_note = None
    if margin_ratio is not None:
        if margin_ratio >= 0.25:
            score += w["profit_strong_bonus"]
            breakdown.append(["profit_strong_bonus", w["profit_strong_bonus"]])
            profit_note = f"strong margin ~{round(margin_ratio*100)}%"
        elif margin_ratio < 0.10:
            score += w["profit_thin_penalty"]
            breakdown.append(["profit_thin_penalty", w["profit_thin_penalty"]])
            profit_note = f"thin margin ~{round(margin_ratio*100)}%"

    # Round for neatness
    score = round(float(score), 2)

    # Build breakdown JSON
    bd = {
        "inputs": {
            "id": d.get("id"),
            "title": d.get("title"),
            "agency": d.get("agency"),
            "source": d.get("source"),
            "due_date": d.get("due_date"),
            "category": d.get("category"),
            "category_weight": d.get("category_weight"),
            "budget": budget,
            "sqft": sqft,
            "customer_type": d.get("customer_type")
        },
        "flags": {
            "is_core": is_core,
            "is_strategic": is_strategic,
            "days_until_due": days
        },
        "profit_estimate": {
            "revenue": round(revenue,2) if revenue else None,
            "cost": round(cost,2) if cost else None,
            "margin_ratio": round(margin_ratio,3) if margin_ratio is not None else None,
            "note": profit_note
        },
        "components": breakdown,
        "final_score": score
    }
    return score, bd

def auto_approval_for(d, score, cfg):
    # explicit rule wins first
    for rule in cfg.get("auto_approval_rules", []):
        tmatch = (rule.get("match_title") or "").lower()
        cmatch = (rule.get("match_category") or "").lower()
        if (not tmatch or tmatch in (d.get("title") or "").lower()) and \
           (not cmatch or cmatch in (d.get("category") or "").lower()):
            return rule.get("decision","Select to Bid"), rule.get("reason","Auto-rule")

    # thresholds
    if score >= cfg["thresholds"]["auto_select"]:
        return "Select to Bid", f"Score {score} ≥ {cfg['thresholds']['auto_select']}"
    if score >= cfg["thresholds"]["hold_min"]:
        return "Hold", f"Score {score} in [{cfg['thresholds']['hold_min']}, {cfg['thresholds']['auto_select']-1}]"
    return "Ignore", f"Score {score} < {cfg['thresholds']['hold_min']}"

# -----------------------------
# Main
# -----------------------------
def main():
    cfg = merged_config()
    baselines = load_vendor_baselines()

    conn = get_conn()
    ensure_tables(conn)

    cur = conn.cursor()
    cur.execute("SELECT * FROM opportunities ORDER BY id DESC")
    rows = cur.fetchall()

    now = datetime.utcnow().isoformat()

    scored = 0
    for row in rows:
        d = fields(row)
        # Score it
        score, breakdown = score_row(d, cfg, baselines)

        # Upsert into scores
        cur.execute("""
        INSERT INTO scores(opportunity_id, score, breakdown, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(opportunity_id) DO UPDATE SET
            score=excluded.score,
            breakdown=excluded.breakdown,
            updated_at=excluded.updated_at
        """, (d["id"], score, json.dumps(breakdown, ensure_ascii=False), now))

        # Decide approval
        decision, reason = auto_approval_for(d, score, cfg)
        cur.execute("""
        INSERT INTO approvals(opportunity_id, decision, reason, decided_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(opportunity_id) DO UPDATE SET
            decision=excluded.decision,
            reason=excluded.reason,
            decided_at=excluded.decided_at
        """, (d["id"], decision, reason, now))

        scored += 1

    conn.commit()
    conn.close()

    print(f"✅ Scored {scored} opportunities. Updated scores + approvals.")

if __name__ == "__main__":
    main()
