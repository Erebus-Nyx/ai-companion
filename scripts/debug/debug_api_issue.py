#!/usr/bin/env python3
"""
Debug the API issue with motion retrieval
"""

import sys
import os
import requests

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.live2d_models import Live2DModelManager

def debug_api_issue():
    """Debug why API returns 0 motions"""
    print("🔍 === DEBUGGING API MOTION ISSUE ===")
    
    # Step 1: Test database directly
    print("\n📂 Testing database directly...")
    try:
        manager = Live2DModelManager('src/ai2d_chat.db')
        motions = manager.get_model_motions('kanade')
        print(f"✅ Direct database query: {len(motions)} motions for kanade")
        
        if motions:
            print("📝 Sample motions from database:")
            for i, motion in enumerate(motions[:5]):
                print(f"   {i+1}. {motion['motion_group']}[{motion['motion_index']}] ({motion['motion_type']})")
        else:
            print("❌ No motions found in database")
            return
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return
    
    # Step 2: Test API endpoint
    print("\n🌐 Testing API endpoint...")
    try:
        response = requests.get("http://localhost:19443/api/live2d/model/kanade/motions", timeout=5)
        print(f"📡 API response status: {response.status_code}")
        
        if response.ok:
            api_motions = response.json()
            print(f"📡 API returned: {len(api_motions)} motions")
            
            if api_motions:
                print("📝 Sample motions from API:")
                for i, motion in enumerate(api_motions[:5]):
                    print(f"   {i+1}. {motion['motion_group']}[{motion['motion_index']}] ({motion['motion_type']})")
            else:
                print("❌ API returned empty motion list")
                
        else:
            print(f"❌ API error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ API request error: {e}")
    
    # Step 3: Check server logs
    print("\n📋 To debug further, check the Flask server console for any errors")
    print("💡 The issue might be:")
    print("   - Flask app using different database path")
    print("   - live2d_manager not properly initialized")
    print("   - Database connection issue in Flask app")

if __name__ == "__main__":
    debug_api_issue()
