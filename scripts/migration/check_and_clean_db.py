#!/usr/bin/env python3
"""
Check and clean the Live2D database
"""

import sqlite3
import os

def check_and_clean_database():
    """Check the database status and clean up duplicates"""
    db_path = '/home/nyx/ai2d_chat/src/ai2d_chat.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    print("🔍 === CHECKING DATABASE STATUS ===")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check total counts
    cursor.execute('SELECT COUNT(*) FROM live2d_motions')
    total_motions = cursor.fetchone()[0]
    print(f"Total motions: {total_motions}")
    
    cursor.execute('SELECT COUNT(*) FROM live2d_models')
    total_models = cursor.fetchone()[0] 
    print(f"Total models: {total_models}")
    
    # Check by model
    cursor.execute("""
        SELECT m.model_name, COUNT(mo.id) as motion_count
        FROM live2d_models m
        LEFT JOIN live2d_motions mo ON m.id = mo.model_id
        GROUP BY m.id, m.model_name
        ORDER BY m.model_name
    """)
    results = cursor.fetchall()
    print("\nMotions by model:")
    for model_name, count in results:
        print(f"   {model_name}: {count} motions")
    
    # Check for duplicates
    cursor.execute("""
        SELECT model_id, motion_group, motion_index, COUNT(*) as count
        FROM live2d_motions 
        GROUP BY model_id, motion_group, motion_index 
        HAVING count > 1
        ORDER BY count DESC
        LIMIT 10
    """)
    duplicates = cursor.fetchall()
    
    if duplicates:
        print(f"\n⚠️ Found {len(duplicates)} duplicate motion entries:")
        for dup in duplicates[:5]:
            print(f"   Model {dup[0]}, {dup[1]}[{dup[2]}]: {dup[3]} copies")
        
        print("\n🧹 Cleaning up duplicates...")
        
        # Delete duplicates, keeping only the first occurrence
        cursor.execute("""
            DELETE FROM live2d_motions 
            WHERE id NOT IN (
                SELECT MIN(id) 
                FROM live2d_motions 
                GROUP BY model_id, motion_group, motion_index
            )
        """)
        
        deleted_count = cursor.rowcount
        conn.commit()
        print(f"✅ Deleted {deleted_count} duplicate entries")
        
        # Recheck totals
        cursor.execute('SELECT COUNT(*) FROM live2d_motions')
        new_total = cursor.fetchone()[0]
        print(f"✅ New total motions: {new_total}")
        
    else:
        print("✅ No duplicates found")
    
    # Check motion types
    cursor.execute("""
        SELECT motion_type, COUNT(*) as count
        FROM live2d_motions
        GROUP BY motion_type
        ORDER BY count DESC
    """)
    type_results = cursor.fetchall()
    print(f"\nMotion types:")
    for motion_type, count in type_results:
        print(f"   {motion_type}: {count} motions")
    
    conn.close()
    print("\n✅ Database check completed!")

if __name__ == "__main__":
    check_and_clean_database()
