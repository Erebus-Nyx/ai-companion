#!/usr/bin/env python3
"""
Test script to verify local git models are properly recognized and accessible.
"""

import sys
import os
import logging
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.model_downloader import ModelDownloader
from utils.system_detector import SystemDetector

def main():
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    print("🧪 Testing Local Git Models")
    print("=" * 50)
    
    # Initialize model downloader
    downloader = ModelDownloader()
    
    # Test local git models specifically
    local_git_models = [
        ("whisper", "tiny"),
        ("silero_vad", "v5"), 
        ("pyannote_vad", "segmentation"),
        ("pyannote_diarization", "speaker_diarization")
    ]
    
    print("\n📋 Checking Local Git Models:")
    for model_type, model_variant in local_git_models:
        print(f"\n🔍 Testing {model_type}:{model_variant}")
        
        # Get model info
        model_info = downloader.get_model_info(model_type, model_variant)
        if model_info:
            print(f"  Source type: {model_info.get('source_type', 'unknown')}")
            print(f"  Local path: {model_info.get('local_path', 'N/A')}")
            print(f"  Size: {model_info.get('size_mb', 0)}MB")
        
        # Test access verification
        can_access = downloader.verify_model_access(model_type, model_variant)
        print(f"  ✅ Access verified: {can_access}")
        
        # Check if model exists (already available)
        exists = downloader.check_model_exists(model_type, model_variant)
        print(f"  ✅ Model exists: {exists}")
        
        # Get model path
        model_path = downloader.get_model_path(model_type, model_variant)
        print(f"  📁 Path: {model_path}")
        
        if exists and model_path:
            print(f"  📊 Directory contents:")
            if model_path.exists():
                for item in sorted(model_path.iterdir()):
                    if item.is_file():
                        size_mb = item.stat().st_size / (1024 * 1024)
                        print(f"    📄 {item.name} ({size_mb:.1f}MB)")
                    elif item.is_dir():
                        print(f"    📁 {item.name}/")
            else:
                print(f"    ❌ Path does not exist: {model_path}")
    
    print("\n🔧 Testing 'Download' (should be instant for local git models):")
    for model_type, model_variant in local_git_models:
        print(f"\n⬇️  'Downloading' {model_type}:{model_variant}")
        
        def progress_callback(percent, message):
            print(f"    [{percent:3d}%] {message}")
        
        success = downloader.download_model(model_type, model_variant, progress_callback)
        print(f"    ✅ Success: {success}")
    
    print("\n📊 Full Model Summary:")
    available = downloader.list_available_models()
    for model_type, variants in available.items():
        print(f"\n{model_type.upper()}:")
        for variant, downloaded in variants.items():
            status = "✅" if downloaded else "❌"
            model_info = downloader.get_model_info(model_type, variant)
            source = model_info.get('source_type', 'unknown') if model_info else 'unknown'
            print(f"  {status} {variant} ({source})")
    
    print(f"\n🎯 Recommended Models for Current System:")
    recommended = downloader.get_recommended_models()
    for model_type, variant in recommended.items():
        model_info = downloader.get_model_info(model_type, variant)
        source = model_info.get('source_type', 'unknown') if model_info else 'unknown'
        exists = downloader.check_model_exists(model_type, variant)
        status = "✅" if exists else "❌"
        print(f"  {status} {model_type}:{variant} ({source})")

if __name__ == "__main__":
    main()
