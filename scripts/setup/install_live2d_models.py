#!/usr/bin/env python3
"""
Install Live2D models from git repository to user data directory.
This should be called as part of the installation process.
"""
import os
import shutil
from pathlib import Path

def install_live2d_models():
    """Copy Live2D models from git repository to user data directory."""
    
    # Source: git repository
    repo_models_dir = Path("/home/nyx/ai2d_chat/src/live2d_models")
    
    # Destination: user data directory
    user_data_dir = Path.home() / ".local/share/ai2d_chat"
    user_models_dir = user_data_dir / "live2d_models"
    
    print("🎭 Installing Live2D models...")
    print(f"📁 Source: {repo_models_dir}")
    print(f"📂 Destination: {user_models_dir}")
    
    if not repo_models_dir.exists():
        print(f"❌ Source directory not found: {repo_models_dir}")
        return False
    
    # Create destination directory
    user_models_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy all model directories
    models_copied = 0
    for model_dir in repo_models_dir.iterdir():
        if model_dir.is_dir():
            dest_dir = user_models_dir / model_dir.name
            
            print(f"🎎 Installing model: {model_dir.name}")
            
            # Remove existing if present
            if dest_dir.exists():
                print(f"  🔄 Updating existing model...")
                shutil.rmtree(dest_dir)
            
            # Copy model directory
            shutil.copytree(model_dir, dest_dir)
            models_copied += 1
            print(f"  ✅ {model_dir.name} installed successfully")
    
    print(f"\n🎉 Live2D model installation completed!")
    print(f"📊 Models installed: {models_copied}")
    print(f"📍 Location: {user_models_dir}")
    
    return True

if __name__ == "__main__":
    install_live2d_models()
