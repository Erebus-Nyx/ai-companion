#!/usr/bin/env python3
"""
Package Live2D Models for Distribution
Converts unpacked model directories to ZIP archives for repository distribution
"""

import os
import zipfile
import shutil
from pathlib import Path
import json

def package_model_directory(model_dir, output_dir):
    """Package a single model directory into a ZIP file"""
    model_name = model_dir.name
    zip_path = output_dir / f"{model_name}.zip"
    
    print(f"📦 Packaging {model_name}...")
    
    # Create ZIP file
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(model_dir):
            for file in files:
                file_path = Path(root) / file
                # Calculate relative path within the model directory
                arcname = file_path.relative_to(model_dir)
                zipf.write(file_path, arcname)
                
    print(f"✅ Created {zip_path} ({zip_path.stat().st_size // 1024} KB)")
    return zip_path

def create_model_manifest(models_dir, zip_dir):
    """Create a manifest of packaged models for installation"""
    manifest = {
        "packaged_models": [],
        "version": "1.0",
        "description": "Pre-packaged Live2D models for AI2D Chat"
    }
    
    for zip_file in zip_dir.glob("*.zip"):
        model_name = zip_file.stem
        manifest["packaged_models"].append({
            "name": model_name,
            "filename": zip_file.name,
            "size": zip_file.stat().st_size,
            "description": f"Live2D model: {model_name}"
        })
    
    manifest_path = zip_dir / "models_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"📋 Created manifest: {manifest_path}")
    return manifest_path

def main():
    """Main packaging process"""
    repo_root = Path(__file__).parent.parent
    models_dir = repo_root / "live2d_models"
    
    # Create output directory for ZIP files
    zip_output_dir = repo_root / "live2d_models_packaged"
    zip_output_dir.mkdir(exist_ok=True)
    
    if not models_dir.exists():
        print("❌ live2d_models directory not found")
        return
    
    print(f"🔍 Scanning models directory: {models_dir}")
    
    # Package each model directory
    packaged_models = []
    for item in models_dir.iterdir():
        if item.is_dir() and item.name != ".git":
            # Check if it looks like a Live2D model (has .model3.json)
            model3_files = list(item.rglob("*.model3.json"))
            if model3_files:
                zip_path = package_model_directory(item, zip_output_dir)
                packaged_models.append(zip_path)
                print(f"   📁 Found config: {model3_files[0].relative_to(item)}")
            else:
                print(f"⚠️  Skipping {item.name} - no .model3.json found")
    
    if packaged_models:
        # Create manifest
        create_model_manifest(models_dir, zip_output_dir)
        
        print(f"\n✅ Packaged {len(packaged_models)} models:")
        for zip_path in packaged_models:
            print(f"   📦 {zip_path.name}")
        
        print(f"\n📂 ZIP files created in: {zip_output_dir}")
        print("\n🗒️  Next steps:")
        print("1. Review the packaged ZIP files")
        print("2. Update installation script to extract these models")
        print("3. Add live2d_models_packaged/ to repository")
        print("4. Add live2d_models/ to .gitignore (keep only README.md)")
        
    else:
        print("❌ No valid Live2D models found to package")

if __name__ == "__main__":
    main()
