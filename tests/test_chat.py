#!/usr/bin/env python3
"""
Test script to verify chat functionality is working
"""

import socketio
import time
import threading

# Create a SocketIO client
sio = socketio.Client()

@sio.event
def connect():
    print("✅ Connected to server")
    
@sio.event
def disconnect():
    print("❌ Disconnected from server")

@sio.event
def ai_response(data):
    print(f"🤖 AI Response: {data['response']}")
    print(f"📝 User Input: {data['user_input']}")
    print(f"⏰ Timestamp: {data['timestamp']}")
    
@sio.event
def error(data):
    print(f"❌ Error: {data['message']}")

@sio.event
def status_update(data):
    print(f"📊 Status: {data.get('status', 'Unknown')}")

def test_chat():
    try:
        print("🔌 Connecting to AI Companion server...")
        sio.connect('http://localhost:13443')
        
        # Wait a moment for connection
        time.sleep(1)
        
        # Send a test message
        test_message = "Hello! Can you introduce yourself?"
        print(f"📤 Sending message: {test_message}")
        sio.emit('chat_message', {'message': test_message})
        
        # Wait for response
        print("⏳ Waiting for AI response...")
        time.sleep(10)  # Wait up to 10 seconds for response
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        sio.disconnect()

if __name__ == "__main__":
    test_chat()
