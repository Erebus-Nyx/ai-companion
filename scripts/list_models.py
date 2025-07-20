#!/usr/bin/env python3
"""
List installed AI models and their metadata.
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.model_downloader import ModelDownloader

def main():
    """List all installed models with their metadata."""
    downloader = ModelDownloader()
    
    # Check if models exist
    print("📦 Installed AI Models Status:")
    print("=" * 50)
    
    available = downloader.list_available_models()
    
    for model_type, variants in available.items():
        print(f"\n🤖 {model_type.upper()} Models:")
        for variant, is_downloaded in variants.items():
            status = "✅ Downloaded" if is_downloaded else "❌ Not Downloaded"
            print(f"  {variant}: {status}")
    
    # Show detailed metadata
    metadata = downloader.get_installed_models_metadata()
    
    if metadata:
        print("\n" + "=" * 50)
        print("📋 Detailed Model Metadata:")
        print("=" * 50)
        
        for model_type, models in metadata.items():
            print(f"\n🔧 {model_type.upper()} Models:")
            for model in models:
                print(f"  Repository: {model.get('repo_id', 'Unknown')}")
                print(f"  Original File: {model.get('original_filename', 'Unknown')}")
                print(f"  Local File: {model.get('local_filename', 'Unknown')}")
                print(f"  Size: {model.get('size_mb', 0)} MB")
                print(f"  Downloaded: {model.get('download_date', 'Unknown')}")
                print("  " + "-" * 40)
    else:
        print("\n📝 No model metadata found.")
        print("   Models may have been downloaded before metadata tracking was implemented.")

if __name__ == "__main__":
    main()
