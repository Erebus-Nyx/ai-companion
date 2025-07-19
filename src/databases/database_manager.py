"""
Database Manager for AI Companion - Separated Database Architecture
Provides connection functions for the different databases.
"""

import sqlite3
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def get_user_data_dir() -> Path:
    """Get the user data directory for AI Companion"""
    return Path.home() / ".local/share/ai2d_chat"

def get_live2d_connection():
    """Get connection to the Live2D database"""
    db_path = get_user_data_dir() / "databases" / "live2d.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row  # Enable dictionary-like access to rows
    return conn

def get_conversations_connection():
    """Get connection to the conversations database"""
    db_path = get_user_data_dir() / "databases" / "conversations.db"
    return sqlite3.connect(str(db_path))

def get_personality_connection():
    """Get connection to the personality database"""
    db_path = get_user_data_dir() / "databases" / "personality.db"
    return sqlite3.connect(str(db_path))

def get_system_connection():
    """Get connection to the system database"""
    db_path = get_user_data_dir() / "databases" / "system.db"
    return sqlite3.connect(str(db_path))

class DatabaseManager:
    """
    Legacy DatabaseManager class for compatibility with existing scripts.
    Uses the separated database architecture.
    """
    
    def __init__(self, base_path=None):
        """Initialize database manager with optional base path (ignored for compatibility)"""
        self.base_path = base_path
        self.logger = logging.getLogger(__name__)
        # For compatibility with memory system
        self._connection = None
        self._cursor = None
        
    @property
    def connection(self):
        """Get connection for compatibility"""
        if not self._connection:
            self._connection = get_conversations_connection()
        return self._connection
        
    @property 
    def cursor(self):
        """Get cursor for compatibility"""
        if not self._cursor:
            self._cursor = self.connection.cursor()
        return self._cursor
        
    def get_live2d_connection(self):
        """Get Live2D database connection"""
        return get_live2d_connection()
        
    def get_conversations_connection(self):
        """Get conversations database connection"""
        return get_conversations_connection()
        
    def get_personality_connection(self):
        """Get personality database connection"""
        return get_personality_connection()
        
    def get_system_connection(self):
        """Get system database connection"""
        return get_system_connection()
        
    # Placeholder methods for memory system compatibility
    def add_memory(self, *args, **kwargs):
        """Placeholder for memory system compatibility"""
        self.logger.warning("add_memory called on legacy DatabaseManager - not implemented")
        return None
        
    def get_memories_by_topic(self, *args, **kwargs):
        """Placeholder for memory system compatibility"""
        self.logger.warning("get_memories_by_topic called on legacy DatabaseManager - not implemented")
        return []
        
    def get_important_memories(self, *args, **kwargs):
        """Placeholder for memory system compatibility"""
        self.logger.warning("get_important_memories called on legacy DatabaseManager - not implemented")
        return []
        
    def add_conversation_summary(self, *args, **kwargs):
        """Placeholder for memory system compatibility"""
        self.logger.warning("add_conversation_summary called on legacy DatabaseManager - not implemented")
        return None
    
    # Model-specific conversation methods
    def add_conversation(self, user_id: str, message_type: str, content: str, 
                        emotion_detected: str = None, response_time_ms: int = None, 
                        model_id: str = "default"):
        """Add conversation message with model isolation"""
        with get_conversations_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conversations (user_id, model_id, message_type, content, emotion_detected, response_time_ms)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, model_id, message_type, content, emotion_detected, response_time_ms))
            conn.commit()
            return cursor.lastrowid
    
    def get_conversation_history(self, user_id: str, model_id: str = "default", limit: int = 10):
        """Get conversation history for specific user and model"""
        with get_conversations_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT message_type, content, timestamp, emotion_detected
                FROM conversations 
                WHERE user_id = ? AND model_id = ?
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (user_id, model_id, limit))
            rows = cursor.fetchall()
            return [{"type": row[0], "content": row[1], "timestamp": row[2], "emotion": row[3]} 
                   for row in reversed(rows)]
    
    def add_conversation_context(self, user_id: str, session_id: str, messages: list, model_id: str = "default"):
        """Store conversation context for session with model isolation"""
        import json
        with get_conversations_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO conversation_contexts (user_id, model_id, session_id, messages)
                VALUES (?, ?, ?, ?)
            """, (user_id, model_id, session_id, json.dumps(messages)))
            conn.commit()
    
    def get_conversation_context(self, user_id: str, session_id: str, model_id: str = "default"):
        """Get conversation context for session with model isolation"""
        import json
        with get_conversations_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT messages FROM conversation_contexts 
                WHERE user_id = ? AND model_id = ? AND session_id = ?
            """, (user_id, model_id, session_id))
            row = cursor.fetchone()
            return json.loads(row[0]) if row else []
    
    def cache_llm_response(self, input_hash: str, response: str, model_name: str, 
                          temperature: float, model_id: str = "default"):
        """Cache LLM response with model awareness"""
        from datetime import datetime, timedelta
        expires_at = datetime.now() + timedelta(hours=24)
        
        with get_conversations_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO llm_cache 
                (input_hash, model_id, response, model_name, temperature, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (input_hash, model_id, response, model_name, temperature, expires_at))
            conn.commit()
    
    def get_cached_llm_response(self, input_hash: str, model_id: str = "default"):
        """Get cached LLM response with model awareness"""
        from datetime import datetime
        with get_conversations_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT response FROM llm_cache 
                WHERE input_hash = ? AND model_id = ? AND expires_at > ?
            """, (input_hash, model_id, datetime.now()))
            row = cursor.fetchone()
            return row[0] if row else None
    
    # Model-specific personality methods
    def get_model_personality(self, model_id: str):
        """Get personality data for a specific model"""
        with get_personality_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name, base_traits, current_traits, description, background_story,
                       favorite_things, personality_notes, appearance_notes
                FROM model_personalities WHERE model_id = ?
            """, (model_id,))
            row = cursor.fetchone()
            if row:
                import json
                return {
                    "name": row[0],
                    "base_traits": json.loads(row[1]),
                    "current_traits": json.loads(row[2]),
                    "description": row[3],
                    "background_story": row[4],
                    "favorite_things": row[5],
                    "personality_notes": row[6],
                    "appearance_notes": row[7]
                }
            return None
    
    def update_model_personality(self, model_id: str, **kwargs):
        """Update personality data for a specific model"""
        import json
        with get_personality_connection() as conn:
            cursor = conn.cursor()
            
            # Build dynamic update query
            update_fields = []
            values = []
            
            for field in ['name', 'description', 'background_story', 'favorite_things', 
                         'personality_notes', 'appearance_notes']:
                if field in kwargs:
                    update_fields.append(f"{field} = ?")
                    values.append(kwargs[field])
            
            for field in ['base_traits', 'current_traits']:
                if field in kwargs:
                    update_fields.append(f"{field} = ?")
                    values.append(json.dumps(kwargs[field]))
            
            if update_fields:
                update_fields.append("last_updated = CURRENT_TIMESTAMP")
                values.append(model_id)
                
                query = f"UPDATE model_personalities SET {', '.join(update_fields)} WHERE model_id = ?"
                cursor.execute(query, values)
                conn.commit()
    
    def get_personality_profile(self, user_id: str, model_id: str = "default"):
        """Get personality traits adapted for user interaction"""
        with get_personality_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ps.trait_name, ps.current_value
                FROM personality_states ps
                WHERE ps.user_id = ? AND ps.model_id = ?
            """, (user_id, model_id))
            
            traits = {}
            for row in cursor.fetchall():
                traits[row[0]] = row[1]
            
            # If no dynamic traits exist, get base traits from model
            if not traits:
                model_personality = self.get_model_personality(model_id)
                if model_personality and 'current_traits' in model_personality:
                    traits = model_personality['current_traits']
            
            return traits
    
    def update_personality_state(self, user_id: str, model_id: str, trait_name: str, 
                               new_value: float, reason: str = None):
        """Update dynamic personality state for user-model interaction"""
        with get_personality_connection() as conn:
            cursor = conn.cursor()
            
            # Get current state or create new
            cursor.execute("""
                SELECT base_value, current_value FROM personality_states
                WHERE user_id = ? AND model_id = ? AND trait_name = ?
            """, (user_id, model_id, trait_name))
            
            row = cursor.fetchone()
            base_value = row[0] if row else new_value
            old_value = row[1] if row else new_value
            
            # Update state
            cursor.execute("""
                INSERT OR REPLACE INTO personality_states 
                (user_id, model_id, trait_name, base_value, current_value, adaptation_reason)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, model_id, trait_name, base_value, new_value, reason))
            
            # Log the interaction
            cursor.execute("""
                INSERT INTO personality_interactions 
                (user_id, model_id, interaction_type, trait_affected, value_change, reason)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, model_id, "trait_adaptation", trait_name, new_value - old_value, reason))
            
            conn.commit()
    
    def get_bonding_progress(self, user_id: str, model_id: str = "default"):
        """Get bonding progress for specific user-model pair"""
        with get_personality_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT bond_level, experience_points, relationship_stage, trust_level, affection_level
                FROM bonding_progress WHERE user_id = ? AND model_id = ?
            """, (user_id, model_id))
            row = cursor.fetchone()
            if row:
                return {
                    "bond_level": row[0],
                    "experience_points": row[1],
                    "relationship_stage": row[2],
                    "trust_level": row[3],
                    "affection_level": row[4]
                }
            return {"bond_level": 1, "experience_points": 0, "relationship_stage": "stranger", 
                   "trust_level": 0.5, "affection_level": 0.5}
    
    def update_bonding_progress(self, user_id: str, experience_gain: int, model_id: str = "default"):
        """Update bonding progress for specific user-model pair"""
        with get_personality_connection() as conn:
            cursor = conn.cursor()
            
            # Get current progress
            current = self.get_bonding_progress(user_id, model_id)
            new_xp = current["experience_points"] + experience_gain
            
            # Calculate new bond level (100 XP per level)
            new_level = max(1, new_xp // 100 + 1)
            
            # Determine relationship stage
            if new_level <= 2:
                stage = "stranger"
            elif new_level <= 5:
                stage = "acquaintance"
            elif new_level <= 10:
                stage = "friend"
            elif new_level <= 20:
                stage = "close_friend"
            else:
                stage = "best_friend"
            
            # Update progress
            cursor.execute("""
                INSERT OR REPLACE INTO bonding_progress 
                (user_id, model_id, bond_level, experience_points, relationship_stage, trust_level, affection_level)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, model_id, new_level, new_xp, stage, 
                 min(1.0, current["trust_level"] + experience_gain * 0.01),
                 min(1.0, current["affection_level"] + experience_gain * 0.01)))
            conn.commit()
    
    def get_avatar_state(self, user_id: str, model_id: str = "default"):
        """Get avatar emotional state for specific user-model pair"""
        with get_personality_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT current_mood, energy_level, happiness_level, stress_level
                FROM avatar_states WHERE user_id = ? AND model_id = ?
            """, (user_id, model_id))
            row = cursor.fetchone()
            if row:
                return {
                    "current_mood": row[0],
                    "energy_level": row[1],
                    "happiness_level": row[2],
                    "stress_level": row[3]
                }
            return {"current_mood": "neutral", "energy_level": 0.8, 
                   "happiness_level": 0.7, "stress_level": 0.2}
    
    def update_avatar_state(self, user_id: str, model_id: str = "default", **kwargs):
        """Update avatar emotional state"""
        with get_personality_connection() as conn:
            cursor = conn.cursor()
            current = self.get_avatar_state(user_id, model_id)
            
            # Update with new values
            for key, value in kwargs.items():
                if key in current:
                    current[key] = value
            
            cursor.execute("""
                INSERT OR REPLACE INTO avatar_states 
                (user_id, model_id, current_mood, energy_level, happiness_level, stress_level)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, model_id, current["current_mood"], current["energy_level"],
                 current["happiness_level"], current["stress_level"]))
            conn.commit()

def init_databases():
    """Initialize all databases with proper schemas"""
    # Ensure directories exist
    databases_dir = get_user_data_dir() / "databases"
    databases_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize Live2D database
    with get_live2d_connection() as conn:
        cursor = conn.cursor()
        
        # Create live2d_models table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS live2d_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL UNIQUE,
                model_path TEXT NOT NULL,
                config_file TEXT NOT NULL,
                model_type TEXT DEFAULT 'Live2D_v4',
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create live2d_motions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS live2d_motions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id INTEGER NOT NULL,
                motion_group TEXT NOT NULL,
                motion_index INTEGER NOT NULL,
                motion_name TEXT,
                motion_type TEXT DEFAULT 'body',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (model_id) REFERENCES live2d_models (id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_motions_model_id ON live2d_motions(model_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_motions_type ON live2d_motions(motion_type)")
        
        conn.commit()
        logger.info("Live2D database initialized")
    
    # Initialize Conversations database with model-specific tables
    with get_conversations_connection() as conn:
        cursor = conn.cursor()
        
        # Check if conversations table exists and has model_id column
        cursor.execute("PRAGMA table_info(conversations)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'model_id' not in columns:
            # Create new conversations table with model_id
            cursor.execute("DROP TABLE IF EXISTS conversations_old")
            if 'conversations' in [row[0] for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
                cursor.execute("ALTER TABLE conversations RENAME TO conversations_old")
            
            cursor.execute("""
                CREATE TABLE conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    model_id TEXT NOT NULL DEFAULT 'default',
                    message_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    emotion_detected TEXT,
                    response_time_ms INTEGER
                )
            """)
            
            # Migrate old data if exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='conversations_old'")
            if cursor.fetchone():
                cursor.execute("""
                    INSERT INTO conversations (user_id, model_id, message_type, content, timestamp, emotion_detected, response_time_ms)
                    SELECT 
                        COALESCE(user_id, 'default_user') as user_id,
                        'default' as model_id,
                        message_type,
                        content,
                        timestamp,
                        emotion_detected,
                        response_time_ms
                    FROM conversations_old
                """)
                cursor.execute("DROP TABLE conversations_old")
                logger.info("Migrated existing conversation data")
        
        # Create or update other tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                model_id TEXT NOT NULL DEFAULT 'default',
                memory_type TEXT NOT NULL,
                key_topic TEXT NOT NULL,
                value_content TEXT NOT NULL,
                importance_score REAL DEFAULT 0.5,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0
            )
        """)
        
        # Create conversation summaries with model isolation
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                model_id TEXT NOT NULL DEFAULT 'default',
                date_range TEXT NOT NULL,
                summary_text TEXT NOT NULL,
                key_topics TEXT,
                emotional_tone TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create session contexts with model isolation
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_contexts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                model_id TEXT NOT NULL DEFAULT 'default',
                session_id TEXT NOT NULL,
                messages TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, model_id, session_id) ON CONFLICT REPLACE
            )
        """)
        
        # Create LLM cache with model awareness
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS llm_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                input_hash TEXT NOT NULL,
                model_id TEXT DEFAULT 'default',
                response TEXT NOT NULL,
                model_name TEXT,
                temperature REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME
            )
        """)
        
        # Create indexes for performance
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conv_user_model ON conversations(user_id, model_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_mem_user_model ON memories(user_id, model_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_mem_topic ON memories(key_topic)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_context_user_model ON conversation_contexts(user_id, model_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_hash_model ON llm_cache(input_hash, model_id)")
        except Exception as e:
            logger.warning(f"Some indexes may already exist: {e}")
        
        conn.commit()
        logger.info("Conversations database initialized")
    
    # Initialize Personality database with model-specific data
    with get_personality_connection() as conn:
        cursor = conn.cursor()
        
        # Create model personalities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_personalities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                base_traits TEXT NOT NULL,
                current_traits TEXT NOT NULL,
                description TEXT,
                background_story TEXT,
                favorite_things TEXT,
                personality_notes TEXT,
                appearance_notes TEXT,
                config_source TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create dynamic personality states (real-time adaptations)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS personality_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                model_id TEXT NOT NULL,
                trait_name TEXT NOT NULL,
                base_value REAL NOT NULL,
                current_value REAL NOT NULL,
                adaptation_reason TEXT,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, model_id, trait_name) ON CONFLICT REPLACE
            )
        """)
        
        # Create personality interactions log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS personality_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                model_id TEXT NOT NULL,
                interaction_type TEXT NOT NULL,
                trait_affected TEXT,
                value_change REAL,
                reason TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create bonding progress per model
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bonding_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                model_id TEXT NOT NULL,
                bond_level INTEGER DEFAULT 1,
                experience_points INTEGER DEFAULT 0,
                relationship_stage TEXT DEFAULT 'stranger',
                trust_level REAL DEFAULT 0.5,
                affection_level REAL DEFAULT 0.5,
                last_interaction DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, model_id) ON CONFLICT REPLACE
            )
        """)
        
        # Create avatar states per model
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS avatar_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                model_id TEXT NOT NULL,
                current_mood TEXT DEFAULT 'neutral',
                energy_level REAL DEFAULT 0.8,
                happiness_level REAL DEFAULT 0.7,
                stress_level REAL DEFAULT 0.2,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, model_id) ON CONFLICT REPLACE
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pers_model ON model_personalities(model_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_states_user_model ON personality_states(user_id, model_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bond_user_model ON bonding_progress(user_id, model_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_avatar_user_model ON avatar_states(user_id, model_id)")
        
        conn.commit()
        logger.info("Personality database initialized")
    
    logger.info("All databases initialized")

if __name__ == "__main__":
    # Test the database connections
    logging.basicConfig(level=logging.INFO)
    init_databases()
    
    with get_live2d_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM live2d_models")
        model_count = cursor.fetchone()[0]
        print(f"Live2D models in database: {model_count}")
