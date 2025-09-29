import sqlite3

DB_FILE = "opportunities.db"

DDL = [
    "ALTER TABLE opportunities ADD COLUMN summary TEXT",
    "ALTER TABLE opportunities ADD COLUMN poc TEXT",
    "ALTER TABLE opportunities ADD COLUMN location TEXT",
    "ALTER TABLE opportunities ADD COLUMN terms TEXT",
    "ALTER TABLE opportunities ADD COLUMN critical_reqs TEXT",
    "ALTER TABLE opportunities ADD COLUMN budget_published REAL",
    "ALTER TABLE opportunities ADD COLUMN solicitation_id TEXT",
    "ALTER TABLE opportunities ADD COLUMN source_url TEXT",

    # Financial scaffolding you’ll edit on the detail page
    "ALTER TABLE opportunities ADD COLUMN cost_equipment REAL",
    "ALTER TABLE opportunities ADD COLUMN cost_labor REAL",
    "ALTER TABLE opportunities ADD COLUMN cost_admin REAL",
    "ALTER TABLE opportunities ADD COLUMN margin_target REAL",
]

def column_exists(conn, table, name):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall()]
    return name in cols

def main():
    conn = sqlite3.connect(DB_FILE)
    for sql in DDL:
        table = "opportunities"
        col = sql.split("ADD COLUMN")[1].strip().split()[0]
        if not column_exists(conn, table, col):
            try:
                conn.execute(sql)
            except Exception as e:
                print("Skip/exists:", sql, "->", e)
    conn.commit()
    conn.close()
    print("✅ migration complete")

if __name__ == "__main__":
    main()
