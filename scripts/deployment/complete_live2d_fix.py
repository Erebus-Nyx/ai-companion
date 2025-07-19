#!/usr/bin/env python3
"""
Complete fix for Live2D models - register models AND their motions
"""

import sys
import os
import json

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.live2d_models import Live2DModelManager

def register_all_motions():
    """Register motions for all models by reading their config files"""
    print("🎭 === REGISTERING ALL MOTIONS ===")
    
    # Initialize the Live2DModelManager
    db_path = os.path.join(os.path.dirname(__file__), 'src', 'ai2d_chat.db')
    models_dir = os.path.join(os.path.dirname(__file__), 'src', 'web', 'static', 'assets')
    
    manager = Live2DModelManager(db_path)
    
    # Get all registered models
    models = manager.get_all_models()
    print(f"📁 Found {len(models)} models in database")
    
    for model in models:
        model_name = model['model_name']
        model_path = model['model_path']
        config_file = model['config_file']
        
        print(f"\n🎭 Processing motions for: {model_name}")
        
        # Full path to config file
        full_config_path = os.path.join(model_path, config_file)
        
        if not os.path.exists(full_config_path):
            print(f"   ❌ Config file not found: {full_config_path}")
            continue
        
        try:
            # Read and parse config file
            with open(full_config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            motions = []
            
            # Parse motion groups
            if 'FileReferences' in config_data and 'Motions' in config_data['FileReferences']:
                motion_groups = config_data['FileReferences']['Motions']
                print(f"   🎭 Found {len(motion_groups)} motion groups in config")
                
                for group_name, group_motions in motion_groups.items():
                    print(f"      📁 Group: {group_name} ({len(group_motions)} motions)")
                    
                    for i, motion_file in enumerate(group_motions):
                        # Determine motion type based on group name
                        motion_type = 'body'  # Default
                        group_lower = group_name.lower()
                        if any(word in group_lower for word in ['head', 'face', 'eye']):
                            motion_type = 'head'
                        elif any(word in group_lower for word in ['expression', 'expr']):
                            motion_type = 'expression'
                        elif any(word in group_lower for word in ['special', 'unique']):
                            motion_type = 'special'
                        
                        motions.append({
                            'group': group_name,
                            'index': i,
                            'name': f"{group_name}_{i}",
                            'type': motion_type
                        })
                
                print(f"   📝 Prepared {len(motions)} individual motions for registration")
                
                # Register motions
                if motions:
                    result = manager.register_motions_for_model(model_name, motions)
                    if result:
                        print(f"   ✅ Successfully registered {len(motions)} motions")
                    else:
                        print(f"   ❌ Failed to register motions")
                        
                        # Check if model exists in database
                        all_models = manager.get_all_models()
                        model_names = [m['model_name'] for m in all_models]
                        if model_name in model_names:
                            print(f"   🔍 Model {model_name} exists in database")
                        else:
                            print(f"   ❌ Model {model_name} NOT found in database!")
                            print(f"   📝 Available models: {model_names}")
                else:
                    print(f"   ⚠️ No motions to register")
            else:
                print(f"   ⚠️ No motion data found in config file structure")
                print(f"   🔍 Config keys: {list(config_data.keys())}")
                
        except Exception as e:
            print(f"   ❌ Error processing config file: {e}")
            import traceback
            traceback.print_exc()
    
    # Final verification
    print(f"\n🔍 === FINAL VERIFICATION ===")
    models = manager.get_all_models()
    total_motions = 0
    
    for model in models:
        motions = manager.get_model_motions(model['model_name'])
        motion_count = len(motions)
        total_motions += motion_count
        print(f"   📁 {model['model_name']}: {motion_count} motions")
        
        # Show motion types
        if motion_count > 0:
            motion_types = {}
            for motion in motions:
                motion_type = motion.get('motion_type', 'unknown')
                motion_types[motion_type] = motion_types.get(motion_type, 0) + 1
            print(f"      📊 Types: {dict(motion_types)}")
    
    print(f"\n✅ Complete! Total: {len(models)} models, {total_motions} motions")

if __name__ == "__main__":
    register_all_motions()
