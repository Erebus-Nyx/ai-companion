#!/usr/bin/env python3
"""
Debug script to test motion detection step by step
"""

import requests
import json

def test_backend_api():
    """Test basic backend API functionality"""
    print("🧪 === TESTING BACKEND API ===")
    
    base_url = "http://localhost:13443"
    
    # Test models endpoint
    try:
        response = requests.get(f"{base_url}/api/live2d/models")
        print(f"✅ Models API: {response.status_code}")
        models = response.json()
        print(f"   Found {len(models)} models:")
        for model in models:
            print(f"   - {model['model_name']} ({model['config_file']})")
            
        # Test motions endpoint for each model
        for model in models:
            model_name = model['model_name']
            try:
                response = requests.get(f"{base_url}/api/live2d/model/{model_name}/motions")
                if response.ok:
                    motions = response.json()
                    print(f"   {model_name}: {len(motions)} motions")
                else:
                    print(f"   {model_name}: API error {response.status_code}")
            except Exception as e:
                print(f"   {model_name}: Exception {e}")
        
        return True
    except Exception as e:
        print(f"❌ Models API failed: {e}")
        return False

def test_model_files():
    """Check if Live2D model files exist"""
    print("\n📁 === TESTING LIVE2D MODEL FILES ===")
    
    import os
    
    # Use user data directory for Live2D models
    user_data_dir = os.path.expanduser("~/.local/share/ai-companion")
    models_dir = os.path.join(user_data_dir, "live2d_models")
    if not os.path.exists(models_dir):
        print(f"❌ Live2D models directory not found: {models_dir}")
        return False
    
    print(f"✅ Live2D models directory exists: {models_dir}")
    
    # Check for kanade model specifically
    kanade_dir = os.path.join(models_dir, "kanade")
    if os.path.exists(kanade_dir):
        print(f"✅ Kanade model directory exists")
        files = os.listdir(kanade_dir)
        print(f"   Files in kanade directory: {len(files)}")
        
        # Look for .model3.json file
        model3_files = [f for f in files if f.endswith('.model3.json')]
        if model3_files:
            print(f"   Found .model3.json files: {model3_files}")
            
            # Try to read the first one
            model3_path = os.path.join(kanade_dir, model3_files[0])
            try:
                with open(model3_path, 'r') as f:
                    model_config = json.load(f)
                    
                print(f"   ✅ Successfully parsed {model3_files[0]}")
                
                # Check for motions in the config
                if 'FileReferences' in model_config and 'Motions' in model_config['FileReferences']:
                    motions = model_config['FileReferences']['Motions']
                    print(f"   📁 Motion groups in config: {list(motions.keys())}")
                    
                    total_motions = 0
                    for group, motion_list in motions.items():
                        motion_count = len(motion_list)
                        total_motions += motion_count
                        print(f"      {group}: {motion_count} motions")
                    
                    print(f"   🎭 Total motions in config: {total_motions}")
                    return total_motions > 0
                else:
                    print(f"   ❌ No motion data found in config")
                    return False
                    
            except Exception as e:
                print(f"   ❌ Error reading model config: {e}")
                return False
        else:
            print(f"   ❌ No .model3.json files found")
            return False
    else:
        print(f"❌ Kanade model directory not found")
        return False

if __name__ == "__main__":
    print("🚀 Starting motion detection debug test...")
    
    # Test each component step by step
    print("\n" + "="*60)
    api_success = test_backend_api()
    
    print("\n" + "="*60)
    files_success = test_model_files()
    
    print(f"\n🏁 === SUMMARY ===")
    print(f"{'✅ PASS' if api_success else '❌ FAIL'} Backend API")
    print(f"{'✅ PASS' if files_success else '❌ FAIL'} Live2D Model Files")
