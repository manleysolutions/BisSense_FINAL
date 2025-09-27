#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration Script — Rebuild approvals table with proper schema
Adds: decision, reason, decided_at
Ensures: opportunity_id is PRIMARY KEY
"""

import sqlite3

DB_FILE = "opportunities.db"

def main():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Get existing schema
    cur.execute("PRAGMA table_info(approvals)")
    cols = [c[1] for c in cur.fetchall()]

    needs_rebuild = False
    if "reason" not in cols or "decided_at" not in cols:
        needs_rebuild = True

    if not needs_rebuild:
        print("ℹ️ approvals table already has correct schema — no changes made.")
        conn.close()
        return

    print("⚠️ Rebuilding approvals table with new schema...")

    # Backup existing data
    cur.execute("SELECT * FROM approvals")
    rows = cur.fetchall()
    existing_cols = [c[1] for c in cur.description] if cur.description else []

    # Rename old table
    cur.execute("ALTER TABLE approvals RENAME TO approvals_old")

    # Create new approvals table
    cur.execute("""
    CREATE TABLE approvals (
        opportunity_id INTEGER PRIMARY KEY,
        decision TEXT,
        reason TEXT,
        decided_at TEXT
    )
    """)

    # Copy back old data (if compatible)
    for row in rows:
        row_dict = dict(zip(existing_cols, row))
        cur.execute("""
        INSERT OR IGNORE INTO approvals(opportunity_id, decision)
        VALUES (?, ?)
        """, (
            row_dict.get("opportunity_id"),
            row_dict.get("decision")
        ))

    # Drop old table
    cur.execute("DROP TABLE IF EXISTS approvals_old")

    conn.commit()
    conn.close()
    print("✅ approvals table rebuilt successfully with new schema.")

if __name__ == "__main__":
    main()
