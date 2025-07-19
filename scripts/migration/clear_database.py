#!/usr/bin/env python3
"""
Clear the Live2D database completely
"""

import sqlite3
import os

def clear_database():
    """Clear all Live2D data from the database"""
    db_path = '/home/nyx/ai2d_chat/src/ai2d_chat.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    print("🗑️ === CLEARING DATABASE ===")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check current counts
    cursor.execute('SELECT COUNT(*) FROM live2d_motions')
    motion_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM live2d_models')
    model_count = cursor.fetchone()[0]
    
    print(f"Current: {model_count} models, {motion_count} motions")
    
    # Clear all data
    print("🧹 Clearing all motions...")
    cursor.execute('DELETE FROM live2d_motions')
    deleted_motions = cursor.rowcount
    
    print("🧹 Clearing all models...")
    cursor.execute('DELETE FROM live2d_models')
    deleted_models = cursor.rowcount
    
    # Reset auto-increment counters
    cursor.execute('DELETE FROM sqlite_sequence WHERE name IN ("live2d_models", "live2d_motions")')
    
    conn.commit()
    conn.close()
    
    print(f"✅ Cleared {deleted_models} models and {deleted_motions} motions")
    print("✅ Database is now empty and ready for fresh import")

if __name__ == "__main__":
    response = input("⚠️ This will DELETE ALL Live2D data from the database. Continue? (y/N): ")
    if response.lower() == 'y':
        clear_database()
    else:
        print("❌ Operation cancelled")
