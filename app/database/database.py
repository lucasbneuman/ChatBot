# app/data/database.py
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "leads.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            thread_id TEXT PRIMARY KEY,
            name TEXT,
            company TEXT,
            budget TEXT,
            location TEXT,
            sector TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_lead_info(thread_id: str, field: str, value: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"""
        INSERT INTO leads (thread_id, {field})
        VALUES (?, ?)
        ON CONFLICT(thread_id) DO UPDATE SET {field} = excluded.{field}
    """, (thread_id, value))
    conn.commit()
    conn.close()

def get_lead(thread_id: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM leads WHERE thread_id = ?", (thread_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "thread_id": row[0],
            "name": row[1],
            "company": row[2],
            "budget": row[3],
            "location": row[4],
            "sector": row[5]
        }
    return {}
