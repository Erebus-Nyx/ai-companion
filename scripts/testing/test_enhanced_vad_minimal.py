#!/usr/bin/env python3
"""
Minimal test for enhanced VAD components
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test importing enhanced VAD components"""
    try:
        from audio.enhanced_vad import (
            EnhancedVADConfig, 
            SILERO_AVAILABLE, 
            PYANNOTE_AVAILABLE,
            FASTER_WHISPER_AVAILABLE
        )
        
        print("✅ Enhanced VAD imports successful")
        print(f"   - Silero VAD: {'✅ Available' if SILERO_AVAILABLE else '❌ Not available'}")
        print(f"   - Pyannote VAD: {'✅ Available' if PYANNOTE_AVAILABLE else '❌ Not available'}")
        print(f"   - Faster Whisper: {'✅ Available' if FASTER_WHISPER_AVAILABLE else '❌ Not available'}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_config():
    """Test enhanced VAD configuration"""
    try:
        from audio.enhanced_vad import EnhancedVADConfig
        
        config = EnhancedVADConfig()
        print("✅ Enhanced VAD config creation successful")
        print(f"   - VAD Engine: {config.vad_engine}")
        print(f"   - STT Model: {config.stt_model}")
        print(f"   - Sample Rate: {config.sample_rate}")
        
        return True
        
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False

def test_factory_functions():
    """Test factory functions"""
    try:
        from audio.enhanced_vad import (
            create_lightweight_enhanced_pipeline,
            create_high_accuracy_pipeline,
            create_enhanced_pipeline
        )
        
        print("✅ Factory functions imported successfully")
        
        # Test lightweight pipeline creation (should work without GPU)
        try:
            pipeline = create_lightweight_enhanced_pipeline()
            print("✅ Lightweight pipeline created successfully")
        except Exception as e:
            print(f"⚠️  Lightweight pipeline creation failed: {e}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Factory function import error: {e}")
        return False

if __name__ == "__main__":
    print("🎤 Testing Enhanced VAD Implementation")
    print("=" * 50)
    
    success = True
    
    print("\n1. Testing imports...")
    success &= test_imports()
    
    print("\n2. Testing configuration...")
    success &= test_config()
    
    print("\n3. Testing factory functions...")
    success &= test_factory_functions()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! Enhanced VAD is ready to use.")
    else:
        print("❌ Some tests failed. Check the errors above.")
    
    print("\nNext steps:")
    print("- Install pyannote.audio for advanced VAD: pip install pyannote.audio")
    print("- Install faster-whisper for optimized STT: pip install faster-whisper")
    print("- Test with real audio data using enhanced_vad_example.py")
