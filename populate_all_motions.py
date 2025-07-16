#!/usr/bin/env python3
"""
Complete script to populate all Live2D motions in the database
"""

import os
import sys
import json
import sqlite3
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.live2d_models import Live2DModelManager

def classify_motion_type(group_name, motion_name=""):
    """Classify motion type based on group and motion names"""
    group_lower = group_name.lower()
    motion_lower = motion_name.lower()
    
    # Head/face motions
    if any(keyword in group_lower for keyword in ['head', 'face', 'eye', 'blink', 'look']):
        return 'head'
    
    # Expression motions  
    if any(keyword in group_lower for keyword in ['expression', 'expr', 'emotion', 'mood']):
        return 'expression'
    
    # Special motions
    if any(keyword in group_lower for keyword in ['special', 'unique', 'event', 'greeting']):
        return 'special'
    
    # Check motion name too
    if any(keyword in motion_lower for keyword in ['head', 'face', 'eye', 'blink', 'look']):
        return 'head'
    if any(keyword in motion_lower for keyword in ['expression', 'expr', 'emotion', 'mood']):
        return 'expression'
    if any(keyword in motion_lower for keyword in ['special', 'unique', 'event', 'greeting']):
        return 'special'
    
    # Default to body motion
    return 'body'

def populate_motions():
    """Populate all motions for all models"""
    print("🔄 === POPULATING ALL LIVE2D MOTIONS ===")
    
    # Initialize database manager
    db_path = '/home/nyx/ai-companion/src/ai_companion.db'
    print(f"📂 Database path: {db_path}")
    
    try:
        manager = Live2DModelManager(db_path)
        print("✅ Database manager initialized")
    except Exception as e:
        print(f"❌ Failed to initialize database manager: {e}")
        return False
    
    # Assets directory
    assets_dir = '/home/nyx/ai-companion/src/web/static/assets'
    print(f"📂 Assets directory: {assets_dir}")
    
    if not os.path.exists(assets_dir):
        print(f"❌ Assets directory not found: {assets_dir}")
        return False
    
    print("✅ Assets directory found")
    
    total_motions = 0
    
    # Find all model directories
    for model_dir in os.listdir(assets_dir):
        model_path = os.path.join(assets_dir, model_dir)
        if not os.path.isdir(model_path):
            continue
        
        # Look for .model3.json file
        model_config = None
        for file in os.listdir(model_path):
            if file.endswith('.model3.json'):
                model_config_path = os.path.join(model_path, file)
                try:
                    with open(model_config_path, 'r', encoding='utf-8') as f:
                        model_config = json.load(f)
                    break
                except Exception as e:
                    print(f"⚠️ Error reading {model_config_path}: {e}")
                    continue
        
        if not model_config:
            print(f"⚠️ No .model3.json found for {model_dir}")
            continue
        
        print(f"\n📂 Processing model: {model_dir}")
        
        # Register model first
        try:
            manager.register_model(model_dir, model_path, model_config_path.split('/')[-1])
            print(f"✅ Registered model: {model_dir}")
        except Exception as e:
            print(f"⚠️ Error registering model {model_dir}: {e}")
            continue
        
        # Extract motions from config
        motions = model_config.get('FileReferences', {}).get('Motions', {})
        model_motions_list = []
        
        for group_name, motion_list in motions.items():
            if not isinstance(motion_list, list):
                continue
            
            for motion_index, motion_data in enumerate(motion_list):
                if isinstance(motion_data, dict):
                    motion_file = motion_data.get('File', '')
                    motion_name = motion_data.get('Name', f"{group_name}_{motion_index}")
                elif isinstance(motion_data, str):
                    motion_file = motion_data
                    motion_name = f"{group_name}_{motion_index}"
                else:
                    continue
                
                # Classify motion type
                motion_type = classify_motion_type(group_name, motion_name)
                
                # Add to model motions list
                model_motions_list.append({
                    'group': group_name,
                    'index': motion_index,
                    'name': motion_name,
                    'type': motion_type
                })
        
        # Register all motions for this model at once
        if model_motions_list:
            try:
                success = manager.register_motions_for_model(model_dir, model_motions_list)
                if success:
                    model_motions = len(model_motions_list)
                    total_motions += model_motions
                    print(f"✅ Registered {model_motions} motions for {model_dir}")
                else:
                    print(f"❌ Failed to register motions for {model_dir}")
            except Exception as e:
                print(f"❌ Error registering motions for {model_dir}: {e}")
        else:
            print(f"⚠️ No motions found in config for {model_dir}")
        
        # Count total motions for this model
        
        print(f"✅ Processed {len(model_motions_list)} motions for {model_dir}")
    
    print(f"\n🎉 Successfully registered {total_motions} total motions across all models!")
    
    # Verify registration
    print("\n🔍 Verification:")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Count by model
    cursor.execute("""
        SELECT m.model_name, COUNT(mo.id) as motion_count
        FROM live2d_models m
        LEFT JOIN live2d_motions mo ON m.id = mo.model_id
        GROUP BY m.id, m.model_name
        ORDER BY m.model_name
    """)
    
    results = cursor.fetchall()
    for model_name, count in results:
        print(f"   {model_name}: {count} motions")
    
    # Count by type
    cursor.execute("""
        SELECT motion_type, COUNT(*) as count
        FROM live2d_motions
        GROUP BY motion_type
        ORDER BY count DESC
    """)
    
    type_results = cursor.fetchall()
    print(f"\n📊 Motion types:")
    for motion_type, count in type_results:
        print(f"   {motion_type}: {count} motions")
    
    conn.close()
    
    return total_motions > 0

if __name__ == "__main__":
    success = populate_motions()
    if success:
        print("\n✅ Motion population completed successfully!")
    else:
        print("\n❌ Motion population failed!")
        sys.exit(1)
