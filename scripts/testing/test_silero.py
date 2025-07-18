#!/usr/bin/env python3

import silero_vad

print("Testing Silero VAD model loading...")

try:
    # Load model
    model = silero_vad.load_silero_vad()
    print(f"Model type: {type(model)}")
    print(f"Model: {model}")
    
    # Test if model can be used directly without unpacking
    import torch
    sample_audio = torch.randn(16000)  # 1 second of random audio at 16kHz
    
    # Try getting speech timestamps
    timestamps = silero_vad.get_speech_timestamps(sample_audio, model)
    print(f"Timestamps type: {type(timestamps)}")
    print(f"Number of timestamps: {len(timestamps)}")
    print("✓ Silero VAD working correctly!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
