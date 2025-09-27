import sqlite3
import bcrypt
from datetime import datetime

DB_FILE = "opportunities.db"

def migrate_users():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Create users table if not exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            subscription TEXT DEFAULT 'demo',
            created_at TEXT
        )
    """)

    # Users to seed
    users = [
        {
            "name": "Stuart Manley",
            "email": "smanley@manleysolutions.com",
            "phone": "9493009992",
            "password": "ChangeMe123",  # 🔑 initial password
            "role": "admin",
            "subscription": "enterprise"
        },
        {
            "name": "Deric Blum",
            "email": "dblum@manleysolutions.com",
            "phone": "3177486652",
            "password": "ChangeMe123",  # 🔑 initial password
            "role": "user",
            "subscription": "demo"
        }
    ]

    for u in users:
        # Hash password
        password_hash = bcrypt.hashpw(u["password"].encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        try:
            cur.execute("""
                INSERT INTO users (name, email, phone, password_hash, role, subscription, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                u["name"],
                u["email"],
                u["phone"],
                password_hash,
                u["role"],
                u["subscription"],
                datetime.utcnow().isoformat()
            ))
            print(f"✅ Inserted user {u['name']} ({u['email']})")
        except sqlite3.IntegrityError:
            print(f"⚠️ User {u['email']} already exists — skipping.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate_users()

