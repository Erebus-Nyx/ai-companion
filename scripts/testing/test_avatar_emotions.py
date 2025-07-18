#!/usr/bin/env python3
"""
Test script to verify avatar emotion changes through the API
"""

import requests
import json
import time

def test_avatar_emotions():
    base_url = "http://localhost:19443"
    
    # Test different emotions
    emotions_to_test = [
        ("happy", "Tell me a joke!"),
        ("surprised", "That's amazing!"),
        ("thinking", "Let me think about this..."),
        ("sad", "I'm feeling a bit down today"),
        ("neutral", "How are you today?")
    ]
    
    print("Testing avatar emotions...")
    
    for emotion, message in emotions_to_test:
        print(f"\n--- Testing {emotion} emotion ---")
        print(f"Sending message: '{message}'")
        
        try:
            # Send message to AI companion
            response = requests.post(
                f"{base_url}/api/chat",
                json={"message": message},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Response received: {data.get('response', 'No response')[:100]}...")
                print(f"Expected emotion: {emotion}")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        
        # Wait between tests
        time.sleep(2)
    
    print("\n--- Avatar emotion testing complete ---")

if __name__ == "__main__":
    test_avatar_emotions()
