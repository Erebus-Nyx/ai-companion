#!/usr/bin/env python3
"""
Database migration script to add preview_image column to live2d_models table
"""

import sqlite3
import os
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def migrate_database():
    """Add preview_image column to live2d_models table"""
    db_path = "databases/live2d.db"
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if preview_image column exists
        cursor.execute("PRAGMA table_info(live2d_models)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'preview_image' not in columns:
            print("Adding preview_image column to live2d_models table...")
            cursor.execute("ALTER TABLE live2d_models ADD COLUMN preview_image TEXT")
            conn.commit()
            print("✓ preview_image column added successfully")
        else:
            print("✓ preview_image column already exists")
        
        # Verify the column was added
        cursor.execute("PRAGMA table_info(live2d_models)")
        columns_after = [column[1] for column in cursor.fetchall()]
        print(f"Current columns: {columns_after}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error migrating database: {e}")
        return False

if __name__ == "__main__":
    print("Live2D Database Migration - Adding preview_image column")
    print("=" * 50)
    
    success = migrate_database()
    
    if success:
        print("✓ Migration completed successfully!")
    else:
        print("✗ Migration failed!")
        sys.exit(1)
