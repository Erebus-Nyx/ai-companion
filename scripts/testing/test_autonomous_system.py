#!/usr/bin/env python3
"""
Test script for autonomous avatar system
"""

import requests
import json
import time
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_autonomous_system():
    """Test the autonomous avatar system endpoints"""
    base_url = "http://localhost:19081"
    
    print("🧪 Testing Autonomous Avatar System")
    print("=" * 50)
    
    # Test 1: Check autonomous system status
    print("\n1. Checking autonomous system status...")
    try:
        response = requests.get(f"{base_url}/api/autonomous/status")
        if response.status_code == 200:
            status = response.json()
            print(f"   ✅ Status endpoint working")
            print(f"   📊 System status: {status}")
        else:
            print(f"   ❌ Status endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Status check failed: {e}")
    
    # Test 2: Test autonomous conversation trigger
    print("\n2. Testing autonomous conversation trigger...")
    try:
        response = requests.post(f"{base_url}/api/autonomous/test_conversation", 
                               json={"test": True})
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Conversation trigger working")
            print(f"   💬 Result: {result}")
        else:
            print(f"   ❌ Conversation trigger failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Conversation trigger failed: {e}")
    
    # Test 3: Check Live2D models
    print("\n3. Checking available Live2D models...")
    try:
        response = requests.get(f"{base_url}/api/live2d/models")
        if response.status_code == 200:
            models = response.json()
            print(f"   ✅ Models endpoint working")
            print(f"   🎭 Available models: {len(models)} found")
            for model in models[:3]:  # Show first 3
                name = model.get('name', 'Unknown')
                model_id = model.get('id', 'No ID')
                print(f"      - {name} (ID: {model_id})")
        else:
            print(f"   ❌ Models endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Models check failed: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Test complete!")
    print("\n💡 To test autonomous greetings in the browser:")
    print("   1. Open http://localhost:19081")
    print("   2. Load some Live2D avatars")
    print("   3. Open browser console (F12)")
    print("   4. Run: triggerTestGreetings()")
    print("   5. Or run: testAutonomousBackend()")

if __name__ == "__main__":
    test_autonomous_system()
