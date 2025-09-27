#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration Script — Rebuild scores table with proper UNIQUE constraint
"""

import sqlite3

DB_FILE = "opportunities.db"

def main():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Check if opportunity_id already exists with UNIQUE/PK
    cur.execute("PRAGMA table_info(scores)")
    cols = cur.fetchall()
    colnames = [c[1] for c in cols]

    # Does opportunity_id already exist properly?
    cur.execute("PRAGMA index_list(scores)")
    idxs = cur.fetchall()
    has_unique = any("opportunity_id" in str(i) and i[2] for i in idxs)

    if has_unique:
        print("ℹ️ scores.opportunity_id already has a UNIQUE/PK constraint — no rebuild needed.")
        conn.close()
        return

    print("⚠️ Rebuilding scores table with UNIQUE constraint on opportunity_id...")

    # Backup data if it exists
    cur.execute("SELECT * FROM scores")
    rows = cur.fetchall()

    # Get columns
    cur.execute("PRAGMA table_info(scores)")
    existing_cols = [c[1] for c in cur.fetchall()]

    # Rename old table
    cur.execute("ALTER TABLE scores RENAME TO scores_old")

    # Create new scores table with constraint
    cur.execute("""
    CREATE TABLE scores (
        opportunity_id INTEGER PRIMARY KEY,
        score REAL,
        breakdown TEXT,
        updated_at TEXT
    )
    """)

    # Copy data back (if compatible)
    for row in rows:
        row_dict = dict(zip(existing_cols, row))
        cur.execute("""
        INSERT OR IGNORE INTO scores(opportunity_id, score, breakdown, updated_at)
        VALUES (?, ?, ?, ?)
        """, (
            row_dict.get("opportunity_id"),
            row_dict.get("score"),
            row_dict.get("breakdown"),
            row_dict.get("updated_at"),
        ))

    # Drop old table
    cur.execute("DROP TABLE IF EXISTS scores_old")

    conn.commit()
    conn.close()
    print("✅ scores table rebuilt successfully with UNIQUE opportunity_id.")

if __name__ == "__main__":
    main()
