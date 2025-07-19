#!/usr/bin/env python3
"""
Simple configuration test for enhanced VAD
Tests only the configuration loading without audio dependencies
"""

import yaml
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_config_loading():
    """Test configuration loading"""
    logger.info("Testing configuration loading...")
    
    try:
        config_file = Path("config.yaml")
        if not config_file.exists():
            logger.error("config.yaml not found")
            return False
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        
        logger.info(f"✓ Config loaded successfully")
        logger.info(f"  Config keys: {list(config.keys())}")
        
        # Test voice detection config
        voice_config = config.get('voice_detection', {})
        if not voice_config:
            logger.warning("No voice_detection config found")
            return False
        
        logger.info(f"  Voice detection config found")
        
        # Test cue words
        cue_words = voice_config.get('cue_words', [])
        logger.info(f"  Cue words: {cue_words}")
        
        # Test enhanced VAD config
        enhanced_vad = voice_config.get('enhanced_vad', {})
        if enhanced_vad:
            logger.info(f"  Enhanced VAD config found:")
            logger.info(f"    Enabled: {enhanced_vad.get('enabled', 'not set')}")
            logger.info(f"    Mode: {enhanced_vad.get('mode', 'not set')}")
            logger.info(f"    VAD Model: {enhanced_vad.get('vad_model', 'not set')}")
            logger.info(f"    STT Model: {enhanced_vad.get('stt_model', 'not set')}")
            logger.info(f"    Fallback: {enhanced_vad.get('fallback_to_basic', 'not set')}")
        else:
            logger.warning("No enhanced_vad config found")
        
        return True
        
    except Exception as e:
        logger.error(f"Config loading failed: {e}")
        return False

def test_enhanced_vad_config_structure():
    """Test the enhanced VAD configuration structure"""
    logger.info("Testing enhanced VAD config structure...")
    
    try:
        with open("config.yaml", 'r') as f:
            config = yaml.safe_load(f)
        
        voice_config = config.get('voice_detection', {})
        enhanced_vad = voice_config.get('enhanced_vad', {})
        
        required_fields = {
            'enabled': bool,
            'mode': str,
            'fallback_to_basic': bool,
            'vad_model': str,
            'stt_model': str,
            'stt_language': str,
            'chunk_duration': (int, float),
            'min_speech_duration': (int, float),
            'max_speech_duration': (int, float)
        }
        
        missing_fields = []
        wrong_types = []
        
        for field, expected_type in required_fields.items():
            if field not in enhanced_vad:
                missing_fields.append(field)
            else:
                value = enhanced_vad[field]
                if not isinstance(value, expected_type):
                    wrong_types.append(f"{field}: expected {expected_type}, got {type(value)}")
        
        if missing_fields:
            logger.warning(f"Missing fields: {missing_fields}")
        
        if wrong_types:
            logger.warning(f"Wrong types: {wrong_types}")
        
        if not missing_fields and not wrong_types:
            logger.info("✓ Enhanced VAD config structure is valid")
            return True
        else:
            return False
    
    except Exception as e:
        logger.error(f"Config structure test failed: {e}")
        return False

def test_requirements_file():
    """Test if requirements.txt includes enhanced VAD dependencies"""
    logger.info("Testing requirements.txt for enhanced VAD dependencies...")
    
    try:
        with open("requirements.txt", 'r') as f:
            requirements = f.read()
        
        enhanced_deps = [
            'faster-whisper',
            'pyannote.audio',
            'pyannote.core'
        ]
        
        found_deps = []
        missing_deps = []
        
        for dep in enhanced_deps:
            if dep in requirements:
                found_deps.append(dep)
            else:
                missing_deps.append(dep)
        
        logger.info(f"Found dependencies: {found_deps}")
        if missing_deps:
            logger.warning(f"Missing dependencies: {missing_deps}")
            return False
        else:
            logger.info("✓ All enhanced VAD dependencies found in requirements.txt")
            return True
    
    except Exception as e:
        logger.error(f"Requirements test failed: {e}")
        return False

def test_file_structure():
    """Test if all enhanced VAD files are present"""
    logger.info("Testing enhanced VAD file structure...")
    
    expected_files = [
        "src/audio/enhanced_vad.py",
        "src/audio/enhanced_audio_pipeline.py", 
        "src/audio/config_loader.py",
        "config.yaml",
        "requirements.txt"
    ]
    
    missing_files = []
    found_files = []
    
    for file_path in expected_files:
        if Path(file_path).exists():
            found_files.append(file_path)
        else:
            missing_files.append(file_path)
    
    logger.info(f"Found files: {found_files}")
    if missing_files:
        logger.warning(f"Missing files: {missing_files}")
        return False
    else:
        logger.info("✓ All enhanced VAD files are present")
        return True

def main():
    """Run all tests"""
    logger.info("Starting enhanced VAD configuration tests...")
    
    tests = [
        ("Configuration Loading", test_config_loading),
        ("Enhanced VAD Config Structure", test_enhanced_vad_config_structure),
        ("Requirements File", test_requirements_file),
        ("File Structure", test_file_structure)
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
        logger.info("🎉 All configuration tests passed!")
        logger.info("\nNext steps:")
        logger.info("1. Install dependencies: pip install -r requirements.txt")
        logger.info("2. Test the enhanced VAD pipeline")
        logger.info("3. Integrate with your existing AI live2d chat")
        return 0
    else:
        logger.warning("⚠️  Some tests failed")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
