import sqlite3
import json
import os
from typing import List, Dict, Optional
from datetime import datetime

class ChatPersistenceService:
    def __init__(self, db_path: str = "chat_history.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database with chat history table."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    user_message TEXT NOT NULL,
                    agent_response TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_id 
                ON chat_sessions(session_id)
            """)
            conn.commit()
    
    def save_chat_turn(self, session_id: str, user_message: str, agent_response: str) -> bool:
        """Save a chat turn (user message + agent response) to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO chat_sessions (session_id, user_message, agent_response, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (session_id, user_message, agent_response, datetime.now()))
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ Error saving chat turn: {e}")
            return False
    
    def get_chat_history(self, session_id: str, limit: int = 10) -> List[Dict]:
        """Get chat history for a session, ordered by most recent first."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT user_message, agent_response, timestamp 
                    FROM chat_sessions 
                    WHERE session_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (session_id, limit))
                
                rows = cursor.fetchall()
                return [
                    {
                        "user_message": row[0],
                        "agent_response": row[1],
                        "timestamp": row[2]
                    }
                    for row in rows
                ]
        except Exception as e:
            print(f"❌ Error getting chat history: {e}")
            return []
    
    def get_session_list(self, limit: int = 20) -> List[Dict]:
        """Get list of recent chat sessions."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT DISTINCT session_id, 
                           MAX(timestamp) as last_activity,
                           COUNT(*) as message_count
                    FROM chat_sessions 
                    GROUP BY session_id 
                    ORDER BY last_activity DESC 
                    LIMIT ?
                """, (limit,))
                
                rows = cursor.fetchall()
                return [
                    {
                        "session_id": row[0],
                        "last_activity": row[1],
                        "message_count": row[2]
                    }
                    for row in rows
                ]
        except Exception as e:
            print(f"❌ Error getting session list: {e}")
            return []
    
    def clear_session_history(self, session_id: str) -> bool:
        """Clear chat history for a specific session."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM chat_sessions WHERE session_id = ?", (session_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ Error clearing session history: {e}")
            return False

# Global instance
chat_db = ChatPersistenceService()
