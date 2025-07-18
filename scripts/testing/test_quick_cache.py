#!/usr/bin/env python3
"""
Quick test to verify models are no longer re-downloading.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from audio.enhanced_vad import create_lightweight_pipeline

def test_no_redownload():
    print("🧪 Testing No Re-download Behavior")
    print("=" * 50)
    
    print("Creating first lightweight pipeline...")
    pipeline1 = create_lightweight_pipeline()
    
    print("\nCreating second lightweight pipeline...")
    print("(Should see 'Using cached model from memory' messages)")
    pipeline2 = create_lightweight_pipeline()
    
    print("\nCreating third lightweight pipeline...")
    print("(Should also use cached models)")
    pipeline3 = create_lightweight_pipeline()
    
    print("\n✅ Test completed! Models should be cached in memory now.")

if __name__ == "__main__":
    test_no_redownload()
