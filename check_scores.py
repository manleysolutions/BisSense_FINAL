import sqlite3
import argparse
from tabulate import tabulate

DB_FILE = "opportunities.db"

# ANSI color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
GRAY = "\033[90m"
RESET = "\033[0m"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-score", type=int, default=0, help="Minimum score filter")
    parser.add_argument("--limit", type=int, default=10, help="Max rows to display")
    parser.add_argument("--auto-only", action="store_true", help="Show only auto-decided opportunities")
    args = parser.parse_args()

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT o.id, o.title, o.agency, o.due_date, o.source,
               s.score, s.reasons,
               a.decision, a.reviewer, a.decided_at, a.notes
        FROM opportunities o
        JOIN scores s ON o.id = s.opportunity_id
        LEFT JOIN approvals a ON o.id = a.opportunity_id
        WHERE s.score >= ?
        GROUP BY o.id
        ORDER BY s.score DESC
        LIMIT ?
    """, (args.min_score, args.limit))

    rows = cur.fetchall()
    if not rows:
        print("⚠️ No opportunities found with current filters.")
        return

    table = []
    for row in rows:
        decision = row["decision"] or "Pending"
        reviewer = row["reviewer"] or ""
        notes = row["notes"] or ""

        # Skip non-auto if filtering
        if args.auto_only and reviewer != "AUTO":
            continue

        # Apply color coding
        if reviewer == "AUTO":
            if decision.lower() == "approved":
                decision = f"{GREEN}{decision} [AUTO]{RESET}"
            elif decision.lower() == "rejected":
                decision = f"{RED}{decision} [AUTO]{RESET}"
            elif decision.lower() == "hold":
                decision = f"{YELLOW}{decision} [AUTO]{RESET}"
        elif decision == "Pending":
            decision = f"{GRAY}{decision}{RESET}"

        table.append([
            row["id"],
            (row["title"] or "")[:65] + ("..." if len(row["title"] or "") > 65 else ""),
            row["agency"] or "",
            row["due_date"] or "",
            row["source"] or "",
            row["score"],
            row["reasons"] or "",
            decision,
            reviewer,
            row["decided_at"] or "",
            notes
        ])

    if not table:
        print("⚠️ No opportunities matched your filters.")
        return

    headers = ["ID", "Title", "Agency", "Due Date", "Source", "Score", "Reasons", "Decision", "Reviewer", "Decided At", "Notes"]
    print(tabulate(table, headers=headers, tablefmt="fancy_grid"))

if __name__ == "__main__":
    main()
