#!/usr/bin/env python3
"""
Test script to verify Live2D fixes are working
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_database_schema():
    """Test that the database schema is correct"""
    print("🔍 Testing database schema...")
    
    try:
        from databases.live2d_models_separated import Live2DModelManager
        manager = Live2DModelManager()
        
        # Test that we can access preview_image column
        from databases.database_manager import get_live2d_connection
        with get_live2d_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(live2d_models)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'preview_image' in columns:
                print("✅ preview_image column exists")
                return True
            else:
                print("❌ preview_image column missing")
                return False
                
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_live2d_files():
    """Test that Live2D files are accessible"""
    print("🔍 Testing Live2D files...")
    
    try:
        # Check if static files exist
        static_files = [
            "web/static/js/live2d_multi_model_manager.js",
            "web/static/js/live2d_interaction.js", 
            "web/static/js/debug.js",
            "web/static/live2d_pixi.html",
            "web/static/css/live2d_test.css"
        ]
        
        missing_files = []
        for file_path in static_files:
            full_path = project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            print(f"❌ Missing files: {missing_files}")
            return False
        else:
            print("✅ All Live2D static files found")
            return True
            
    except Exception as e:
        print(f"❌ File test failed: {e}")
        return False

def test_config():
    """Test configuration"""
    print("🔍 Testing configuration...")
    
    try:
        from config.config_manager import ConfigManager, is_live2d_enabled
        
        config_manager = ConfigManager()
        live2d_enabled = is_live2d_enabled()
        
        print(f"✅ Live2D enabled: {live2d_enabled}")
        print(f"✅ Config directory: {config_manager.config_dir}")
        return True
        
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

def main():
    print("🧪 Live2D Fixes Test Suite")
    print("=" * 40)
    
    tests = [
        ("Database Schema", test_database_schema),
        ("Live2D Files", test_live2d_files),
        ("Configuration", test_config)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 40)
    print("📊 Test Results:")
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 All tests passed! Live2D fixes should be working.")
        print("\nNext steps:")
        print("1. Start the application: python3 app.py")
        
        # Get actual dev port from config
        try:
            import yaml
            with open('config.yaml', 'r') as f:
                config = yaml.safe_load(f)
            dev_port = config.get('server', {}).get('dev_port', 19081)
            print(f"2. Open browser to: http://localhost:{dev_port}")
        except Exception:
            print("2. Open browser to: http://localhost:19081")
            
        print("3. Open debug console and run 'System Test'")
        print("4. Load a model and test drag/zoom functionality")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
