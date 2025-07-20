#!/usr/bin/env python3
"""
Copy PyAnnote models from git repository to user data directory.
This resolves the path mismatch issue where models are in git but 
the system expects them in the user data directory.
"""
import os
import shutil
from pathlib import Path

def copy_pyannote_models():
    """Copy PyAnnote models from git to user data directory."""
    
    # Source paths (in git repository) - use relative path
    script_dir = Path(__file__).parent.parent.parent  # Go up to repo root  
    repo_base = script_dir
    git_pyannote_base = repo_base / "src/models/pyannote"
    
    # Destination paths (user data directory) 
    user_data_dir = Path.home() / ".local/share/ai2d_chat"
    user_pyannote_base = user_data_dir / "models/pyannote"
    
    # Models to copy
    models = {
        "segmentation-3.0": "segmentation-3.0/snapshots/e66f3d3b9eb0873085418a7b813d3b369bf160bb",
        "speaker-diarization-3.1": "speaker-diarization-3.1/snapshots/84fd25912480287da0247647c3d2b4853cb3ee5d"
    }
    
    print("🔄 Copying PyAnnote models from git to user data directory...")
    
    # Create destination directory
    user_pyannote_base.mkdir(parents=True, exist_ok=True)
    
    for model_name, git_path in models.items():
        src_path = git_pyannote_base / git_path
        dst_path = user_pyannote_base / model_name
        
        if src_path.exists():
            print(f"📁 Copying {model_name}...")
            print(f"   From: {src_path}")
            print(f"   To:   {dst_path}")
            
            # Remove destination if it exists
            if dst_path.exists():
                shutil.rmtree(dst_path)
            
            # Copy the model directory
            shutil.copytree(src_path, dst_path)
            print(f"✅ {model_name} copied successfully")
        else:
            print(f"❌ Source not found: {src_path}")
    
    print("\n🎉 PyAnnote model migration completed!")
    print(f"Models are now available in: {user_pyannote_base}")

if __name__ == "__main__":
    copy_pyannote_models()
