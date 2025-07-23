#!/usr/bin/env python3
"""
Install Packaged Live2D Models
Extracts pre-packaged model ZIP files during installation
"""

import os
import zipfile
import json
from pathlib import Path
import sys

def install_packaged_models(force_reinstall=False):
    """Install pre-packaged Live2D models from ZIP archives"""
    
    # Get paths
    repo_root = Path(__file__).parent.parent
    packaged_dir = repo_root / "live2d_models_packaged"
    
    # Get user data directory for models
    try:
        from config.config_manager import ConfigManager
        config_manager = ConfigManager()
        models_base_path = Path(config_manager.get_live2d_models_path())
    except ImportError:
        models_base_path = Path.home() / ".local/share/ai2d_chat/live2d_models"
    
    print(f"📂 Installing models to: {models_base_path}")
    models_base_path.mkdir(parents=True, exist_ok=True)
    
    # Check for manifest
    manifest_path = packaged_dir / "models_manifest.json"
    if not manifest_path.exists():
        print("❌ No models manifest found. Run package_models_for_distribution.py first.")
        return False
    
    # Load manifest
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    print(f"📋 Found {len(manifest['packaged_models'])} packaged models")
    
    installed_count = 0
    skipped_count = 0
    
    # Install each model
    for model_info in manifest['packaged_models']:
        model_name = model_info['name']
        zip_filename = model_info['filename']
        zip_path = packaged_dir / zip_filename
        
        model_install_dir = models_base_path / model_name
        
        # Check if already installed
        if model_install_dir.exists() and not force_reinstall:
            print(f"⏭️  Skipping {model_name} - already installed")
            skipped_count += 1
            continue
        
        # Extract model
        if not zip_path.exists():
            print(f"❌ ZIP file not found: {zip_path}")
            continue
        
        print(f"📦 Installing {model_name}...")
        
        # Create model directory
        model_install_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract ZIP
        try:
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(model_install_dir)
            
            # Verify installation
            model3_files = list(model_install_dir.rglob("*.model3.json"))
            if model3_files:
                print(f"✅ Installed {model_name} - found {model3_files[0].name}")
                installed_count += 1
            else:
                print(f"⚠️  Warning: {model_name} installed but no .model3.json found")
                installed_count += 1
                
        except Exception as e:
            print(f"❌ Failed to install {model_name}: {e}")
            # Clean up partial installation
            if model_install_dir.exists():
                import shutil
                shutil.rmtree(model_install_dir, ignore_errors=True)
    
    print(f"\n🎉 Installation complete:")
    print(f"   ✅ Installed: {installed_count} models")
    print(f"   ⏭️  Skipped: {skipped_count} models")
    
    # Register models with database
    if installed_count > 0:
        try:
            register_installed_models(models_base_path)
        except Exception as e:
            print(f"⚠️  Warning: Failed to register models in database: {e}")
            print("   Models installed but may need manual registration")
    
    return installed_count > 0

def register_installed_models(models_base_path):
    """Register installed models with the Live2D database"""
    print("\n📊 Registering models with database...")
    
    try:
        from databases.live2d_models_separated import Live2DModelsDB
        live2d_db = Live2DModelsDB()
        
        registered_count = 0
        
        for model_dir in models_base_path.iterdir():
            if model_dir.is_dir():
                model_name = model_dir.name
                
                # Check if already registered
                existing_models = live2d_db.get_all_models()
                if any(m['model_name'] == model_name for m in existing_models):
                    print(f"   ⏭️  {model_name} already registered")
                    continue
                
                # Find config file
                model3_files = list(model_dir.rglob("*.model3.json"))
                if model3_files:
                    config_file = str(model3_files[0].relative_to(models_base_path))
                    
                    # Register model
                    model_id = live2d_db.register_model(
                        model_name=model_name,
                        model_path=str(model_dir.relative_to(models_base_path)),
                        config_file=config_file,
                        description=f"Pre-packaged Live2D model: {model_name}"
                    )
                    
                    # Scan for motions
                    live2d_db.scan_and_register_motions(model_name, str(model_dir))
                    
                    print(f"   ✅ Registered {model_name} (ID: {model_id})")
                    registered_count += 1
                else:
                    print(f"   ⚠️  {model_name} - no .model3.json found")
        
        print(f"📊 Registered {registered_count} models in database")
        
    except ImportError as e:
        print(f"⚠️  Database registration skipped - dependencies not available: {e}")

def main():
    """Main installation process"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Install packaged Live2D models")
    parser.add_argument('--force', action='store_true', 
                       help='Force reinstall even if models already exist')
    
    args = parser.parse_args()
    
    print("🚀 Installing packaged Live2D models...")
    
    success = install_packaged_models(force_reinstall=args.force)
    
    if success:
        print("\n✅ Model installation completed successfully!")
    else:
        print("\n❌ Model installation failed or no models to install")
        sys.exit(1)

if __name__ == "__main__":
    main()
