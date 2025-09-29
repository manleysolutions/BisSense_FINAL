def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            agency TEXT,
            source TEXT,
            issue_date TEXT,
            due_date TEXT,
            url TEXT,
            category TEXT,
            budget REAL,
            budget_published REAL,
            summary TEXT,
            scope_of_work TEXT,
            requirements TEXT,
            poc TEXT,
            location TEXT,
            terms TEXT,
            critical_reqs TEXT,
            raw_text TEXT,
            ai_score INTEGER,
            human_score INTEGER,
            reasons TEXT,
            status TEXT,
            equipment_cost REAL,
            labor_cost REAL,
            admin_cost REAL,
            total_cost REAL,
            suggested_bid REAL,
            profit_margin REAL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opp_id INTEGER,
            ai_score INTEGER,
            human_score INTEGER,
            reasons TEXT
        )
    """)

    conn.commit()
    conn.close()
