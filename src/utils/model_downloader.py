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


def get_user_data_dir() -> Path:
    """Get platform-appropriate user data directory for AI Companion models."""
    if os.name == 'nt':  # Windows
        data_dir = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming'))
    elif os.name == 'posix':  # Linux/macOS
        # Use XDG_DATA_HOME or fallback to ~/.local/share
        data_dir = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local' / 'share'))
    else:
        data_dir = Path.home() / '.ai-companion'
    
    return data_dir / 'ai-companion'


class ModelDownloader:
    """
    Handles downloading and managing AI models for the companion application.
    Uses user data directories for cross-platform compatibility and pipx installation.
    """
    
    def __init__(self, models_dir: Optional[str] = None, cache_dir: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        # Use user data directory if not specified
        if models_dir is None or models_dir == "models":
            user_data_dir = get_user_data_dir()
            self.models_dir = user_data_dir / "models"
            self.cache_dir = user_data_dir / "cache"
        else:
            # Support legacy relative paths for development
            self.models_dir = Path(models_dir)
            self.cache_dir = Path(cache_dir) if cache_dir else Path("cache")
        
        # Create directories
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"AI Companion models directory: {self.models_dir}")
        self.logger.info(f"AI Companion cache directory: {self.cache_dir}")
        
        self.system_detector = SystemDetector()
        
        # Model registry with different variants - ALL required models for AI Companion
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
                        "kokoro-v1_0.onnx",
                        "voices.json",
                        "config.json"
                    ],
                    "size_mb": 350,
                    "min_ram_gb": 1
                }
            },
            "whisper": {
                "tiny": {
                    "source_type": "pip_package",
                    "package_name": "faster-whisper",
                    "model_name": "tiny",
                    "size_mb": 39,
                    "min_ram_gb": 1
                },
                "base": {
                    "source_type": "pip_package", 
                    "package_name": "faster-whisper",
                    "model_name": "base",
                    "size_mb": 142,
                    "min_ram_gb": 1
                },
                "small": {
                    "source_type": "pip_package",
                    "package_name": "faster-whisper", 
                    "model_name": "small",
                    "size_mb": 244,
                    "min_ram_gb": 2
                }
            },
            "silero_vad": {
                "v5": {
                    "source_type": "direct_url",
                    "download_url": "https://github.com/snakers4/silero-vad/releases/download/v5.0/silero_vad.onnx",
                    "local_path": str(Path("models/silero_vad/silero_vad.onnx")),
                    "filename": "silero_vad.onnx",
                    "size_mb": 2,
                    "min_ram_gb": 1
                }
            },
            "pyannote_vad": {
                "segmentation": {
                    "source_type": "skip",
                    "reason": "Requires HuggingFace authentication - install manually if needed",
                    "manual_install_cmd": "pip install pyannote.audio",
                    "size_mb": 17,
                    "min_ram_gb": 1
                }
            },
            "pyannote_diarization": {
                "speaker_diarization": {
                    "source_type": "skip",
                    "reason": "Requires HuggingFace authentication - install manually if needed", 
                    "manual_install_cmd": "pip install pyannote.audio",
                    "size_mb": 23,
                    "min_ram_gb": 2
                }
            }
        }
    
    def get_recommended_models(self) -> Dict[str, str]:
        """Get recommended models based on system capabilities."""
        recommended = self.system_detector.get_recommended_models()
        capabilities = self.system_detector.capabilities
        
        # Map to our model registry based on system performance
        llm_size = capabilities["recommended_llm_size"]
        memory_gb = self.system_detector.system_info.get("total_memory_gb", 4)
        
        # Select whisper model based on system capability
        if memory_gb >= 8:
            whisper_size = "small"
        elif memory_gb >= 4:
            whisper_size = "base" 
        else:
            whisper_size = "tiny"
        
        # All required models for AI Companion
        models = {
            "llm": llm_size,
            "tts": "kokoro",
            "whisper": whisper_size,
            "silero_vad": "v5",
            "pyannote_vad": "segmentation", 
            "pyannote_diarization": "speaker_diarization"
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
            
        elif model_type == "whisper":
            # Check whisper models
            whisper_dir = self.models_dir / "whisper" / model_variant
            for filename in model_info["files"]:
                if not (whisper_dir / filename).exists():
                    return False
            return True
            
        elif model_type == "silero_vad":
            # Check silero VAD model
            silero_path = self.models_dir / "silero_vad" / model_info["filename"]
            return silero_path.exists()
            
        elif model_type in ["pyannote_vad", "pyannote_diarization"]:
            # Check pyannote models
            pyannote_dir = self.models_dir / model_type / model_variant
            for filename in model_info["files"]:
                if not (pyannote_dir / filename).exists():
                    return False
            return True
        
        return False
    
    def verify_model_access(self, model_type: str, model_variant: str) -> bool:
        """Verify that a model is accessible from its source before attempting download."""
        if model_type not in self.model_registry:
            self.logger.error(f"Unknown model type: {model_type}")
            return False
        
        if model_variant not in self.model_registry[model_type]:
            self.logger.error(f"Unknown model variant: {model_variant} for type {model_type}")
            return False
        
        model_info = self.model_registry[model_type][model_variant]
        source_type = model_info.get("source_type", "huggingface")
        
        try:
            if source_type == "huggingface":
                # Original HuggingFace verification
                from huggingface_hub import repo_exists, list_repo_files
                repo_id = model_info["repo_id"]
                
                if not repo_exists(repo_id):
                    self.logger.error(f"Repository {repo_id} does not exist or is not accessible")
                    return False
                
                available_files = list(list_repo_files(repo_id))
                self.logger.info(f"Repository {repo_id} is accessible with {len(available_files)} files")
                
                # Check required files
                if "filename" in model_info:
                    required_file = model_info["filename"]
                    if required_file not in available_files:
                        self.logger.error(f"Required file {required_file} not found in {repo_id}")
                        return False
                    self.logger.info(f"✅ Required file {required_file} found in {repo_id}")
                elif "files" in model_info:
                    required_files = model_info["files"]
                    missing_files = [f for f in required_files if f not in available_files]
                    if missing_files:
                        self.logger.error(f"Missing files in {repo_id}: {missing_files}")
                        return False
                    for f in required_files:
                        self.logger.info(f"✅ Required file {f} found in {repo_id}")
                        
            elif source_type == "direct_url":
                # Check if direct URL is accessible
                import requests
                url = model_info["download_url"]
                response = requests.head(url, timeout=10)
                if response.status_code == 200:
                    self.logger.info(f"✅ Direct URL {url} is accessible")
                    return True
                else:
                    self.logger.error(f"Direct URL {url} returned status {response.status_code}")
                    return False
                    
            elif source_type == "pip_package":
                # Check if package is installable (always return True for pip packages)
                package_name = model_info["package_name"]
                self.logger.info(f"✅ Pip package {package_name} will be installed if needed")
                return True
                
            elif source_type == "skip":
                # Models that should be skipped
                reason = model_info.get("reason", "No download source available")
                self.logger.warning(f"⚠️  Skipping {model_type}:{model_variant} - {reason}")
                manual_cmd = model_info.get("manual_install_cmd")
                if manual_cmd:
                    self.logger.info(f"💡 Manual installation: {manual_cmd}")
                return False
                
            return True
            
        except ImportError:
            self.logger.error("Required dependencies not available - cannot verify model access")
            return False
        except Exception as e:
            self.logger.error(f"Failed to verify access to {model_type}:{model_variant}: {e}")
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
        source_type = model_info.get("source_type", "huggingface")
        
        # Skip models that require manual installation
        if source_type == "skip":
            reason = model_info.get("reason", "No download source available")
            manual_cmd = model_info.get("manual_install_cmd")
            self.logger.warning(f"⚠️  Skipping {model_type}:{model_variant} - {reason}")
            if manual_cmd:
                self.logger.info(f"💡 To use this model, run: {manual_cmd}")
            return False
        
        # Verify model access before attempting download
        if not self.verify_model_access(model_type, model_variant):
            self.logger.error(f"Cannot access {model_type}:{model_variant} - skipping download")
            return False
        
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
            if source_type == "huggingface":
                if model_type == "llm":
                    return self._download_llm_model(model_info, progress_callback)
                elif model_type == "tts":
                    return self._download_tts_model(model_variant, model_info, progress_callback)
            elif source_type == "direct_url":
                return self._download_direct_url(model_type, model_variant, model_info, progress_callback)
            elif source_type == "pip_package":
                return self._install_pip_package(model_type, model_variant, model_info, progress_callback)
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
    
    def _download_whisper_model(self, model_variant: str, model_info: Dict, 
                               progress_callback: Optional[Callable] = None) -> bool:
        """Download Whisper model files."""
        try:
            repo_id = model_info["repo_id"]
            files = model_info["files"]
            
            self.logger.info(f"Downloading Whisper model: {repo_id}")
            
            # Create Whisper models directory
            whisper_dir = self.models_dir / "whisper" / model_variant
            whisper_dir.mkdir(parents=True, exist_ok=True)
            
            for i, filename in enumerate(files):
                self.logger.info(f"Downloading Whisper file: {filename}")
                
                downloaded_path = hf_hub_download(
                    repo_id=repo_id,
                    filename=filename,
                    cache_dir=str(self.cache_dir),
                    resume_download=True
                )
                
                # Copy to our models directory
                target_path = whisper_dir / filename
                if not target_path.exists():
                    import shutil
                    shutil.copy2(downloaded_path, target_path)
                
                if progress_callback:
                    progress = int(((i + 1) / len(files)) * 100)
                    progress_callback(progress, progress, f"Downloaded: {filename}")
            
            self.logger.info(f"Whisper model downloaded successfully: {whisper_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to download Whisper model: {e}")
            return False
    
    def _download_silero_vad_model(self, model_variant: str, model_info: Dict, 
                                  progress_callback: Optional[Callable] = None) -> bool:
        """Download Silero VAD model."""
        try:
            repo_id = model_info["repo_id"]
            filename = model_info["filename"]
            
            self.logger.info(f"Downloading Silero VAD model: {repo_id}/{filename}")
            
            # Create Silero VAD models directory
            silero_dir = self.models_dir / "silero_vad"
            silero_dir.mkdir(parents=True, exist_ok=True)
            
            downloaded_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                cache_dir=str(self.cache_dir),
                resume_download=True
            )
            
            # Copy to our models directory
            target_path = silero_dir / filename
            if not target_path.exists():
                import shutil
                shutil.copy2(downloaded_path, target_path)
            
            if progress_callback:
                progress_callback(100, 100, f"Silero VAD model downloaded: {filename}")
            
            self.logger.info(f"Silero VAD model downloaded successfully: {target_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to download Silero VAD model: {e}")
            return False
    
    def _download_pyannote_model(self, model_variant: str, model_info: Dict, 
                                progress_callback: Optional[Callable] = None, model_subtype: str = "") -> bool:
        """Download PyAnnote model files."""
        try:
            repo_id = model_info["repo_id"]
            files = model_info["files"]
            
            self.logger.info(f"Downloading PyAnnote {model_subtype} model: {repo_id}")
            
            # Create PyAnnote models directory based on type
            if model_subtype == "vad":
                pyannote_dir = self.models_dir / "pyannote_vad" / model_variant
            elif model_subtype == "diarization":
                pyannote_dir = self.models_dir / "pyannote_diarization" / model_variant
            else:
                pyannote_dir = self.models_dir / "pyannote" / model_variant
                
            pyannote_dir.mkdir(parents=True, exist_ok=True)
            
            for i, filename in enumerate(files):
                self.logger.info(f"Downloading PyAnnote file: {filename}")
                
                downloaded_path = hf_hub_download(
                    repo_id=repo_id,
                    filename=filename,
                    cache_dir=str(self.cache_dir),
                    resume_download=True
                )
                
                # Copy to our models directory
                target_path = pyannote_dir / filename
                if not target_path.exists():
                    import shutil
                    shutil.copy2(downloaded_path, target_path)
                
                if progress_callback:
                    progress = int(((i + 1) / len(files)) * 100)
                    progress_callback(progress, progress, f"Downloaded: {filename}")
            
            self.logger.info(f"PyAnnote {model_subtype} model downloaded successfully: {pyannote_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to download PyAnnote {model_subtype} model: {e}")
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

    def _download_direct_url(self, model_type: str, model_variant: str, model_info: dict, progress_callback=None):
        """Download model from direct URL."""
        import urllib.request
        import shutil
        import zipfile
        import tarfile
        
        download_url = model_info["download_url"]
        local_path = model_info["local_path"]
        
        self.logger.info(f"📥 Downloading {model_type}:{model_variant} from {download_url}")
        
        # Create directory structure
        local_dir = os.path.dirname(local_path)
        os.makedirs(local_dir, exist_ok=True)
        
        # Download file
        try:
            if progress_callback:
                progress_callback(0, f"Starting download of {model_variant}")
            
            # Use urllib to download with progress tracking
            def report_progress(block_num, block_size, total_size):
                if progress_callback and total_size > 0:
                    percent = min(100, (block_num * block_size / total_size) * 100)
                    progress_callback(percent, f"Downloading {model_variant}: {percent:.1f}%")
            
            urllib.request.urlretrieve(download_url, local_path, reporthook=report_progress)
            
            # Extract if it's an archive
            if local_path.endswith('.zip'):
                with zipfile.ZipFile(local_path, 'r') as zip_ref:
                    extract_dir = os.path.splitext(local_path)[0]
                    zip_ref.extractall(extract_dir)
                    self.logger.info(f"✅ Extracted to {extract_dir}")
            elif local_path.endswith(('.tar.gz', '.tgz')):
                with tarfile.open(local_path, 'r:gz') as tar_ref:
                    extract_dir = os.path.splitext(os.path.splitext(local_path)[0])[0]
                    tar_ref.extractall(extract_dir)
                    self.logger.info(f"✅ Extracted to {extract_dir}")
            
            if progress_callback:
                progress_callback(100, f"✅ {model_variant} downloaded successfully")
            
            self.logger.info(f"✅ Successfully downloaded {model_type}:{model_variant}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to download {model_type}:{model_variant}: {e}")
            # Clean up partial download
            if os.path.exists(local_path):
                os.remove(local_path)
            return False

    def _install_pip_package(self, model_type: str, model_variant: str, model_info: dict, progress_callback=None):
        """Install model via pip package."""
        import subprocess
        import sys
        
        package_name = model_info["package_name"]
        
        self.logger.info(f"📦 Installing {model_type}:{model_variant} via pip package: {package_name}")
        
        try:
            if progress_callback:
                progress_callback(0, f"Installing {package_name}")
            
            # Install package using pip
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package_name
            ], capture_output=True, text=True, check=True)
            
            if progress_callback:
                progress_callback(100, f"✅ {package_name} installed successfully")
            
            self.logger.info(f"✅ Successfully installed {model_type}:{model_variant}")
            self.logger.debug(f"Pip output: {result.stdout}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"❌ Failed to install {model_type}:{model_variant}: {e}")
            self.logger.error(f"Pip stderr: {e.stderr}")
            return False


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
