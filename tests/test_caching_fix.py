#!/usr/bin/env python3
"""
Test script to verify that model caching is working correctly.
This should not re-download models if they're already cached.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from audio.enhanced_vad import (
    EnhancedVADConfig, 
    SileroVAD, 
    FasterWhisperSTT,
    ModelCacheManager,
    create_lightweight_pipeline
)

def test_caching():
    print("🧪 Testing Model Caching System")
    print("=" * 50)
    
    # Test cache manager
    cache_manager = ModelCacheManager()
    print(f"Cache directory: {cache_manager.cache_dir}")
    
    # Check what's cached
    cache_info = cache_manager.cache_info
    print(f"Cached models: {list(cache_info.keys())}")
    
    print("\n1. Testing Silero VAD caching...")
    config = EnhancedVADConfig(vad_engine="silero")
    
    # First load
    print("First load:")
    silero1 = SileroVAD(config)
    
    print("\nSecond load (should use cache):")
    silero2 = SileroVAD(config)
    
    print("\n2. Testing FasterWhisper caching...")
    
    # First load
    print("First load:")
    stt1 = FasterWhisperSTT(config)
    
    print("\nSecond load (should use cache):")
    stt2 = FasterWhisperSTT(config)
    
    print("\n3. Testing full pipeline caching...")
    
    print("First pipeline:")
    pipeline1 = create_lightweight_pipeline()
    
    print("\nSecond pipeline (should use cached models):")
    pipeline2 = create_lightweight_pipeline()
    
    print("\n✅ Caching test completed!")

if __name__ == "__main__":
    test_caching()
