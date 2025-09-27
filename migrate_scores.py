#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration Script — Fix scores table to include 'breakdown' and 'updated_at'
"""

import sqlite3

DB_FILE = "opportunities.db"

def main():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Get existing schema for scores table
    cur.execute("PRAGMA table_info(scores)")
    cols = [row[1] for row in cur.fetchall()]

    if "breakdown" not in cols:
        try:
            cur.execute("ALTER TABLE scores ADD COLUMN breakdown TEXT")
            print("✅ Added 'breakdown' column to scores table.")
        except Exception as e:
            print("⚠️ Could not add 'breakdown' column:", e)
    else:
        print("ℹ️ 'breakdown' column already exists — no changes made.")

    if "updated_at" not in cols:
        try:
            cur.execute("ALTER TABLE scores ADD COLUMN updated_at TEXT")
            print("✅ Added 'updated_at' column to scores table.")
        except Exception as e:
            print("⚠️ Could not add 'updated_at' column:", e)
    else:
        print("ℹ️ 'updated_at' column already exists — no changes made.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()
