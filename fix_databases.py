#!/usr/bin/env python3
"""
Database Fix Script - Reinitialize databases with correct schema
"""

import sqlite3
import sys
import os
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def fix_databases():
    """Fix database schema issues"""
    print("🔧 Fixing database schema issues...")
    
    try:
        # Import after adding to path
        from databases.database_manager import init_databases, get_user_data_dir
        from routes.app_routes_users import init_user_tables
        
        print("✅ Database modules imported successfully")
        
        # Initialize databases with correct schema
        print("🔄 Reinitializing databases...")
        init_databases()
        print("✅ Main databases initialized")
        
        # Initialize user tables with display_name column
        print("🔄 Initializing user tables...")
        init_user_tables()
        print("✅ User tables initialized")
        
        # Verify the databases
        print("🔍 Verifying database schema...")
        
        # Check users table
        users_db_path = get_user_data_dir() / "databases" / "users.db"
        if users_db_path.exists():
            with sqlite3.connect(str(users_db_path)) as conn:
                cursor = conn.cursor()
                
                # Check if display_name column exists
                cursor.execute("PRAGMA table_info(users)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'display_name' in columns:
                    print("✅ Users table has display_name column")
                else:
                    print("❌ Users table missing display_name column")
                    # Add the column
                    try:
                        cursor.execute("ALTER TABLE users ADD COLUMN display_name TEXT")
                        print("✅ Added display_name column to users table")
                    except sqlite3.OperationalError as e:
                        if "duplicate column name" not in str(e):
                            print(f"❌ Failed to add display_name column: {e}")
        
        # Check conversations database
        conversations_db_path = get_user_data_dir() / "databases" / "conversations.db"
        if conversations_db_path.exists():
            with sqlite3.connect(str(conversations_db_path)) as conn:
                cursor = conn.cursor()
                
                # Check if conversation_history table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='conversation_history'")
                table_exists = cursor.fetchone() is not None
                
                if table_exists:
                    print("✅ Conversation_history table exists")
                else:
                    print("❌ Conversation_history table missing, creating...")
                    cursor.execute("""
                        CREATE TABLE conversation_history (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id TEXT,
                            avatar_id TEXT,
                            user_message TEXT,
                            ai_response TEXT,
                            metadata TEXT,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    print("✅ Created conversation_history table")
        
        print("🎉 Database fixes completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database fix failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_databases()
    sys.exit(0 if success else 1)
