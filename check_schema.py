import sqlite3

DB_FILE = "opportunities.db"

def main():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    print("=== Tables in DB ===")
    tables = [row[0] for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table';")]
    for t in tables:
        print(f"- {t}")

    print("\n=== Columns per Table ===")
    for t in tables:
        print(f"\nTable: {t}")
        for col in cur.execute(f"PRAGMA table_info({t});"):
            cid, name, ctype, notnull, dflt, pk = col
            print(f"  {name} ({ctype}){' PRIMARY KEY' if pk else ''}")

    conn.close()

if __name__ == "__main__":
    main()
