#!/usr/bin/env python3
"""
Migrate from single database to separated databases and clear only Live2D data
"""

import sys
import os
from pathlib import Path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.database_manager import DatabaseManager

def migrate_and_clear_live2d():
    """Migrate existing data to separated databases and clear only Live2D data"""
    
    # Paths - use relative path to find old database
    script_dir = Path(__file__).parent.parent.parent  # Go up to repo root
    old_db_path = str(script_dir / 'src' / 'ai2d_chat.db')
    
    print("🔄 === MIGRATING TO SEPARATED DATABASES ===")
    
    # Initialize new database manager
    db_manager = DatabaseManager()
    
    # Migrate existing data if old database exists
    if os.path.exists(old_db_path):
        print(f"📦 Migrating data from {old_db_path}")
        try:
            db_manager.migrate_from_single_db(old_db_path)
            print("✅ Migration completed successfully")
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            return False
    else:
        print("ℹ️ No existing database found, starting fresh")
    
    # Show database stats
    print("\n📊 Database Statistics:")
    stats = db_manager.get_database_stats()
    for db_name, db_stats in stats.items():
        if 'error' in db_stats:
            print(f"  {db_name}: Error - {db_stats['error']}")
        else:
            print(f"  {db_name}: {db_stats['total_rows']} rows, {db_stats['size_mb']} MB")
            for table, count in db_stats['tables'].items():
                print(f"    {table}: {count} rows")
    
    # Clear only Live2D database
    print(f"\n🗑️ Clearing Live2D database only...")
    try:
        results = db_manager.clear_database('live2d')
        print(f"✅ Cleared Live2D database: {results['tables_cleared']} tables, {results['total_rows_deleted']} rows")
    except Exception as e:
        print(f"❌ Failed to clear Live2D database: {e}")
        return False
    
    # Show updated stats
    print("\n📊 Updated Database Statistics:")
    stats = db_manager.get_database_stats()
    for db_name, db_stats in stats.items():
        if 'error' in db_stats:
            print(f"  {db_name}: Error - {db_stats['error']}")
        else:
            print(f"  {db_name}: {db_stats['total_rows']} rows, {db_stats['size_mb']} MB")
    
    print("\n✅ Database separation completed!")
    # Get databases directory relative to repo root
    databases_dir = script_dir / "databases"
    print(f"📁 Database files located in: {databases_dir}/")
    print("   - live2d.db (cleared and ready for import)")
    print("   - conversations.db (preserved)")
    print("   - personality.db (preserved)")
    print("   - system.db (preserved)")
    
    return True

if __name__ == "__main__":
    print("⚠️ This will:")
    print("1. Create separated databases")
    print("2. Migrate existing data")
    print("3. Clear ONLY Live2D data (preserving conversations/emotions)")
    print()
    
    response = input("Continue? (y/N): ")
    if response.lower() == 'y':
        if migrate_and_clear_live2d():
            print("\n🎉 Ready to populate Live2D models!")
        else:
            print("\n❌ Migration failed")
    else:
        print("❌ Operation cancelled")
