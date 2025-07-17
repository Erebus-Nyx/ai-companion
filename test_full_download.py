#!/usr/bin/env python3
"""
Test script for downloading all recommended models for the AI Companion.
This verifies the complete system works together.
"""

import os
import sys
import logging
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

def progress_callback(percent, message):
    """Progress callback for testing."""
    print(f"[{percent:6.1f}%] {message}")

def main():
    """Test downloading all recommended models."""
    print("=" * 60)
    print("AI COMPANION - FULL MODEL DOWNLOAD TEST")
    print("=" * 60)
    
    setup_logging()
    
    # Use test directories
    downloader = ModelDownloader(models_dir="full_test_models", cache_dir="full_test_cache")
    
    # Show download summary first
    print("\n📋 DOWNLOAD SUMMARY:")
    print(downloader.get_download_summary())
    
    # Get recommended models
    recommended = downloader.get_recommended_models()
    print(f"\n🎯 RECOMMENDED MODELS:")
    for model_type, variant in recommended.items():
        print(f"  - {model_type}: {variant}")
    
    # Check what's already available
    print(f"\n📦 CHECKING EXISTING MODELS:")
    for model_type, variant in recommended.items():
        exists = downloader.check_model_exists(model_type, variant)
        status = "✅ EXISTS" if exists else "⬇️  NEEDS DOWNLOAD"
        print(f"  - {model_type}:{variant}: {status}")
    
    # Download all recommended models
    print(f"\n🚀 DOWNLOADING RECOMMENDED MODELS...")
    results = downloader.download_recommended_models(progress_callback)
    
    # Show results
    print(f"\n📊 DOWNLOAD RESULTS:")
    success_count = 0
    total_count = len(results)
    
    for model, success in results.items():
        if success:
            success_count += 1
            print(f"  ✅ {model}: SUCCESS")
        else:
            print(f"  ❌ {model}: FAILED")
    
    # Final summary
    print(f"\n🏆 FINAL SUMMARY:")
    print(f"  Total Models: {total_count}")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {total_count - success_count}")
    
    if success_count == total_count:
        print(f"  🎉 ALL MODELS DOWNLOADED SUCCESSFULLY!")
    else:
        print(f"  ⚠️  Some models failed to download")
    
    # Show file structure
    test_dir = Path("full_test_models")
    if test_dir.exists():
        print(f"\n📁 DOWNLOADED FILE STRUCTURE:")
        for root, dirs, files in os.walk(test_dir):
            level = root.replace(str(test_dir), '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                file_path = Path(root) / file
                size_mb = file_path.stat().st_size / (1024 * 1024)
                print(f"{subindent}{file} ({size_mb:.1f} MB)")
    
    # Ask about cleanup
    response = input(f"\n🗑️  Clean up test files? (y/N): ").strip().lower()
    if response in ['y', 'yes']:
        import shutil
        for test_dir in ["full_test_models", "full_test_cache"]:
            if os.path.exists(test_dir):
                shutil.rmtree(test_dir)
                print(f"  Removed {test_dir}")
        print("  Cleanup complete!")
    else:
        print("  Test files preserved for inspection")

if __name__ == "__main__":
    main()
