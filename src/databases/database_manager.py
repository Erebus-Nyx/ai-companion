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
    return Path.home() / ".local/share/ai-companion"

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
    
    # Other databases would be initialized here if needed
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
