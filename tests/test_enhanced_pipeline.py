#!/usr/bin/env python3
"""
Test script for Enhanced VAD Pipeline
Tests the complete enhanced audio pipeline with VAD integration
"""

import sys
import os
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_enhanced_vad_imports():
    """Test importing all enhanced VAD classes"""
    try:
        from audio.enhanced_vad import EnhancedVADConfig, SileroVAD, HybridVAD
        logger.info("✓ Successfully imported enhanced VAD classes")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to import enhanced VAD classes: {e}")
        return False

def test_enhanced_pipeline_import():
    """Test importing enhanced audio pipeline"""
    try:
        from audio.enhanced_audio_pipeline import EnhancedAudioPipelineWrapper
        logger.info("✓ Successfully imported enhanced audio pipeline")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to import enhanced audio pipeline: {e}")
        return False

def test_create_silero_vad():
    """Test creating SileroVAD instance"""
    try:
        from audio.enhanced_vad import SileroVAD, EnhancedVADConfig
        
        config = EnhancedVADConfig()
        vad = SileroVAD(config)
        logger.info("✓ Successfully created SileroVAD instance")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to create SileroVAD instance: {e}")
        return False

def test_create_hybrid_vad():
    """Test creating HybridVAD instance"""
    try:
        from audio.enhanced_vad import HybridVAD, EnhancedVADConfig
        
        config = EnhancedVADConfig()
        vad = HybridVAD(config)
        logger.info("✓ Successfully created HybridVAD instance")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to create HybridVAD instance: {e}")
        return False

def test_create_enhanced_pipeline():
    """Test creating Enhanced Audio Pipeline"""
    try:
        from audio.enhanced_audio_pipeline import EnhancedAudioPipelineWrapper, EnhancedAudioConfig
        
        # Create config and wake words
        config = EnhancedAudioConfig()
        wake_words = ["hey", "ai"]
        
        # Test with config (should use faster-whisper)
        pipeline = EnhancedAudioPipelineWrapper(wake_words=wake_words, config=config)
        logger.info("✓ Successfully created Enhanced Audio Pipeline")
        
        # Check if VAD is properly initialized
        if hasattr(pipeline, 'vad') and pipeline.vad is not None:
            logger.info(f"✓ VAD initialized: {type(pipeline.vad).__name__}")
        else:
            logger.warning("⚠ VAD not initialized in pipeline")
        
        return True
    except Exception as e:
        logger.error(f"✗ Failed to create Enhanced Audio Pipeline: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("Starting Enhanced VAD Pipeline Tests")
    logger.info("=" * 50)
    
    tests = [
        ("Enhanced VAD Imports", test_enhanced_vad_imports),
        ("Enhanced Pipeline Import", test_enhanced_pipeline_import),
        ("SileroVAD Creation", test_create_silero_vad),
        ("HybridVAD Creation", test_create_hybrid_vad),
        ("Enhanced Pipeline Creation", test_create_enhanced_pipeline),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\nRunning test: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("TEST SUMMARY")
    logger.info("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nPassed: {passed}/{len(results)} tests")
    
    if passed == len(results):
        logger.info("🎉 All tests passed! Enhanced VAD pipeline is ready.")
    else:
        logger.warning(f"⚠ {len(results) - passed} tests failed. Check logs above.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
