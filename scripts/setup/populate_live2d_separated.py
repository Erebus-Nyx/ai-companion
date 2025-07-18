#!/usr/bin/env python3
"""
Populate Live2D models using the new separated database system
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database.live2d_models_separated import Live2DModelManager

def populate_live2d_models():
    """Populate Live2D models in the separated database"""
    
    print("🔄 === POPULATING LIVE2D MODELS (SEPARATED DB) ===")
    
    try:
        # Initialize the Live2D model manager
        manager = Live2DModelManager()
        print("✅ Live2D model manager initialized")
        
        # Clear existing data first
        print("🧹 Clearing existing Live2D data...")
        results = manager.clear_all_models()
        print(f"✅ Cleared {results['models_deleted']} models and {results['motions_deleted']} motions")
        
        # Scan and register models
        print("📂 Scanning for Live2D models...")
        manager.scan_models_directory()
        
        # Get statistics
        print("\n📊 Final Statistics:")
        stats = manager.get_database_stats()
        print(f"✅ Total models: {stats['total_models']}")
        print(f"✅ Total motions: {stats['total_motions']}")
        
        print("\nModels with motion counts:")
        for model_info in stats['motions_per_model']:
            print(f"  {model_info['model_name']}: {model_info['motion_count']} motions")
        
        print("\nMotion types distribution:")
        for motion_type in stats['motion_types']:
            print(f"  {motion_type['motion_type']}: {motion_type['count']} motions")
        
        print("\n🎉 Live2D population completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during population: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if populate_live2d_models():
        print("\n✅ Ready to test Live2D models in the web interface!")
    else:
        print("\n❌ Population failed")
