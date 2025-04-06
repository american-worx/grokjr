# In app/memory/sqlite_store.py

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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS status (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_prompt TEXT,
                local_response TEXT,
                response TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                agent_id TEXT  -- Optional, for swarm interactions
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                description TEXT,  
                instructions TEXT,
                code TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                acquired TEXT DEFAULT 'false'
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY,
                role TEXT,
                status TEXT,  -- "online" or "offline"
                last_seen TEXT  -- ISO timestamp
            )
        """)
        conn.commit()
        conn.close()

    def get_next_skill_id(self) -> int:
        """Get the next available skill ID by finding the max ID and incrementing."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(id) FROM skills")
        max_id = cursor.fetchone()[0]
        conn.close()
        return (max_id or 0) + 1
    

    def store_identity(self, identity: dict):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO status (key, value) VALUES (?, ?)", ("identity_name", identity["name"]))
        cursor.execute("INSERT OR REPLACE INTO status (key, value) VALUES (?, ?)", ("identity_purpose", identity["purpose"]))
        conn.commit()
        conn.close()
        logger.info("Identity stored in SQLite.")

    def get_identity(self) -> dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM status WHERE key = 'identity_name'")
        result = cursor.fetchone()
        name = result[0] if result else "Grok Jr."
        cursor.execute("SELECT value FROM status WHERE key = 'identity_purpose'")
        result = cursor.fetchone()
        purpose = result[0] if result else "The Adaptive Skill Master and Continuous Learning Facilitator"
        conn.close()
        return {"name": name, "purpose": purpose}

    def set_status(self, key: str, value: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO status (key, value) VALUES (?, ?)", (key, value))
        conn.commit()
        conn.close()

    def get_status(self, key: str) -> str | None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM status WHERE key = ?", (key,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else "0"

    def add_interaction(self, user_prompt: str, local_response: str, response: str, agent_id: str = None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO interactions (user_prompt, local_response, response, agent_id)
            VALUES (?, ?, ?, ?)
        """, (user_prompt, local_response, response, agent_id))
        conn.commit()
        conn.close()

    def register_agent(self, agent_id: str, role: str, status: str = "online"):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO agents (agent_id, role, status, last_seen)
            VALUES (?, ?, ?, ?)
        """, (agent_id, role, status, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        logger.info(f"Registered agent '{agent_id}' with role '{role}'.")

    def update_agent_status(self, agent_id: str, status: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE agents SET status = ?, last_seen = ? WHERE agent_id = ?
        """, (status, datetime.now().isoformat(), agent_id))
        conn.commit()
        conn.close()
        logger.info(f"Updated agent '{agent_id}' status to '{status}'.")

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
            INSERT OR IGNORE INTO skills (name, description, instructions, code, timestamp, acquired)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (skill["name"], skill.get("description"), skill.get("instructions"), skill.get("code"), skill["timestamp"], skill.get("acquired", "false")))
        skill_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return skill_id

    def update_skill(self, skill: dict):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE skills
            SET instructions = ?, code = ?, timestamp = ?, acquired = ?
            WHERE name = ?
        """, (skill.get("instructions"), skill.get("code"), skill["timestamp"], skill.get("acquired", "false"), skill["name"]))
        conn.commit()
        conn.close()

    def get_skill(self, skill_name: str) -> dict | None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, description, instructions, code, timestamp, acquired FROM skills WHERE name = ?", (skill_name,))
        result = cursor.fetchone()
        conn.close()
        if result:
            timestamp = result[5]
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp)
                except ValueError:
                    timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            elif timestamp is None:
                timestamp = datetime.now()
            
            return {
                "id": result[0],
                "name": result[1],
                "description": result[2],
                "instructions": result[3],
                "code": result[4],
                "timestamp": timestamp,
                "acquired": result[6]
            }
        return None
    def delete_skill(self, skill_name: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM skills WHERE name = ?", (skill_name,))
            conn.commit()
            if cursor.rowcount > 0:
                logger.info(f"Deleted skill '{skill_name}' from SQLite.")
            else:
                logger.warning(f"Skill '{skill_name}' not found for deletion.")

    def query_sql(self, query: str, params: tuple = ()) -> list:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        return [dict(row) for row in results]

    def is_initialized(self) -> bool:
        return self.get_status("core_initialized") == "true"