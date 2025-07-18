"""
Database manager for AI Companion application.
Handles all database operations including CRUD operations for conversations, 
personality traits, user preferences, and memories.
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from .schemas import SCHEMA_SQL, DEFAULT_PERSONALITY_TRAITS, DEFAULT_USER_PREFERENCES


class DBManager:
    """
    Manages all database operations for the AI Companion application.
    """
    
    def __init__(self, db_path: str = "ai_companion.db"):
        """
        Initialize database manager and create necessary tables.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Ensure database directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row  # Enable dict-like access
        self.cursor = self.connection.cursor()
        
        self.create_tables()
        self.initialize_defaults()
    
    def create_tables(self):
        """Create all necessary database tables."""
        try:
            for table_name, schema in SCHEMA_SQL.items():
                self.cursor.execute(schema)
                self.logger.info(f"Created/verified table: {table_name}")
            
            self.connection.commit()
            self.logger.info("Database schema initialized successfully")
        except Exception as e:
            self.logger.error(f"Error creating tables: {e}")
            raise
    
    def initialize_defaults(self, user_id: str = "default_user"):
        """Initialize default personality traits and preferences for a user."""
        try:
            # Initialize personality traits
            for trait_name, trait_value in DEFAULT_PERSONALITY_TRAITS.items():
                self.cursor.execute("""
                    INSERT OR IGNORE INTO personality_traits 
                    (user_id, trait_name, trait_value) VALUES (?, ?, ?)
                """, (user_id, trait_name, trait_value))
            
            # Initialize user preferences
            for category, prefs in DEFAULT_USER_PREFERENCES.items():
                for key, value in prefs.items():
                    self.cursor.execute("""
                        INSERT OR IGNORE INTO user_preferences 
                        (user_id, preference_category, preference_key, preference_value) 
                        VALUES (?, ?, ?, ?)
                    """, (user_id, category, key, value))
            
            # Initialize bonding progress
            self.cursor.execute("""
                INSERT OR IGNORE INTO bonding_progress (user_id) VALUES (?)
            """, (user_id,))
            
            # Initialize avatar state
            self.cursor.execute("""
                INSERT OR IGNORE INTO avatar_states (user_id) VALUES (?)
            """, (user_id,))
            
            self.connection.commit()
            self.logger.info(f"Initialized defaults for user: {user_id}")
        except Exception as e:
            self.logger.error(f"Error initializing defaults: {e}")
            raise
    
    # Conversation management
    def add_conversation(self, user_id: str, message_type: str, content: str, 
                        emotion_state: str = None, context_tags: List[str] = None) -> int:
        """Add a new conversation message."""
        context_tags_json = json.dumps(context_tags) if context_tags else None
        
        self.cursor.execute("""
            INSERT INTO conversations 
            (user_id, message_type, content, emotion_state, context_tags)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, message_type, content, emotion_state, context_tags_json))
        
        conversation_id = self.cursor.lastrowid
        self.connection.commit()
        
        # Update bonding progress
        self._update_conversation_count(user_id)
        
        return conversation_id
    
    def get_conversation_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent conversation history for a user."""
        self.cursor.execute("""
            SELECT * FROM conversations 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (user_id, limit))
        
        rows = self.cursor.fetchall()
        return [dict(row) for row in reversed(rows)]  # Return in chronological order
    
    def get_conversations_by_date_range(self, user_id: str, start_date: datetime, 
                                      end_date: datetime) -> List[Dict[str, Any]]:
        """Get conversations within a specific date range."""
        self.cursor.execute("""
            SELECT * FROM conversations 
            WHERE user_id = ? AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp ASC
        """, (user_id, start_date.isoformat(), end_date.isoformat()))
        
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]
    
    # Personality management
    def update_personality_trait(self, user_id: str, trait_name: str, trait_value: float):
        """Update a personality trait value."""
        # Clamp value between 0.0 and 1.0
        trait_value = max(0.0, min(1.0, trait_value))
        
        self.cursor.execute("""
            UPDATE personality_traits 
            SET trait_value = ?, last_updated = CURRENT_TIMESTAMP
            WHERE user_id = ? AND trait_name = ?
        """, (trait_value, user_id, trait_name))
        
        self.connection.commit()
    
    def get_personality_profile(self, user_id: str) -> Dict[str, float]:
        """Get all personality traits for a user."""
        self.cursor.execute("""
            SELECT trait_name, trait_value FROM personality_traits 
            WHERE user_id = ?
        """, (user_id,))
        
        rows = self.cursor.fetchall()
        return {row['trait_name']: row['trait_value'] for row in rows}
    
    # Memory management
    def add_memory(self, user_id: str, memory_type: str, key_topic: str, 
                  value_content: str, importance_score: float = 0.5) -> int:
        """Add a new memory for the user."""
        self.cursor.execute("""
            INSERT INTO user_memories 
            (user_id, memory_type, key_topic, value_content, importance_score)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, memory_type, key_topic, value_content, importance_score))
        
        memory_id = self.cursor.lastrowid
        self.connection.commit()
        return memory_id
    
    def get_memories_by_topic(self, user_id: str, topic: str) -> List[Dict[str, Any]]:
        """Get memories related to a specific topic."""
        self.cursor.execute("""
            SELECT * FROM user_memories 
            WHERE user_id = ? AND key_topic LIKE ?
            ORDER BY importance_score DESC, last_accessed DESC
        """, (user_id, f"%{topic}%"))
        
        rows = self.cursor.fetchall()
        
        # Update access count and timestamp
        for row in rows:
            self.cursor.execute("""
                UPDATE user_memories 
                SET access_count = access_count + 1, last_accessed = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (row['id'],))
        
        self.connection.commit()
        return [dict(row) for row in rows]
    
    def get_important_memories(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most important memories for context."""
        self.cursor.execute("""
            SELECT * FROM user_memories 
            WHERE user_id = ? 
            ORDER BY importance_score DESC, access_count DESC
            LIMIT ?
        """, (user_id, limit))
        
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]
    
    # Bonding system
    def get_bonding_progress(self, user_id: str) -> Dict[str, Any]:
        """Get current bonding progress for a user."""
        self.cursor.execute("""
            SELECT * FROM bonding_progress WHERE user_id = ?
        """, (user_id,))
        
        row = self.cursor.fetchone()
        return dict(row) if row else {}
    
    def update_bonding_progress(self, user_id: str, experience_points: int):
        """Update bonding progress and potentially level up."""
        current_progress = self.get_bonding_progress(user_id)
        new_xp = current_progress.get('experience_points', 0) + experience_points
        
        # Calculate new bond level (every 100 XP = 1 level, max 10)
        new_level = min(10, max(1, (new_xp // 100) + 1))
        
        # Determine relationship stage
        relationship_stages = [
            'stranger', 'acquaintance', 'friend', 'close_friend', 'best_friend'
        ]
        stage_index = min(len(relationship_stages) - 1, (new_level - 1) // 2)
        new_stage = relationship_stages[stage_index]
        
        self.cursor.execute("""
            UPDATE bonding_progress 
            SET bond_level = ?, experience_points = ?, relationship_stage = ?,
                last_interaction = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (new_level, new_xp, new_stage, user_id))
        
        self.connection.commit()
    
    def update_bonding_progress_with_personality(self, user_id: str, bond_level: int, personality_data: str):
        """Update bonding progress with personality data."""
        self.cursor.execute("""
            UPDATE bonding_progress 
            SET bond_level = ?, personality_data = ?, last_interaction = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (bond_level, personality_data, user_id))
        
        self.connection.commit()
    
    def _update_conversation_count(self, user_id: str):
        """Internal method to update conversation count."""
        self.cursor.execute("""
            UPDATE bonding_progress 
            SET total_conversations = total_conversations + 1,
                last_interaction = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (user_id,))
        
        self.connection.commit()
    
    # Avatar state management
    def get_avatar_state(self, user_id: str) -> Dict[str, Any]:
        """Get current avatar emotional state."""
        self.cursor.execute("""
            SELECT * FROM avatar_states WHERE user_id = ?
        """, (user_id,))
        
        row = self.cursor.fetchone()
        return dict(row) if row else {}
    
    def update_avatar_state(self, user_id: str, **kwargs):
        """Update avatar emotional state."""
        valid_fields = ['current_mood', 'energy_level', 'happiness_level', 
                       'curiosity_level', 'trust_level']
        
        updates = []
        values = []
        
        for field, value in kwargs.items():
            if field in valid_fields:
                updates.append(f"{field} = ?")
                values.append(value)
        
        if updates:
            values.append(user_id)
            query = f"""
                UPDATE avatar_states 
                SET {', '.join(updates)}, last_updated = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """
            self.cursor.execute(query, values)
            self.connection.commit()
    
    # User preferences
    def get_user_preference(self, user_id: str, category: str, key: str) -> Optional[str]:
        """Get a specific user preference."""
        self.cursor.execute("""
            SELECT preference_value FROM user_preferences 
            WHERE user_id = ? AND preference_category = ? AND preference_key = ?
        """, (user_id, category, key))
        
        row = self.cursor.fetchone()
        return row['preference_value'] if row else None
    
    def set_user_preference(self, user_id: str, category: str, key: str, value: str):
        """Set a user preference."""
        self.cursor.execute("""
            INSERT OR REPLACE INTO user_preferences 
            (user_id, preference_category, preference_key, preference_value)
            VALUES (?, ?, ?, ?)
        """, (user_id, category, key, value))
        
        self.connection.commit()
    
    def get_all_preferences(self, user_id: str) -> Dict[str, Dict[str, str]]:
        """Get all preferences for a user, organized by category."""
        self.cursor.execute("""
            SELECT preference_category, preference_key, preference_value 
            FROM user_preferences WHERE user_id = ?
        """, (user_id,))
        
        rows = self.cursor.fetchall()
        preferences = {}
        
        for row in rows:
            category = row['preference_category']
            if category not in preferences:
                preferences[category] = {}
            preferences[category][row['preference_key']] = row['preference_value']
        
        return preferences
    
    # Cleanup and maintenance
    def cleanup_old_data(self, days_to_keep: int = 365):
        """Clean up old conversation data based on retention policy."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        self.cursor.execute("""
            DELETE FROM conversations 
            WHERE timestamp < ?
        """, (cutoff_date.isoformat(),))
        
        deleted_count = self.cursor.rowcount
        self.connection.commit()
        
        self.logger.info(f"Cleaned up {deleted_count} old conversation records")
        return deleted_count
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        stats = {}
        
        for table_name in SCHEMA_SQL.keys():
            self.cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            row = self.cursor.fetchone()
            stats[table_name] = row['count']
        
        return stats
    
    # Enhanced memory management
    def add_conversation_context(self, user_id: str, session_id: str, context_window: List[Dict]) -> None:
        """Store conversation context for session continuity."""
        context_json = json.dumps(context_window)
        
        self.cursor.execute("""
            INSERT OR REPLACE INTO conversation_context 
            (user_id, session_id, context_window, last_updated)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (user_id, session_id, context_json))
        
        self.connection.commit()
    
    def get_conversation_context(self, user_id: str, session_id: str) -> List[Dict]:
        """Retrieve conversation context for session."""
        self.cursor.execute("""
            SELECT context_window FROM conversation_context 
            WHERE user_id = ? AND session_id = ?
        """, (user_id, session_id))
        
        row = self.cursor.fetchone()
        if row:
            return json.loads(row['context_window'])
        return []
    
    def create_memory_cluster(self, user_id: str, cluster_name: str, 
                            memory_ids: List[int], description: str = "") -> int:
        """Create a cluster of related memories."""
        memory_ids_json = json.dumps(memory_ids)
        
        self.cursor.execute("""
            INSERT INTO memory_clusters 
            (user_id, cluster_name, cluster_description, memory_ids)
            VALUES (?, ?, ?, ?)
        """, (user_id, cluster_name, description, memory_ids_json))
        
        cluster_id = self.cursor.lastrowid
        self.connection.commit()
        return cluster_id
    
    def get_memory_clusters(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all memory clusters for a user."""
        self.cursor.execute("""
            SELECT * FROM memory_clusters 
            WHERE user_id = ? 
            ORDER BY importance_score DESC, last_accessed DESC
        """, (user_id,))
        
        return [dict(row) for row in self.cursor.fetchall()]
    
    # LLM response caching
    def cache_llm_response(self, input_hash: str, response: str, model_name: str, temperature: float) -> None:
        """Cache LLM response for faster retrieval."""
        self.cursor.execute("""
            INSERT OR REPLACE INTO llm_cache 
            (input_hash, response_text, model_name, temperature, last_accessed)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (input_hash, response, model_name, temperature))
        
        self.connection.commit()
    
    def get_cached_llm_response(self, input_hash: str) -> Optional[str]:
        """Retrieve cached LLM response if available."""
        self.cursor.execute("""
            SELECT response_text FROM llm_cache 
            WHERE input_hash = ?
        """, (input_hash,))
        
        row = self.cursor.fetchone()
        if row:
            # Update access count and timestamp
            self.cursor.execute("""
                UPDATE llm_cache 
                SET access_count = access_count + 1, last_accessed = CURRENT_TIMESTAMP
                WHERE input_hash = ?
            """, (input_hash,))
            self.connection.commit()
            return row['response_text']
        return None
    
    # Conversation summarization
    def add_conversation_summary(self, user_id: str, date_range: str, 
                                summary_text: str, key_topics: List[str], 
                                emotional_tone: str = "") -> int:
        """Add a conversation summary."""
        key_topics_json = json.dumps(key_topics)
        
        self.cursor.execute("""
            INSERT INTO conversation_summaries 
            (user_id, date_range, summary_text, key_topics, emotional_tone)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, date_range, summary_text, key_topics_json, emotional_tone))
        
        summary_id = self.cursor.lastrowid
        self.connection.commit()
        return summary_id
    
    def get_conversation_summaries(self, user_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get recent conversation summaries."""
        self.cursor.execute("""
            SELECT * FROM conversation_summaries 
            WHERE user_id = ? AND created_at > datetime('now', '-{} days')
            ORDER BY created_at DESC
        """.format(days), (user_id,))
        
        return [dict(row) for row in self.cursor.fetchall()]
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.logger.info("Database connection closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

