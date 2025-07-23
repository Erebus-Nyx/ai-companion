#!/usr/bin/env python3
"""
Quick TTS debug script to test TTS functionality
"""
import sys
import os
sys.path.append('/home/nyx/ai2d_chat')

import app_globals
from models.tts_handler import EmotionalTTSHandler

def test_tts():
    print("🔊 Testing TTS Handler...")
    
    # Check if TTS handler exists in app_globals
    print(f"TTS Handler in app_globals: {hasattr(app_globals, 'tts_handler')}")
    if hasattr(app_globals, 'tts_handler'):
        print(f"TTS Handler value: {app_globals.tts_handler}")
    
    # Try to create a new TTS handler
    try:
        print("Creating new TTS handler...")
        handler = EmotionalTTSHandler()
        print(f"TTS Handler created: {handler}")
        
        print("Initializing TTS model...")
        success = handler.initialize_model()
        print(f"TTS Model initialization success: {success}")
        
        if success:
            print("Testing speech synthesis...")
            audio_data = handler.synthesize_speech("Hello world test")
            print(f"Audio data generated: {audio_data is not None}")
            if audio_data is not None:
                print(f"Audio data type: {type(audio_data)}, shape: {getattr(audio_data, 'shape', 'No shape')}")
        
    except Exception as e:
        print(f"❌ Error creating/testing TTS handler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_tts()
