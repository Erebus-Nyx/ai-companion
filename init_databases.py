#!/usr/bin/env python3
"""
Database initialization script for AI2D Chat
Ensures all user tables are created properly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routes.app_routes_users import init_user_tables
import logging

def main():
    logging.basicConfig(level=logging.INFO)
    
    print("🔧 Initializing AI2D Chat user databases...")
    
    try:
        init_user_tables()
        print("✅ User databases initialized successfully!")
        
        # Test the tables by checking if we can query them
        from databases.database_manager import get_users_connection, get_user_profiles_connection
        
        with get_users_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            print(f"📊 Users table: {user_count} users found")
            
        with get_user_profiles_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM user_profiles")
            profile_count = cursor.fetchone()[0]
            print(f"📊 User profiles table: {profile_count} profiles found")
            
        print("✅ Database initialization complete!")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
