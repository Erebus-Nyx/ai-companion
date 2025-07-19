#!/usr/bin/env python3
"""
Script to properly populate Live2D models using the correct database manager
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set the correct working directory for user data
user_data_dir = os.path.expanduser("~/.local/share/ai2d_chat")
databases_dir = os.path.join(user_data_dir, "databases")

# Import and configure the database manager to use user data directory
from databases.database_manager import DatabaseManager
from databases.live2d_models_separated import Live2DModelManager

def populate_with_correct_paths():
    """Populate models using the correct user data directory"""
    
    print("🎯 === POPULATING LIVE2D MODELS (CORRECT PATHS) ===\n")
    
    print(f"📁 User data directory: {user_data_dir}")
    print(f"💾 Databases directory: {databases_dir}")
    
    # Initialize database manager with correct path
    db_manager = DatabaseManager(base_path=databases_dir)
    print("✅ Database manager initialized with user data directory")
    
    # Initialize Live2D model manager
    live2d_manager = Live2DModelManager()
    print("✅ Live2D model manager initialized")
    
    # Models directory
    live2d_models_path = os.path.join(user_data_dir, "live2d_models")
    print(f"🎭 Live2D models path: {live2d_models_path}")
    
    if not os.path.exists(live2d_models_path):
        print(f"❌ Live2D models directory not found: {live2d_models_path}")
        return False
    
    # Get current models
    current_models = live2d_manager.get_all_models()
    print(f"📊 Current models in database: {len(current_models)}")
    
    # Show current models
    if current_models:
        print("📋 Current models:")
        for model in current_models:
            print(f"   🎭 {model['model_name']}: {model['model_path']}")
    
    # Scan for new models
    print(f"\n🔍 Scanning models directory: {live2d_models_path}")
    live2d_manager.scan_models_directory(live2d_models_path)
    
    # Show updated models
    updated_models = live2d_manager.get_all_models()
    print(f"📊 After scan: {len(updated_models)} models")
    
    print("\n📋 All registered models:")
    for model in updated_models:
        model_full_path = os.path.join(user_data_dir, model['model_path'])
        exists = "✅ EXISTS" if os.path.exists(model_full_path) else "❌ MISSING"
        print(f"   🎭 {model['model_name']}: {model['model_path']} {exists}")
    
    print(f"\n🎉 Model population complete!")
    return True

if __name__ == "__main__":
    populate_with_correct_paths()
