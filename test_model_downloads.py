#!/usr/bin/env python3
"""
Test script for individual model download methods.
Tests each download method separately to ensure they work before integration.
"""

import os
import sys
import logging
import shutil
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.model_downloader import ModelDownloader

def setup_logging():
    """Setup logging for testing."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_progress_callback(percent, message):
    """Progress callback for testing."""
    print(f"[{percent:6.1f}%] {message}")

def test_huggingface_download():
    """Test HuggingFace model download (TTS model)."""
    print("\n" + "="*50)
    print("Testing HuggingFace Download (TTS Model)")
    print("="*50)
    
    downloader = ModelDownloader(models_dir="test_models", cache_dir="test_cache")
    
    # Test TTS model download
    success = downloader.download_model("tts", "kokoro", test_progress_callback)
    print(f"TTS Download Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    
    # Check if files exist
    tts_dir = Path("test_models/tts/kokoro")
    if tts_dir.exists():
        files = list(tts_dir.iterdir())
        print(f"Downloaded files: {[f.name for f in files]}")
        print(f"Total files: {len(files)}")
    
    return success

def test_direct_url_download():
    """Test direct URL download (Silero VAD)."""
    print("\n" + "="*50)
    print("Testing Direct URL Download (Silero VAD)")
    print("="*50)
    
    downloader = ModelDownloader(models_dir="test_models", cache_dir="test_cache")
    
    # Test Silero VAD model download
    success = downloader.download_model("silero_vad", "v5", test_progress_callback)
    print(f"Silero VAD Download Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    
    # Check if file exists
    vad_file = Path("test_models/silero_vad/silero_vad.onnx")
    if vad_file.exists():
        file_size = vad_file.stat().st_size
        print(f"Downloaded file: {vad_file}")
        print(f"File size: {file_size} bytes ({file_size/1024/1024:.1f} MB)")
    
    return success

def test_pip_package_install():
    """Test pip package installation (Faster Whisper)."""
    print("\n" + "="*50)
    print("Testing Pip Package Installation (Faster Whisper)")
    print("="*50)
    
    downloader = ModelDownloader(models_dir="test_models", cache_dir="test_cache")
    
    # Test Whisper package installation
    success = downloader.download_model("whisper", "tiny", test_progress_callback)
    print(f"Whisper Package Install Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    
    # Check if package is installed
    try:
        import faster_whisper
        print(f"faster-whisper package version: {faster_whisper.__version__}")
        print("Package successfully accessible")
    except ImportError:
        print("Package not accessible after installation")
        success = False
    
    return success

def test_skip_models():
    """Test skip models (PyAnnote models)."""
    print("\n" + "="*50)
    print("Testing Skip Models (PyAnnote)")
    print("="*50)
    
    downloader = ModelDownloader(models_dir="test_models", cache_dir="test_cache")
    
    # Test PyAnnote VAD (should be skipped)
    success = downloader.download_model("pyannote_vad", "segmentation", test_progress_callback)
    print(f"PyAnnote VAD Skip Result: {'✅ SKIPPED' if not success else '❌ UNEXPECTED SUCCESS'}")
    
    # Test PyAnnote Diarization (should be skipped) 
    success = downloader.download_model("pyannote_diarization", "speaker_diarization", test_progress_callback)
    print(f"PyAnnote Diarization Skip Result: {'✅ SKIPPED' if not success else '❌ UNEXPECTED SUCCESS'}")
    
    return True  # Skip is expected behavior

def test_model_verification():
    """Test model access verification."""
    print("\n" + "="*50)
    print("Testing Model Access Verification")
    print("="*50)
    
    downloader = ModelDownloader(models_dir="test_models", cache_dir="test_cache")
    
    # Test verification for each model type
    models_to_test = [
        ("tts", "kokoro"),
        ("silero_vad", "v5"),
        ("whisper", "tiny"),
        ("pyannote_vad", "segmentation"),
        ("pyannote_diarization", "speaker_diarization")
    ]
    
    results = {}
    for model_type, model_variant in models_to_test:
        print(f"Verifying {model_type}:{model_variant}...")
        accessible = downloader.verify_model_access(model_type, model_variant)
        results[f"{model_type}:{model_variant}"] = accessible
        print(f"  Result: {'✅ ACCESSIBLE' if accessible else '❌ NOT ACCESSIBLE'}")
    
    return results

def cleanup_test_files():
    """Clean up test files."""
    print("\n" + "="*50)
    print("Cleaning Up Test Files")
    print("="*50)
    
    test_dirs = ["test_models", "test_cache"]
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
            print(f"Removed {test_dir}")
    
    print("Cleanup complete")

def main():
    """Main test function."""
    print("AI Companion Model Download Testing")
    print("="*50)
    
    setup_logging()
    
    # Test model verification first
    print("Phase 1: Model Access Verification")
    verification_results = test_model_verification()
    
    # Test each download method
    print("\nPhase 2: Individual Download Tests")
    download_results = {}
    
    # Test HuggingFace download
    try:
        download_results["huggingface"] = test_huggingface_download()
    except Exception as e:
        print(f"❌ HuggingFace test failed: {e}")
        download_results["huggingface"] = False
    
    # Test direct URL download
    try:
        download_results["direct_url"] = test_direct_url_download()
    except Exception as e:
        print(f"❌ Direct URL test failed: {e}")
        download_results["direct_url"] = False
    
    # Test pip package installation
    try:
        download_results["pip_package"] = test_pip_package_install()
    except Exception as e:
        print(f"❌ Pip package test failed: {e}")
        download_results["pip_package"] = False
    
    # Test skip functionality
    try:
        download_results["skip"] = test_skip_models()
    except Exception as e:
        print(f"❌ Skip models test failed: {e}")
        download_results["skip"] = False
    
    # Print summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    print("\nModel Access Verification:")
    for model, accessible in verification_results.items():
        status = "✅ PASS" if accessible else "❌ FAIL"
        print(f"  {model}: {status}")
    
    print("\nDownload Method Tests:")
    for method, success in download_results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {method}: {status}")
    
    # Overall result
    all_passed = all(download_results.values())
    print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    # Ask user if they want to clean up
    response = input("\nDo you want to clean up test files? (y/N): ").strip().lower()
    if response in ['y', 'yes']:
        cleanup_test_files()
    else:
        print("Test files preserved for inspection")

if __name__ == "__main__":
    main()
