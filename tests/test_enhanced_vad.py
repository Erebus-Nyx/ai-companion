#!/usr/bin/env python3
"""
Test script for enhanced VAD integration
Tests the enhanced audio pipeline with configuration loading
"""

import sys
import asyncio
import logging
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.audio import (
    create_audio_pipeline_from_config,
    load_enhanced_audio_config,
    AudioConfigLoader
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_config_loading():
    """Test configuration loading"""
    logger.info("Testing configuration loading...")
    
    try:
        # Test config loader
        loader = AudioConfigLoader("config.yaml")
        config = loader.load_config()
        
        logger.info(f"Loaded config keys: {list(config.keys())}")
        
        # Test wake words
        wake_words = loader.get_wake_words()
        logger.info(f"Wake words: {wake_words}")
        
        # Test enhanced VAD settings
        enhanced_enabled = loader.is_enhanced_vad_enabled()
        enhanced_mode = loader.get_enhanced_vad_mode()
        
        logger.info(f"Enhanced VAD enabled: {enhanced_enabled}")
        logger.info(f"Enhanced VAD mode: {enhanced_mode}")
        
        # Test enhanced config creation
        enhanced_config = loader.create_enhanced_audio_config()
        logger.info(f"Enhanced config created successfully")
        logger.info(f"  - Use enhanced VAD: {enhanced_config.use_enhanced_vad}")
        logger.info(f"  - Enhanced mode: {enhanced_config.enhanced_mode}")
        logger.info(f"  - Fallback to basic: {enhanced_config.fallback_to_basic}")
        logger.info(f"  - VAD model: {enhanced_config.enhanced_vad_config.vad_model}")
        logger.info(f"  - STT model: {enhanced_config.enhanced_vad_config.stt_model}")
        
        return True
        
    except Exception as e:
        logger.error(f"Config loading test failed: {e}")
        return False

def test_pipeline_creation():
    """Test pipeline creation from config"""
    logger.info("Testing pipeline creation...")
    
    try:
        # Create pipeline from config
        pipeline = create_audio_pipeline_from_config("config.yaml")
        logger.info(f"Pipeline created: {type(pipeline).__name__}")
        
        # Check if it's enhanced pipeline
        if hasattr(pipeline, 'using_enhanced'):
            logger.info(f"Using enhanced VAD: {pipeline.using_enhanced}")
            if pipeline.using_enhanced:
                logger.info(f"Enhanced mode: {pipeline.config.enhanced_mode}")
        
        return True
        
    except Exception as e:
        logger.error(f"Pipeline creation test failed: {e}")
        return False

def test_enhanced_vad_components():
    """Test enhanced VAD components availability"""
    logger.info("Testing enhanced VAD components...")
    
    try:
        # Test imports
        from src.audio.enhanced_vad import (
            EnhancedVADConfig,
            PyannoteVAD,
            FasterWhisperSTT,
            EnhancedAudioPipeline
        )
        
        logger.info("Enhanced VAD components imported successfully")
        
        # Test config creation
        config = EnhancedVADConfig()
        logger.info(f"EnhancedVADConfig created with VAD model: {config.vad_model}")
        logger.info(f"STT model: {config.stt_model}")
        
        return True
        
    except ImportError as e:
        logger.warning(f"Enhanced VAD components not available: {e}")
        logger.info("This is expected if dependencies are not installed")
        return False
    except Exception as e:
        logger.error(f"Enhanced VAD component test failed: {e}")
        return False

def test_dependency_check():
    """Check if enhanced VAD dependencies are available"""
    logger.info("Checking enhanced VAD dependencies...")
    
    dependencies = {
        'faster_whisper': 'faster-whisper',
        'pyannote.audio': 'pyannote.audio',
        'pyannote.core': 'pyannote.core'
    }
    
    available = {}
    
    for module, package in dependencies.items():
        try:
            __import__(module)
            available[package] = True
            logger.info(f"✓ {package} is available")
        except ImportError:
            available[package] = False
            logger.warning(f"✗ {package} is not installed")
    
    if all(available.values()):
        logger.info("All enhanced VAD dependencies are available")
        return True
    else:
        logger.warning("Some enhanced VAD dependencies are missing")
        logger.info("Run: pip install faster-whisper pyannote.audio")
        return False

def main():
    """Run all tests"""
    logger.info("Starting enhanced VAD integration tests...")
    
    tests = [
        ("Configuration Loading", test_config_loading),
        ("Pipeline Creation", test_pipeline_creation),
        ("Enhanced VAD Components", test_enhanced_vad_components),
        ("Dependency Check", test_dependency_check)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running test: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        logger.info(f"{test_name}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    logger.info(f"\nTests passed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        logger.info("🎉 All tests passed!")
        return 0
    else:
        logger.warning("⚠️  Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
