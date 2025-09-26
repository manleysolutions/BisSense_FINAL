import sqlite3

DB_FILE = "opportunities.db"

def main():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # --- Opportunities by source ---
    print("=== Opportunities by source ===")
    for row in cur.execute("SELECT source, COUNT(*) FROM opportunities GROUP BY source"):
        print(f"{row[0]}: {row[1]}")

    # --- Opportunities by category ---
    print("\n=== Opportunities by category ===")
    for row in cur.execute("""
        SELECT category, COUNT(*), AVG(category_weight), MAX(category_weight)
        FROM opportunities
        WHERE category IS NOT NULL
        GROUP BY category
        ORDER BY COUNT(*) DESC
    """):
        cat, count, avg_w, max_w = row
        avg_w = round(avg_w, 2) if avg_w is not None else 0
        print(f"{cat}: {count} (avg weight {avg_w}, max {max_w})")

    # --- Last 10 events ---
    print("\n=== Last 10 events ===")
    for row in cur.execute("""
        SELECT timestamp, actor, action, outcome, details
        FROM events
        ORDER BY timestamp DESC
        LIMIT 10
    """):
        print(" | ".join(str(x) for x in row))

    # --- Last 10 opportunities ---
    print("\n=== Last 10 opportunities ===")
    for row in cur.execute("""
        SELECT source, title, url, category, category_weight
        FROM opportunities
        ORDER BY id DESC
        LIMIT 10
    """):
        src, title, url, cat, weight = row
        print(f"[{src}] {title} ({cat}, weight {weight}) -> {url}")

    conn.close()

if __name__ == "__main__":
    main()
