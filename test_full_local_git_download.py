#!/usr/bin/env python3
"""
Test the full recommended model download process including local git models.
"""

import sys
import os
import logging
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.model_downloader import ModelDownloader

def main():
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    print("🚀 Testing Full Recommended Model Download Process")
    print("=" * 60)
    
    # Initialize model downloader
    downloader = ModelDownloader()
    
    print("\n📊 Current System Recommendations:")
    recommended = downloader.get_recommended_models()
    for model_type, variant in recommended.items():
        model_info = downloader.get_model_info(model_type, variant)
        source = model_info.get('source_type', 'unknown') if model_info else 'unknown'
        exists = downloader.check_model_exists(model_type, variant)
        status = "✅" if exists else "⬇️"
        print(f"  {status} {model_type}:{variant} ({source})")
    
    print(f"\n⬇️ Downloading all recommended models...")
    
    def progress_callback(percent, message):
        print(f"    [{percent:3d}%] {message}")
    
    results = downloader.download_recommended_models(progress_callback)
    
    print(f"\n📋 Download Results:")
    for model, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {model}")
    
    print(f"\n🎯 Final Status Check:")
    final_recommended = downloader.get_recommended_models()
    all_ready = True
    for model_type, variant in final_recommended.items():
        exists = downloader.check_model_exists(model_type, variant)
        status = "✅" if exists else "❌"
        if not exists:
            all_ready = False
        model_info = downloader.get_model_info(model_type, variant)
        source = model_info.get('source_type', 'unknown') if model_info else 'unknown'
        print(f"  {status} {model_type}:{variant} ({source})")
    
    if all_ready:
        print(f"\n🎉 SUCCESS: All recommended models are ready!")
    else:
        print(f"\n⚠️  Some models are still missing")
    
    print(f"\n📈 Download Summary:")
    print(downloader.get_download_summary())

if __name__ == "__main__":
    main()
