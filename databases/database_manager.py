"""
Database Manager for AI Companion - Separated Database Architecture
Provides connection functions for the different databases.
"""

import sqlite3
from pathlib import Path
import logging
import os

logger = logging.getLogger(__name__)

def get_user_data_dir() -> Path:
    """Get the user data directory for AI Companion using config manager"""
    try:
        # Import here to avoid circular imports
        from config.config_manager import ConfigManager
        config_manager = ConfigManager()
        return config_manager.data_dir
    except ImportError:
        # Fallback if config manager not available
        logger.warning("Config manager not available, using fallback path")
        return Path.home() / ".local/share/ai2d_chat"

def get_database_path(db_name: str) -> Path:
    """Get database path using config manager"""
    try:
        from config.config_manager import ConfigManager
        config_manager = ConfigManager()
        return config_manager.get_database_path(db_name)
    except ImportError:
        # Fallback if config manager not available
        logger.warning("Config manager not available, using fallback database path")
        return get_user_data_dir() / "databases" / db_name

def get_live2d_connection():
    """Get connection to the Live2D database"""
    db_path = get_database_path("live2d.db")
    # Ensure the parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row  # Enable dictionary-like access to rows
    return conn

def get_conversations_connection():
    """Get connection to the conversations database"""
    db_path = get_database_path("conversations.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(db_path))

def get_personality_connection():
    """Get connection to the personality database"""
    db_path = get_database_path("personality.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(db_path))

def get_system_connection():
    """Get connection to the system database"""
    db_path = get_database_path("system.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(db_path))

def get_users_connection():
    """Get connection to the users database"""
    db_path = get_database_path("users.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(db_path))

def get_user_profiles_connection():
    """Get connection to the user profiles database"""
    db_path = get_database_path("user_profiles.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(db_path))

def get_user_sessions_connection():
    """Get connection to the user sessions database"""
    db_path = get_database_path("user_sessions.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(db_path))

def get_ai2d_chat_connection():
    """Get connection to the main AI2D chat database"""
    db_path = get_database_path("ai2d_chat.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
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
        
    def get_users_connection(self):
        """Get users database connection"""
        return get_users_connection()
        
    def get_user_profiles_connection(self):
        """Get user profiles database connection"""
        return get_user_profiles_connection()
        
    def get_user_sessions_connection(self):
        """Get user sessions database connection"""
        return get_user_sessions_connection()
        
    def get_ai2d_chat_connection(self):
        """Get main AI2D chat database connection"""
        return get_ai2d_chat_connection()
        
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
        
        # Create conversation_history table for chat routes compatibility
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                avatar_id TEXT,
                user_message TEXT,
                ai_response TEXT,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
    
    # Initialize System database
    system_db_path = get_user_data_dir() / "databases" / "system.db"
    with sqlite3.connect(str(system_db_path)) as conn:
        cursor = conn.cursor()
        
        # Create system configuration table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key TEXT NOT NULL UNIQUE,
                config_value TEXT NOT NULL,
                config_type TEXT DEFAULT 'string',
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create system performance metrics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                metric_unit TEXT,
                recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create system logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_level TEXT NOT NULL,
                component TEXT NOT NULL,
                message TEXT NOT NULL,
                details TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_config_key ON system_config(config_key)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_name ON system_metrics(metric_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_level ON system_logs(log_level)")
        
        conn.commit()
        logger.info("System database initialized")
    
    # Initialize Users database
    users_db_path = get_user_data_dir() / "databases" / "users.db"
    with sqlite3.connect(str(users_db_path)) as conn:
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT UNIQUE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                display_name TEXT,
                is_active BOOLEAN DEFAULT 1,
                is_admin BOOLEAN DEFAULT 0,
                permissions TEXT DEFAULT '["chat", "voice", "model_switch"]',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Check if display_name column exists, add if missing (migration support)
        try:
            cursor.execute("SELECT display_name FROM users LIMIT 1")
        except sqlite3.OperationalError:
            # Column doesn't exist, add it
            cursor.execute("ALTER TABLE users ADD COLUMN display_name TEXT")
            print("Added missing display_name column to users table")
        
        # Create user authentication tokens
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auth_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                token_type TEXT DEFAULT 'session',
                expires_at DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tokens_user ON auth_tokens(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tokens_hash ON auth_tokens(token_hash)")
        
        conn.commit()
        logger.info("Users database initialized")
    
    # Initialize User Profiles database
    user_profiles_db_path = get_user_data_dir() / "databases" / "user_profiles.db"
    with sqlite3.connect(str(user_profiles_db_path)) as conn:
        cursor = conn.cursor()
        
        # Create user profiles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                display_name TEXT,
                age INTEGER,
                avatar_preferences TEXT,
                conversation_settings TEXT,
                privacy_settings TEXT,
                theme_preferences TEXT,
                language_preference TEXT DEFAULT 'en',
                timezone TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        
        # Create user preferences table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                preference_key TEXT NOT NULL,
                preference_value TEXT NOT NULL,
                preference_type TEXT DEFAULT 'string',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, preference_key) ON CONFLICT REPLACE,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_profiles_user ON user_profiles(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_preferences_user ON user_preferences(user_id)")
        
        conn.commit()
        logger.info("User profiles database initialized")
    
    # Initialize User Sessions database
    user_sessions_db_path = get_user_data_dir() / "databases" / "user_sessions.db"
    with sqlite3.connect(str(user_sessions_db_path)) as conn:
        cursor = conn.cursor()
        
        # Create user sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_id TEXT NOT NULL UNIQUE,
                session_data TEXT,
                ip_address TEXT,
                user_agent TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        
        # Create active sessions view for performance
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                activity_data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES user_sessions (session_id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_active ON user_sessions(is_active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_activities_session ON session_activities(session_id)")
        
        conn.commit()
        logger.info("User sessions database initialized")
    
    # Initialize Main AI2D Chat database
    ai2d_chat_db_path = get_user_data_dir() / "databases" / "ai2d_chat.db"
    with sqlite3.connect(str(ai2d_chat_db_path)) as conn:
        cursor = conn.cursor()
        
        # Create application state table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                state_key TEXT NOT NULL UNIQUE,
                state_value TEXT NOT NULL,
                state_type TEXT DEFAULT 'string',
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create application settings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_category TEXT NOT NULL,
                setting_key TEXT NOT NULL,
                setting_value TEXT NOT NULL,
                setting_type TEXT DEFAULT 'string',
                is_user_configurable BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(setting_category, setting_key) ON CONFLICT REPLACE
            )
        """)
        
        # Create error logs specific to application
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_type TEXT NOT NULL,
                error_message TEXT NOT NULL,
                error_traceback TEXT,
                user_id INTEGER,
                session_id TEXT,
                component TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_state_key ON app_state(state_key)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_settings_category ON app_settings(setting_category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_errors_type ON app_errors(error_type)")
        
        conn.commit()
        logger.info("AI2D Chat database initialized")
    
    logger.info("All databases initialized")

def verify_database_schemas():
    """Verify that all databases have been created with proper schemas"""
    verification_results = {}
    
    # Expected tables for each database
    expected_schemas = {
        "live2d.db": ["live2d_models", "live2d_motions"],
        "conversations.db": ["conversations", "memories", "conversation_summaries", "conversation_contexts", "llm_cache"],
        "personality.db": ["model_personalities", "personality_states", "personality_interactions", "bonding_progress", "avatar_states"],
        "system.db": ["system_config", "system_metrics", "system_logs"],
        "users.db": ["users", "auth_tokens"],
        "user_profiles.db": ["user_profiles", "user_preferences"],
        "user_sessions.db": ["user_sessions", "session_activities"],
        "ai2d_chat.db": ["app_state", "app_settings", "app_errors"]
    }
    
    databases_dir = get_user_data_dir() / "databases"
    
    for db_name, expected_tables in expected_schemas.items():
        db_path = databases_dir / db_name
        verification_results[db_name] = {
            "exists": db_path.exists(),
            "tables": [],
            "missing_tables": [],
            "schema_valid": False,
            "detailed_schema": {}
        }
        
        if db_path.exists():
            try:
                with sqlite3.connect(str(db_path)) as conn:
                    cursor = conn.cursor()
                    
                    # Get all table names
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                    actual_tables = [row[0] for row in cursor.fetchall()]
                    
                    verification_results[db_name]["tables"] = actual_tables
                    verification_results[db_name]["missing_tables"] = [
                        table for table in expected_tables if table not in actual_tables
                    ]
                    verification_results[db_name]["schema_valid"] = len(verification_results[db_name]["missing_tables"]) == 0
                    
                    # Get detailed schema information for each table
                    for table_name in actual_tables:
                        verification_results[db_name]["detailed_schema"][table_name] = {}
                        
                        # Get table schema (CREATE statement)
                        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                        create_sql = cursor.fetchone()
                        if create_sql:
                            verification_results[db_name]["detailed_schema"][table_name]["create_sql"] = create_sql[0]
                        
                        # Get column information
                        cursor.execute(f"PRAGMA table_info({table_name})")
                        columns = cursor.fetchall()
                        verification_results[db_name]["detailed_schema"][table_name]["columns"] = [
                            {
                                "cid": col[0],
                                "name": col[1],
                                "type": col[2],
                                "notnull": bool(col[3]),
                                "default_value": col[4],
                                "pk": bool(col[5])
                            }
                            for col in columns
                        ]
                        
                        # Get indexes
                        cursor.execute(f"PRAGMA index_list({table_name})")
                        indexes = cursor.fetchall()
                        verification_results[db_name]["detailed_schema"][table_name]["indexes"] = [
                            {
                                "seq": idx[0],
                                "name": idx[1],
                                "unique": bool(idx[2]),
                                "origin": idx[3],
                                "partial": bool(idx[4])
                            }
                            for idx in indexes
                        ]
                        
                        # Get foreign keys
                        cursor.execute(f"PRAGMA foreign_key_list({table_name})")
                        foreign_keys = cursor.fetchall()
                        verification_results[db_name]["detailed_schema"][table_name]["foreign_keys"] = [
                            {
                                "id": fk[0],
                                "seq": fk[1],
                                "table": fk[2],
                                "from": fk[3],
                                "to": fk[4],
                                "on_update": fk[5],
                                "on_delete": fk[6],
                                "match": fk[7]
                            }
                            for fk in foreign_keys
                        ]
                    
            except Exception as e:
                logger.error(f"Error verifying {db_name}: {e}")
                verification_results[db_name]["error"] = str(e)
    
    return verification_results

def print_database_verification_report(verification_results, show_detailed_schemas=False):
    """Print a detailed verification report"""
    print("\n📊 Database Schema Verification Report")
    print("=" * 60)
    
    total_dbs = len(verification_results)
    valid_dbs = sum(1 for result in verification_results.values() if result.get("schema_valid", False))
    
    print(f"📈 Overall Status: {valid_dbs}/{total_dbs} databases verified")
    
    for db_name, result in verification_results.items():
        status_icon = "✅" if result.get("schema_valid", False) else "❌"
        print(f"\n{status_icon} {db_name}")
        
        if not result["exists"]:
            print(f"   ❌ Database file not found")
        elif "error" in result:
            print(f"   ❌ Error: {result['error']}")
        else:
            print(f"   📋 Tables found: {len(result['tables'])}")
            if result["tables"]:
                for table in result["tables"]:
                    print(f"      • {table}")
            
            if result["missing_tables"]:
                print(f"   ⚠️  Missing tables: {len(result['missing_tables'])}")
                for table in result["missing_tables"]:
                    print(f"      • {table}")
            
            # Show detailed schema if requested
            if show_detailed_schemas and "detailed_schema" in result:
                print(f"\n   🔍 Detailed Schema for {db_name}:")
                for table_name, schema_info in result["detailed_schema"].items():
                    print(f"\n      📋 Table: {table_name}")
                    
                    # Show CREATE statement
                    if "create_sql" in schema_info:
                        print(f"         CREATE SQL:")
                        # Format the CREATE statement for better readability
                        create_sql = schema_info["create_sql"]
                        lines = create_sql.split('\n')
                        for line in lines:
                            print(f"           {line.strip()}")
                    
                    # Show columns
                    if "columns" in schema_info:
                        print(f"         Columns ({len(schema_info['columns'])}):")
                        for col in schema_info["columns"]:
                            pk_indicator = " [PK]" if col["pk"] else ""
                            null_indicator = " NOT NULL" if col["notnull"] else ""
                            default_indicator = f" DEFAULT {col['default_value']}" if col["default_value"] is not None else ""
                            print(f"           • {col['name']}: {col['type']}{pk_indicator}{null_indicator}{default_indicator}")
                    
                    # Show indexes
                    if "indexes" in schema_info and schema_info["indexes"]:
                        print(f"         Indexes ({len(schema_info['indexes'])}):")
                        for idx in schema_info["indexes"]:
                            unique_indicator = " [UNIQUE]" if idx["unique"] else ""
                            print(f"           • {idx['name']}{unique_indicator}")
                    
                    # Show foreign keys
                    if "foreign_keys" in schema_info and schema_info["foreign_keys"]:
                        print(f"         Foreign Keys ({len(schema_info['foreign_keys'])}):")
                        for fk in schema_info["foreign_keys"]:
                            print(f"           • {fk['from']} → {fk['table']}.{fk['to']} (ON DELETE {fk['on_delete']})")
    
    if valid_dbs == total_dbs:
        print(f"\n🎉 All {total_dbs} databases verified successfully!")
        return True
    else:
        print(f"\n⚠️  {total_dbs - valid_dbs} database(s) have schema issues")
        return False

def print_detailed_schema_report(verification_results):
    """Print a comprehensive schema report for manual inspection"""
    print("\n🔬 Comprehensive Database Schema Analysis")
    print("=" * 80)
    
    for db_name, result in verification_results.items():
        if not result.get("exists") or "detailed_schema" not in result:
            continue
            
        print(f"\n{'='*20} {db_name.upper()} {'='*20}")
        
        for table_name, schema_info in result["detailed_schema"].items():
            print(f"\n📋 TABLE: {table_name}")
            print("-" * 50)
            
            # Full CREATE statement
            if "create_sql" in schema_info:
                print("CREATE STATEMENT:")
                print(schema_info["create_sql"])
                print()
            
            # Column details
            if "columns" in schema_info:
                print("COLUMN STRUCTURE:")
                print(f"{'Name':<20} {'Type':<15} {'Null':<6} {'Default':<15} {'PK':<4}")
                print("-" * 65)
                for col in schema_info["columns"]:
                    name = col["name"]
                    data_type = col["type"]
                    nullable = "NO" if col["notnull"] else "YES"
                    default = str(col["default_value"]) if col["default_value"] is not None else "NULL"
                    primary_key = "YES" if col["pk"] else "NO"
                    print(f"{name:<20} {data_type:<15} {nullable:<6} {default:<15} {primary_key:<4}")
                print()
            
            # Indexes
            if "indexes" in schema_info and schema_info["indexes"]:
                print("INDEXES:")
                for idx in schema_info["indexes"]:
                    unique_text = " (UNIQUE)" if idx["unique"] else ""
                    print(f"  • {idx['name']}{unique_text}")
                print()
            
            # Foreign keys
            if "foreign_keys" in schema_info and schema_info["foreign_keys"]:
                print("FOREIGN KEY CONSTRAINTS:")
                for fk in schema_info["foreign_keys"]:
                    print(f"  • {fk['from']} REFERENCES {fk['table']}({fk['to']})")
                    print(f"    ON UPDATE {fk['on_update']}, ON DELETE {fk['on_delete']}")
                print()
        
        print(f"Total tables in {db_name}: {len(result['detailed_schema'])}")
        print("=" * 60)

if __name__ == "__main__":
    # Test the database connections
    logging.basicConfig(level=logging.INFO)
    init_databases()
    
    # Verify schemas
    verification_results = verify_database_schemas()
    print_database_verification_report(verification_results)
    
    # Print detailed schema report for manual inspection
    print_detailed_schema_report(verification_results)
    
    with get_live2d_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM live2d_models")
        model_count = cursor.fetchone()[0]
        print(f"\nLive2D models in database: {model_count}")
