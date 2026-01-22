"""
Memory Component - Three Types of Memory
1. Episodic Memory: Conversation history (in-session)
2. Short-term Memory: Session context (Redis cache)
3. Long-term Memory: User preferences (PostgreSQL)
"""

import os
import json
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class Memory:
    """Manages three types of memory for the chatbot"""

    def __init__(self, user_id: str):
        load_dotenv()
        self.user_id = user_id

        # 1. Episodic Memory: In-memory conversation history
        self.episodic = []

        # 2. Short-term Memory: Redis cache for session
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(
                    host=os.getenv('REDIS_HOST', 'localhost'),
                    port=int(os.getenv('REDIS_PORT', 6379)),
                    decode_responses=True
                )
                self.redis_client.ping()  # Test connection
                self.redis_available = True
            except:
                self.redis_available = False
                self.shortterm = {}  # Fallback to dict
        else:
            self.redis_available = False
            self.shortterm = {}

        # 3. Long-term Memory: PostgreSQL
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', 5432),
            'database': os.getenv('DB_NAME', 'realestate'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD')
        }

    # ============ EPISODIC MEMORY ============
    def add_message(self, role: str, content: str):
        """Add message to conversation history (episodic memory)"""
        self.episodic.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })

    def get_conversation_history(self, last_n: int = None) -> list:
        """Get conversation history"""
        if last_n:
            return self.episodic[-last_n:]
        return self.episodic

    def clear_conversation(self):
        """Clear conversation history"""
        self.episodic = []

    # ============ SHORT-TERM MEMORY (Redis) ============
    def set_context(self, key: str, value: str, ttl: int = 3600):
        """Store session context (expires after ttl seconds)"""
        full_key = f"session:{self.user_id}:{key}"

        if self.redis_available:
            self.redis_client.setex(full_key, ttl, json.dumps(value))
        else:
            self.shortterm[full_key] = value

    def get_context(self, key: str):
        """Retrieve session context"""
        full_key = f"session:{self.user_id}:{key}"

        if self.redis_available:
            value = self.redis_client.get(full_key)
            return json.loads(value) if value else None
        else:
            return self.shortterm.get(full_key)

    def clear_session(self):
        """Clear all session data"""
        if self.redis_available:
            pattern = f"session:{self.user_id}:*"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
        else:
            self.shortterm = {}

    # ============ LONG-TERM MEMORY (PostgreSQL) ============
    def save_preference(self, key: str, value: str):
        """Save user preference to database (persistent)"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()

        # Check if user_memory table exists (from Phase 1 migrations)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_memory (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(100) NOT NULL,
                memory_key VARCHAR(100) NOT NULL,
                memory_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, memory_key)
            )
        """)

        # Insert or update
        cursor.execute("""
            INSERT INTO user_memory (user_id, memory_key, memory_value)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, memory_key)
            DO UPDATE SET memory_value = EXCLUDED.memory_value, updated_at = CURRENT_TIMESTAMP
        """, (self.user_id, key, value))

        conn.commit()
        cursor.close()
        conn.close()

    def get_preference(self, key: str):
        """Retrieve user preference from database"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT memory_value FROM user_memory
            WHERE user_id = %s AND memory_key = %s
        """, (self.user_id, key))

        result = cursor.fetchone()
        cursor.close()
        conn.close()

        return result[0] if result else None

    def get_all_preferences(self) -> dict:
        """Get all user preferences"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT memory_key, memory_value FROM user_memory
            WHERE user_id = %s
        """, (self.user_id,))

        results = cursor.fetchall()
        cursor.close()
        conn.close()

        return {row[0]: row[1] for row in results}
