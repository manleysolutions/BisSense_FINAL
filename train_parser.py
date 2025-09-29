import sqlite3
import json

DB_FILE = "opportunities.db"
OUTPUT_FILE = "training_data.json"

def export_training_data():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Collect opportunities with corrections
    cur.execute("""
        SELECT o.id, o.title, o.agency, o.category, o.scope_summary,
               c.field, c.parsed_value, c.corrected_value
        FROM opportunities o
        LEFT JOIN corrections c ON o.id = c.opp_id
        ORDER BY o.id
    """)
    rows = cur.fetchall()
    conn.close()

    training_set = {}
    for row in rows:
        opp_id = row["id"]
        if opp_id not in training_set:
            training_set[opp_id] = {
                "title": row["title"],
                "agency": row["agency"],
                "category": row["category"],
                "scope_summary": row["scope_summary"],
                "corrections": []
            }
        if row["field"]:
            training_set[opp_id]["corrections"].append({
                "field": row["field"],
                "parsed": row["parsed_value"],
                "corrected": row["corrected_value"]
            })

    with open(OUTPUT_FILE, "w") as f:
        json.dump(list(training_set.values()), f, indent=2)

    print(f"✅ Exported {len(training_set)} training examples to {OUTPUT_FILE}")

if __name__ == "__main__":
    export_training_data()
