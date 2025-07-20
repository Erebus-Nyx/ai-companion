#!/usr/bin/env python3
"""
Live2D Model Installation and Management

Handles installation of Live2D models from project repository to user data directory,
and provides functionality to refresh/update the model list.
"""

import os
import shutil
import json
from pathlib import Path
from typing import Dict, List, Optional
import logging

class Live2DModelInstaller:
    """Manages Live2D model installation and updates."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Paths
        self.project_root = Path(__file__).parent.parent  # utils/live2d_model_installer.py -> ai2d_chat/
        self.source_models_dir = self.project_root / "live2d_models"
        self.user_data_dir = Path.home() / ".local" / "share" / "ai2d_chat"
        self.user_models_dir = self.user_data_dir / "live2d_models"
        self.model_registry_file = self.user_models_dir / "model_registry.json"
        
        # Ensure directories exist
        self.user_models_dir.mkdir(parents=True, exist_ok=True)
    
    def get_available_models_from_project(self) -> List[Dict]:
        """Scan project directory for available Live2D models."""
        models = []
        
        if not self.source_models_dir.exists():
            self.logger.warning(f"Source models directory not found: {self.source_models_dir}")
            return models
        
        for model_dir in self.source_models_dir.iterdir():
            if model_dir.is_dir():
                model_info = self._scan_model_directory(model_dir)
                if model_info:
                    models.append(model_info)
        
        return models
    
    def _scan_model_directory(self, model_dir: Path) -> Optional[Dict]:
        """Scan a model directory to extract model information."""
        try:
            # Look for model3.json (Cubism 3) or .model (Cubism 2) recursively
            model_files = list(model_dir.rglob("*.model3.json")) + list(model_dir.rglob("*.model"))
            
            if not model_files:
                self.logger.debug(f"No model files found in {model_dir}")
                return None
            
            # Use the first model file found
            model_file = model_files[0]
            
            # Extract model info
            model_info = {
                "name": model_dir.name,
                "source_path": str(model_dir),
                "model_file": str(model_file.relative_to(model_dir)),  # Relative path from model root
                "type": "model3" if model_file.suffix == ".json" else "model2",
                "size_mb": self._calculate_directory_size(model_dir),
                "files": self._list_model_files(model_dir),
                "model_count": len(model_files)  # How many model files this directory has
            }
            
            # Try to read model configuration for additional info
            if model_file.suffix == ".json":
                try:
                    with open(model_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        model_info.update({
                            "version": config.get("Version", "Unknown"),
                            "textures": len(config.get("FileReferences", {}).get("Textures", [])),
                            "motions": len(config.get("FileReferences", {}).get("Motions", {}))
                        })
                except Exception as e:
                    self.logger.debug(f"Could not read model config: {e}")
            
            return model_info
            
        except Exception as e:
            self.logger.error(f"Error scanning model directory {model_dir}: {e}")
            return None
    
    def _calculate_directory_size(self, directory: Path) -> float:
        """Calculate total size of directory in MB."""
        total_size = 0
        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception as e:
            self.logger.debug(f"Error calculating size for {directory}: {e}")
        
        return round(total_size / (1024 * 1024), 2)
    
    def _list_model_files(self, directory: Path) -> List[str]:
        """List all files in model directory."""
        files = []
        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    files.append(str(file_path.relative_to(directory)))
        except Exception as e:
            self.logger.debug(f"Error listing files for {directory}: {e}")
        
        return files
    
    def install_model(self, model_name: str) -> bool:
        """Install a specific model from project to user directory."""
        try:
            source_path = self.source_models_dir / model_name
            target_path = self.user_models_dir / model_name
            
            if not source_path.exists():
                self.logger.error(f"Source model not found: {source_path}")
                return False
            
            if target_path.exists():
                self.logger.info(f"Model already exists, updating: {model_name}")
                shutil.rmtree(target_path)
            
            # Copy model directory
            shutil.copytree(source_path, target_path)
            self.logger.info(f"Successfully installed model: {model_name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to install model {model_name}: {e}")
            return False
    
    def install_all_models(self) -> Dict[str, bool]:
        """Install all available models from project directory."""
        results = {}
        available_models = self.get_available_models_from_project()
        
        self.logger.info(f"Installing {len(available_models)} Live2D models...")
        
        for model in available_models:
            model_name = model["name"]
            success = self.install_model(model_name)
            results[model_name] = success
        
        # Update registry
        self.update_model_registry()
        
        return results
    
    def update_model_registry(self) -> bool:
        """Update the model registry with currently installed models."""
        try:
            installed_models = self.get_installed_models()
            
            registry = {
                "version": "1.0",
                "updated": str(Path(__file__).stat().st_mtime),
                "models": installed_models
            }
            
            with open(self.model_registry_file, 'w', encoding='utf-8') as f:
                json.dump(registry, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Updated model registry with {len(installed_models)} models")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update model registry: {e}")
            return False
    
    def get_installed_models(self) -> List[Dict]:
        """Get list of currently installed models in user directory."""
        models = []
        
        if not self.user_models_dir.exists():
            return models
        
        for model_dir in self.user_models_dir.iterdir():
            if model_dir.is_dir() and model_dir.name != "__pycache__":
                model_info = self._scan_model_directory(model_dir)
                if model_info:
                    model_info["installed_path"] = str(model_dir)
                    models.append(model_info)
        
        return models
    
    def refresh_models(self) -> Dict[str, int]:
        """Refresh models - install new ones and update registry."""
        try:
            # Get current state
            available_models = self.get_available_models_from_project()
            installed_models = {m["name"]: m for m in self.get_installed_models()}
            
            results = {
                "new_installed": 0,
                "updated": 0,
                "errors": 0
            }
            
            for model in available_models:
                model_name = model["name"]
                
                if model_name not in installed_models:
                    # New model
                    if self.install_model(model_name):
                        results["new_installed"] += 1
                    else:
                        results["errors"] += 1
                else:
                    # Check if update needed (compare file sizes or timestamps)
                    source_size = model["size_mb"]
                    installed_size = installed_models[model_name]["size_mb"]
                    
                    if abs(source_size - installed_size) > 0.1:  # Size difference threshold
                        if self.install_model(model_name):
                            results["updated"] += 1
                        else:
                            results["errors"] += 1
            
            # Update registry
            self.update_model_registry()
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to refresh models: {e}")
            return {"new_installed": 0, "updated": 0, "errors": 1}

def main():
    """CLI interface for model installation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Live2D Model Installer")
    parser.add_argument("action", choices=["install", "refresh", "list"], 
                       help="Action to perform")
    parser.add_argument("--model", help="Specific model name to install")
    
    args = parser.parse_args()
    
    installer = Live2DModelInstaller()
    
    if args.action == "install":
        if args.model:
            success = installer.install_model(args.model)
            print(f"{'✅' if success else '❌'} Model installation: {args.model}")
        else:
            results = installer.install_all_models()
            successful = sum(1 for success in results.values() if success)
            print(f"✅ Installed {successful}/{len(results)} models successfully")
    
    elif args.action == "refresh":
        results = installer.refresh_models()
        print(f"✅ Refresh complete:")
        print(f"   - New models: {results['new_installed']}")
        print(f"   - Updated: {results['updated']}")
        print(f"   - Errors: {results['errors']}")
    
    elif args.action == "list":
        installed = installer.get_installed_models()
        available = installer.get_available_models_from_project()
        
        print(f"📦 Available models in project: {len(available)}")
        for model in available:
            print(f"   - {model['name']} ({model['size_mb']} MB)")
        
        print(f"\n✅ Installed models: {len(installed)}")
        for model in installed:
            print(f"   - {model['name']} ({model['size_mb']} MB)")

if __name__ == "__main__":
    main()
