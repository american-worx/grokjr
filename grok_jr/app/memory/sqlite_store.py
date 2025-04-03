import sqlite3
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SQLiteStore:
    def __init__(self, db_path: str = "grok_jr.db"):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Status table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS status (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        # Interactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_prompt TEXT,
                local_response TEXT,  -- New column for local inference
                response TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Skills table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                instructions TEXT,
                code TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def get_status(self, key: str) -> str | None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM status WHERE key = ?", (key,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def set_status(self, key: str, value: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO status (key, value) VALUES (?, ?)", (key, value))
        conn.commit()
        conn.close()

    def add_interaction(self, user_prompt: str, local_response: str, response: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO interactions (user_prompt, local_response, response)
            VALUES (?, ?, ?)
        """, (user_prompt, local_response, response))
        conn.commit()
        conn.close()

    def get_last_interactions(self, limit: int = 3) -> list:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_prompt, local_response, response
            FROM interactions
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        result = cursor.fetchall()
        conn.close()
        return result

    def add_skill(self, skill: dict) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO skills (name, instructions, code, timestamp)
            VALUES (?, ?, ?, ?)
        """, (skill["name"], skill["instructions"], skill.get("code"), skill["timestamp"]))
        skill_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return skill_id

    def update_skill(self, skill: dict):
        """Update an existing skill in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE skills
            SET name = ?, instructions = ?, code = ?, timestamp = ?
            WHERE id = ?
        """, (skill["name"], skill["instructions"], skill.get("code"), skill["timestamp"], skill["id"]))
        conn.commit()
        conn.close()

    def get_skill(self, skill_name: str) -> dict | None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM skills WHERE name = ?", (skill_name,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return {
                "id": result[0],
                "name": result[1],
                "instructions": result[2],
                "code": result[3],
                "timestamp": datetime.fromisoformat(result[4])
            }
        return None
    
    def delete_skill(self, skill_name: str):
        """Delete a skill by name from the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM skills WHERE name = ?", (skill_name,))
            conn.commit()
            if cursor.rowcount > 0:
                logger.info(f"Deleted skill '{skill_name}' from SQLite.")
            else:
                logger.warning(f"Skill '{skill_name}' not found for deletion.")