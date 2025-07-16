"""
Model downloader for AI Companion application.
Handles automatic downloading and management of LLM and TTS models based on system capabilities.
"""

import os
import requests
import logging
from pathlib import Path
from typing import Dict, Optional, Callable
from urllib.parse import urlparse
import hashlib
import json
from huggingface_hub import hf_hub_download, list_repo_files
from tqdm import tqdm

from .system_detector import SystemDetector


class ModelDownloader:
    """
    Handles downloading and managing AI models for the companion application.
    """
    
    def __init__(self, models_dir: str = "models", cache_dir: str = "cache"):
        self.logger = logging.getLogger(__name__)
        self.models_dir = Path(models_dir)
        self.cache_dir = Path(cache_dir)
        
        # Create directories
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.system_detector = SystemDetector()
        
        # Model registry with different variants
        self.model_registry = {
            "llm": {
                "tiny": {
                    "repo_id": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
                    "filename": "tinyllama-1.1b-chat-v1.0.Q4_0.gguf",
                    "size_mb": 700,
                    "min_ram_gb": 2
                },
                "small": {
                    "repo_id": "TheBloke/Llama-2-7B-Chat-GGUF", 
                    "filename": "llama-2-7b-chat.Q4_0.gguf",
                    "size_mb": 4000,
                    "min_ram_gb": 6
                },
                "medium": {
                    "repo_id": "TheBloke/Llama-2-13B-Chat-GGUF",
                    "filename": "llama-2-13b-chat.Q4_0.gguf", 
                    "size_mb": 7000,
                    "min_ram_gb": 10
                }
            },
            "tts": {
                "kokoro": {
                    "repo_id": "hexgrad/Kokoro-82M",
                    "files": [
                        "kokoro-v0_19.onnx",
                        "voices.json"
                    ],
                    "size_mb": 350,
                    "min_ram_gb": 1
                }
            }
        }
    
    def get_recommended_models(self) -> Dict[str, str]:
        """Get recommended models based on system capabilities."""
        recommended = self.system_detector.get_recommended_models()
        capabilities = self.system_detector.capabilities
        
        # Map to our model registry
        llm_size = capabilities["recommended_llm_size"]
        
        models = {
            "llm": llm_size,
            "tts": "kokoro"
        }
        
        return models
    
    def check_model_exists(self, model_type: str, model_variant: str) -> bool:
        """Check if a model is already downloaded."""
        if model_type not in self.model_registry:
            return False
        
        if model_variant not in self.model_registry[model_type]:
            return False
        
        model_info = self.model_registry[model_type][model_variant]
        
        if model_type == "llm":
            model_path = self.models_dir / "llm" / model_info["filename"]
            return model_path.exists()
        elif model_type == "tts":
            # Check if all required files exist
            tts_dir = self.models_dir / "tts" / model_variant
            for filename in model_info["files"]:
                if not (tts_dir / filename).exists():
                    return False
            return True
        
        return False
    
    def download_model(self, model_type: str, model_variant: str, 
                      progress_callback: Optional[Callable] = None) -> bool:
        """Download a specific model variant."""
        if model_type not in self.model_registry:
            self.logger.error(f"Unknown model type: {model_type}")
            return False
        
        if model_variant not in self.model_registry[model_type]:
            self.logger.error(f"Unknown model variant: {model_variant} for type {model_type}")
            return False
        
        model_info = self.model_registry[model_type][model_variant]
        
        # Check system requirements
        system_ram = self.system_detector.system_info.get("total_memory_gb", 0)
        if system_ram < model_info["min_ram_gb"]:
            self.logger.warning(
                f"Insufficient RAM for {model_type}:{model_variant}. "
                f"Required: {model_info['min_ram_gb']}GB, Available: {system_ram}GB"
            )
            return False
        
        # Check available disk space
        disk_free = self.system_detector.system_info.get("disk_free_gb", 0)
        if disk_free < (model_info["size_mb"] / 1024) * 1.5:  # 1.5x for safety
            self.logger.error(
                f"Insufficient disk space for {model_type}:{model_variant}. "
                f"Required: {model_info['size_mb']}MB, Available: {disk_free*1024}MB"
            )
            return False
        
        try:
            if model_type == "llm":
                return self._download_llm_model(model_info, progress_callback)
            elif model_type == "tts":
                return self._download_tts_model(model_variant, model_info, progress_callback)
        except Exception as e:
            self.logger.error(f"Failed to download {model_type}:{model_variant}: {e}")
            return False
        
        return False
    
    def _download_llm_model(self, model_info: Dict, progress_callback: Optional[Callable] = None) -> bool:
        """Download LLM model from Hugging Face."""
        try:
            repo_id = model_info["repo_id"]
            filename = model_info["filename"]
            
            self.logger.info(f"Downloading LLM model: {repo_id}/{filename}")
            
            # Create LLM models directory
            llm_dir = self.models_dir / "llm"
            llm_dir.mkdir(parents=True, exist_ok=True)
            
            # Download using huggingface_hub
            downloaded_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                cache_dir=str(self.cache_dir),
                resume_download=True
            )
            
            # Copy to our models directory
            target_path = llm_dir / filename
            if not target_path.exists():
                import shutil
                shutil.copy2(downloaded_path, target_path)
            
            if progress_callback:
                progress_callback(100, f"LLM model downloaded: {filename}")
            
            self.logger.info(f"LLM model downloaded successfully: {target_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to download LLM model: {e}")
            return False
    
    def _download_tts_model(self, model_variant: str, model_info: Dict, 
                           progress_callback: Optional[Callable] = None) -> bool:
        """Download TTS model files."""
        try:
            repo_id = model_info["repo_id"]
            files = model_info["files"]
            
            self.logger.info(f"Downloading TTS model: {repo_id}")
            
            # Create TTS models directory
            tts_dir = self.models_dir / "tts" / model_variant
            tts_dir.mkdir(parents=True, exist_ok=True)
            
            for i, filename in enumerate(files):
                self.logger.info(f"Downloading TTS file: {filename}")
                
                downloaded_path = hf_hub_download(
                    repo_id=repo_id,
                    filename=filename,
                    cache_dir=str(self.cache_dir),
                    resume_download=True
                )
                
                # Copy to our models directory
                target_path = tts_dir / filename
                if not target_path.exists():
                    import shutil
                    shutil.copy2(downloaded_path, target_path)
                
                if progress_callback:
                    progress = int(((i + 1) / len(files)) * 100)
                    progress_callback(progress, f"Downloaded: {filename}")
            
            self.logger.info(f"TTS model downloaded successfully: {tts_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to download TTS model: {e}")
            return False
    
    def download_recommended_models(self, progress_callback: Optional[Callable] = None) -> Dict[str, bool]:
        """Download all recommended models for the current system."""
        recommended = self.get_recommended_models()
        results = {}
        
        for model_type, model_variant in recommended.items():
            self.logger.info(f"Downloading recommended {model_type}: {model_variant}")
            
            if self.check_model_exists(model_type, model_variant):
                self.logger.info(f"Model {model_type}:{model_variant} already exists, skipping")
                results[f"{model_type}:{model_variant}"] = True
                continue
            
            success = self.download_model(model_type, model_variant, progress_callback)
            results[f"{model_type}:{model_variant}"] = success
            
            if not success:
                self.logger.error(f"Failed to download {model_type}:{model_variant}")
        
        return results
    
    def get_model_path(self, model_type: str, model_variant: str) -> Optional[Path]:
        """Get the local path to a downloaded model."""
        if not self.check_model_exists(model_type, model_variant):
            return None
        
        if model_type == "llm":
            model_info = self.model_registry[model_type][model_variant]
            return self.models_dir / "llm" / model_info["filename"]
        elif model_type == "tts":
            return self.models_dir / "tts" / model_variant
        
        return None
    
    def list_available_models(self) -> Dict[str, Dict[str, bool]]:
        """List all available models and their download status."""
        available = {}
        
        for model_type, variants in self.model_registry.items():
            available[model_type] = {}
            for variant_name in variants.keys():
                available[model_type][variant_name] = self.check_model_exists(model_type, variant_name)
        
        return available
    
    def get_model_info(self, model_type: str, model_variant: str) -> Optional[Dict]:
        """Get detailed information about a model."""
        if model_type not in self.model_registry:
            return None
        
        if model_variant not in self.model_registry[model_type]:
            return None
        
        model_info = self.model_registry[model_type][model_variant].copy()
        model_info["downloaded"] = self.check_model_exists(model_type, model_variant)
        model_info["local_path"] = str(self.get_model_path(model_type, model_variant)) if model_info["downloaded"] else None
        
        return model_info
    
    def cleanup_cache(self):
        """Clean up downloaded model cache."""
        try:
            import shutil
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info("Model cache cleaned up")
        except Exception as e:
            self.logger.error(f"Failed to cleanup cache: {e}")
    
    def get_download_summary(self) -> str:
        """Get a summary of download requirements and recommendations."""
        recommended = self.get_recommended_models()
        available = self.list_available_models()
        
        summary = "Model Download Summary:\n"
        summary += "=" * 30 + "\n"
        
        total_size_mb = 0
        
        for model_type, model_variant in recommended.items():
            model_info = self.get_model_info(model_type, model_variant)
            if model_info:
                status = "✓ Downloaded" if model_info["downloaded"] else "⬇ Required"
                summary += f"{model_type.upper()} ({model_variant}): {status}\n"
                summary += f"  Size: {model_info['size_mb']}MB\n"
                summary += f"  RAM Required: {model_info['min_ram_gb']}GB\n"
                
                if not model_info["downloaded"]:
                    total_size_mb += model_info['size_mb']
        
        if total_size_mb > 0:
            summary += f"\nTotal download required: {total_size_mb}MB ({total_size_mb/1024:.1f}GB)\n"
        else:
            summary += "\nAll required models are already downloaded!\n"
        
        return summary


