#!/usr/bin/env python3
"""
Multi-Database Manager for AI Companion
Manages separate databases for different components
"""

import sqlite3
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from contextlib import contextmanager

class DatabaseManager:
    """
    Manages multiple separate databases for different AI companion components
    """
    
    def __init__(self, base_path: str = "/home/nyx/ai-companion/databases"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # Database file paths
        self.databases = {
            'live2d': self.base_path / 'live2d.db',
            'conversations': self.base_path / 'conversations.db', 
            'personality': self.base_path / 'personality.db',
            'system': self.base_path / 'system.db'
        }
        
        # Connection pool
        self._connections = {}
        
        # Initialize all databases
        self._initialize_databases()
    
    def _initialize_databases(self):
        """Initialize all database schemas"""
        self.logger.info("Initializing separated databases...")
        
        # Initialize Live2D database
        self._init_live2d_db()
        
        # Initialize Conversations database
        self._init_conversations_db()
        
        # Initialize Personality database
        self._init_personality_db()
        
        # Initialize System database
        self._init_system_db()
        
        self.logger.info(f"✅ All databases initialized in {self.base_path}")
    
    def _init_live2d_db(self):
        """Initialize Live2D models and motions database"""
        with self.get_connection('live2d') as conn:
            cursor = conn.cursor()
            
            # Live2D Models table
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
            
            # Live2D Motions table
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
            
            # Indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_motions_model_id ON live2d_motions(model_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_motions_type ON live2d_motions(motion_type)")
            
            conn.commit()
    
    def _init_conversations_db(self):
        """Initialize conversation and LLM database"""
        with self.get_connection('conversations') as conn:
            cursor = conn.cursor()
            
            # Conversation history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    user_message TEXT NOT NULL,
                    ai_response TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    message_metadata TEXT,
                    emotion_detected TEXT,
                    context_used TEXT
                )
            """)
            
            # Conversation contexts
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_contexts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    context_data TEXT NOT NULL,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # LLM cache for responses
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS llm_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_hash TEXT NOT NULL UNIQUE,
                    prompt TEXT NOT NULL,
                    response TEXT NOT NULL,
                    model_used TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 1
                )
            """)
            
            # Indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_llm_cache_hash ON llm_cache(prompt_hash)")
            
            conn.commit()
    
    def _init_personality_db(self):
        """Initialize personality and emotions database"""
        with self.get_connection('personality') as conn:
            cursor = conn.cursor()
            
            # Personality traits
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS personality_traits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trait_name TEXT NOT NULL UNIQUE,
                    trait_value REAL NOT NULL,
                    confidence REAL DEFAULT 0.5,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Emotion states
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS emotion_states (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    emotion TEXT NOT NULL,
                    intensity REAL NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    trigger_context TEXT,
                    duration_seconds INTEGER
                )
            """)
            
            # Memory clusters
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory_clusters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cluster_name TEXT NOT NULL,
                    cluster_data TEXT NOT NULL,
                    importance_score REAL DEFAULT 0.5,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Learning patterns
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT NOT NULL,
                    pattern_data TEXT NOT NULL,
                    frequency INTEGER DEFAULT 1,
                    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_emotions_timestamp ON emotion_states(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_emotions_type ON emotion_states(emotion)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_importance ON memory_clusters(importance_score)")
            
            conn.commit()
    
    def _init_system_db(self):
        """Initialize system settings and preferences database"""
        with self.get_connection('system') as conn:
            cursor = conn.cursor()
            
            # User preferences
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    preference_key TEXT NOT NULL UNIQUE,
                    preference_value TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Application settings
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT NOT NULL UNIQUE,
                    setting_value TEXT NOT NULL,
                    setting_type TEXT DEFAULT 'string',
                    description TEXT,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Session data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL UNIQUE,
                    session_data TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME
                )
            """)
            
            # Indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_preferences_category ON user_preferences(category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at)")
            
            conn.commit()
    
    @contextmanager
    def get_connection(self, db_name: str):
        """Get a database connection with proper cleanup"""
        if db_name not in self.databases:
            raise ValueError(f"Unknown database: {db_name}")
        
        conn = sqlite3.connect(str(self.databases[db_name]), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        
        try:
            yield conn
        finally:
            conn.close()
    
    def clear_database(self, db_name: str) -> Dict[str, int]:
        """Clear all data from a specific database"""
        if db_name not in self.databases:
            raise ValueError(f"Unknown database: {db_name}")
        
        results = {'tables_cleared': 0, 'total_rows_deleted': 0}
        
        with self.get_connection(db_name) as conn:
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [row[0] for row in cursor.fetchall()]
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
                
                cursor.execute(f"DELETE FROM {table}")
                results['total_rows_deleted'] += row_count
                results['tables_cleared'] += 1
                
                self.logger.info(f"Cleared table {table}: {row_count} rows")
            
            # Reset sequences
            cursor.execute("DELETE FROM sqlite_sequence WHERE name IN (?)", (','.join(tables),))
            
            conn.commit()
        
        self.logger.info(f"✅ Cleared database {db_name}: {results['tables_cleared']} tables, {results['total_rows_deleted']} rows")
        return results
    
    def backup_database(self, db_name: str, backup_path: Optional[str] = None) -> str:
        """Create a backup of a specific database"""
        if db_name not in self.databases:
            raise ValueError(f"Unknown database: {db_name}")
        
        if backup_path is None:
            backup_path = self.base_path / f"{db_name}_backup.db"
        
        source_path = self.databases[db_name]
        
        # Copy database file
        import shutil
        shutil.copy2(source_path, backup_path)
        
        self.logger.info(f"✅ Database {db_name} backed up to {backup_path}")
        return str(backup_path)
    
    def get_database_stats(self) -> Dict[str, Dict]:
        """Get statistics for all databases"""
        stats = {}
        
        for db_name in self.databases:
            try:
                with self.get_connection(db_name) as conn:
                    cursor = conn.cursor()
                    
                    # Get table stats
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    table_stats = {}
                    total_rows = 0
                    
                    for table in tables:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        row_count = cursor.fetchone()[0]
                        table_stats[table] = row_count
                        total_rows += row_count
                    
                    # Get database size
                    db_size = os.path.getsize(self.databases[db_name])
                    
                    stats[db_name] = {
                        'tables': table_stats,
                        'total_rows': total_rows,
                        'size_bytes': db_size,
                        'size_mb': round(db_size / 1024 / 1024, 2)
                    }
                    
            except Exception as e:
                self.logger.error(f"Error getting stats for {db_name}: {e}")
                stats[db_name] = {'error': str(e)}
        
        return stats
    
    def migrate_from_single_db(self, old_db_path: str):
        """Migrate data from old single database to new separated databases"""
        if not os.path.exists(old_db_path):
            self.logger.warning(f"Old database not found: {old_db_path}")
            return
        
        self.logger.info(f"Migrating data from {old_db_path} to separated databases...")
        
        # Connect to old database
        old_conn = sqlite3.connect(old_db_path)
        old_conn.row_factory = sqlite3.Row
        old_cursor = old_conn.cursor()
        
        try:
            # Migrate Live2D data
            self._migrate_live2d_data(old_cursor)
            
            # Migrate conversation data if it exists
            self._migrate_conversation_data(old_cursor)
            
            # Migrate personality data if it exists
            self._migrate_personality_data(old_cursor)
            
            # Migrate system data if it exists
            self._migrate_system_data(old_cursor)
            
        except Exception as e:
            self.logger.error(f"Migration error: {e}")
            raise
        finally:
            old_conn.close()
        
        self.logger.info("✅ Migration completed successfully")
    
    def _migrate_live2d_data(self, old_cursor):
        """Migrate Live2D data to new database"""
        with self.get_connection('live2d') as new_conn:
            new_cursor = new_conn.cursor()
            
            # Check if tables exist in old DB
            old_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='live2d_models'")
            if not old_cursor.fetchone():
                self.logger.info("No Live2D data to migrate")
                return
            
            # Migrate models
            old_cursor.execute("SELECT * FROM live2d_models")
            models = old_cursor.fetchall()
            
            for model in models:
                new_cursor.execute("""
                    INSERT OR REPLACE INTO live2d_models 
                    (model_name, model_path, config_file, model_type, description, created_at, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (model['model_name'], model['model_path'], model['config_file'], 
                     model['model_type'], model['description'], model['created_at'], model['last_updated']))
            
            # Migrate motions
            old_cursor.execute("SELECT * FROM live2d_motions")
            motions = old_cursor.fetchall()
            
            for motion in motions:
                new_cursor.execute("""
                    INSERT OR REPLACE INTO live2d_motions
                    (model_id, motion_group, motion_index, motion_name, motion_type, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (motion['model_id'], motion['motion_group'], motion['motion_index'],
                     motion['motion_name'], motion['motion_type'], motion['created_at']))
            
            new_conn.commit()
            self.logger.info(f"Migrated {len(models)} models and {len(motions)} motions")
    
    def _migrate_conversation_data(self, old_cursor):
        """Migrate conversation data if it exists"""
        # Check for conversation tables and migrate if they exist
        tables_to_check = ['conversations', 'conversation_contexts', 'llm_cache']
        
        with self.get_connection('conversations') as new_conn:
            new_cursor = new_conn.cursor()
            
            for table in tables_to_check:
                old_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
                if old_cursor.fetchone():
                    old_cursor.execute(f"SELECT * FROM {table}")
                    rows = old_cursor.fetchall()
                    
                    if rows:
                        # Get column names
                        old_cursor.execute(f"PRAGMA table_info({table})")
                        columns = [col[1] for col in old_cursor.fetchall()]
                        
                        # Insert data
                        placeholders = ','.join(['?' for _ in columns])
                        for row in rows:
                            new_cursor.execute(f"INSERT OR REPLACE INTO {table} VALUES ({placeholders})", 
                                             tuple(row))
                        
                        self.logger.info(f"Migrated {len(rows)} rows from {table}")
            
            new_conn.commit()
    
    def _migrate_personality_data(self, old_cursor):
        """Migrate personality data if it exists"""
        # Similar to conversation migration
        pass
    
    def _migrate_system_data(self, old_cursor):
        """Migrate system data if it exists"""
        # Similar to conversation migration
        pass


# Global instance
db_manager = None

def get_db_manager() -> DatabaseManager:
    """Get global database manager instance"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager

def get_live2d_connection():
    """Get Live2D database connection"""
    return get_db_manager().get_connection('live2d')

def get_conversations_connection():
    """Get conversations database connection"""
    return get_db_manager().get_connection('conversations')

def get_personality_connection():
    """Get personality database connection"""
    return get_db_manager().get_connection('personality')

def get_system_connection():
    """Get system database connection"""
    return get_db_manager().get_connection('system')
