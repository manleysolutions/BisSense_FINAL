import json
import sqlite3

DB_FILE = "opportunities.db"
TRAINING_FILE = "rfp_training.jsonl"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def seed_training():
    conn = get_db()
    cur = conn.cursor()

    with open(TRAINING_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)

            # Insert into opportunities
            cur.execute("""
                INSERT INTO opportunities 
                (title, agency, source, issue_date, due_date, url, category, budget, status,
                 contacts, submission_method, qna_deadline, prebid, prebid_required, set_aside,
                 bonding, insurance, scope_summary, tech_requirements, external_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.get("title"),
                item.get("agency"),
                "Training Dataset",
                item.get("issue_date"),
                item.get("due_date"),
                "",
                item.get("category"),
                item.get("budget"),
                "Open",
                item.get("contacts"),
                item.get("submission_method"),
                item.get("qna_deadline"),
                item.get("prebid"),
                item.get("prebid_required"),
                item.get("set_aside"),
                item.get("bonding"),
                item.get("insurance"),
                item.get("scope_summary"),
                ", ".join(item.get("tech_requirements")) if isinstance(item.get("tech_requirements"), list) else item.get("tech_requirements"),
                item.get("id")
            ))
            opp_id = cur.lastrowid

            # Insert evaluation factors into scores (if numeric weighting exists)
            if "evaluation_factors" in item and isinstance(item["evaluation_factors"], dict):
                total_score = sum(item["evaluation_factors"].values())
                cur.execute("INSERT INTO scores (opp_id, score) VALUES (?, ?)", (opp_id, total_score))

    conn.commit()
    conn.close()
    print("✅ Training dataset seeded successfully!")

if __name__ == "__main__":
    seed_training()