def main():
    """CLI interface for model downloading."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Companion Model Downloader")
    parser.add_argument("--download-recommended", action="store_true", 
                       help="Download all recommended models")
    parser.add_argument("--list", action="store_true", 
                       help="List available models")
    parser.add_argument("--summary", action="store_true",
                       help="Show download summary")
    parser.add_argument("--model-type", type=str, choices=["llm", "tts"],
                       help="Specific model type to download")
    parser.add_argument("--model-variant", type=str,
                       help="Specific model variant to download")
    
    args = parser.parse_args()
    
    downloader = ModelDownloader()
    
    if args.summary:
        print(downloader.get_download_summary())
    elif args.list:
        available = downloader.list_available_models()
        print("Available Models:")
        for model_type, variants in available.items():
            print(f"\n{model_type.upper()}:")
            for variant, downloaded in variants.items():
                status = "✓" if downloaded else "✗"
                print(f"  {status} {variant}")
    elif args.download_recommended:
        def progress_callback(percent, message):
            print(f"[{percent:3d}%] {message}")
        
        print("Downloading recommended models...")
        results = downloader.download_recommended_models(progress_callback)
        
        print("\nDownload Results:")
        for model, success in results.items():
            status = "✓" if success else "✗"
            print(f"  {status} {model}")
    elif args.model_type and args.model_variant:
        def progress_callback(percent, message):
            print(f"[{percent:3d}%] {message}")
        
        success = downloader.download_model(args.model_type, args.model_variant, progress_callback)
        if success:
            print(f"Successfully downloaded {args.model_type}:{args.model_variant}")
        else:
            print(f"Failed to download {args.model_type}:{args.model_variant}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

def get_model_urls(system_config):
    # Placeholder for model URLs based on system configuration
    model_urls = {
        'llm': 'https://example.com/path/to/llm/model',
        'tts': 'https://example.com/path/to/tts/model'
    }
    return model_urls

def download_models(system_config):
    model_urls = get_model_urls(system_config)
    download_status = {}

    for model_type, url in model_urls.items():
        save_path = os.path.join('models', f'{model_type}_model.bin')
        success = download_model(url, save_path)
        download_status[model_type] = success

    return download_status
