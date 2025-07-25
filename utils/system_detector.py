"""
System detector for AI Companion application.
Auto-detects hardware capabilities and recommends appropriate model configurations.
"""

import platform
import psutil
import subprocess
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import json


class SystemDetector:
    """
    Detects system capabilities and recommends optimal AI model configurations.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.system_info = self.detect_system()
        self.capabilities = self.assess_capabilities()
    
    def get_system_info(self) -> Dict[str, any]:
        """Get the detected system information including capabilities."""
        # Combine system info with capabilities
        combined_info = self.system_info.copy()
        combined_info.update(self.capabilities)
        # Add 'tier' key for backward compatibility
        combined_info['tier'] = self.capabilities.get('performance_tier', 'low')
        return combined_info
    
    def detect_system(self) -> Dict[str, any]:
        """Detect comprehensive system information."""
        try:
            # Basic system info
            system_info = {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "architecture": platform.architecture()[0],
                "processor": platform.processor(),
                "machine": platform.machine(),
                "python_version": platform.python_version(),
            }
            
            # Memory information
            memory = psutil.virtual_memory()
            system_info.update({
                "total_memory_gb": round(memory.total / (1024**3), 2),
                "available_memory_gb": round(memory.available / (1024**3), 2),
                "memory_percent_used": memory.percent
            })
            
            # CPU information
            system_info.update({
                "cpu_count": psutil.cpu_count(logical=False),
                "cpu_count_logical": psutil.cpu_count(logical=True),
                "cpu_freq_max": psutil.cpu_freq().max if psutil.cpu_freq() else None,
            })
            
            # GPU detection
            gpu_info = self._detect_gpu()
            system_info.update(gpu_info)
            
            # Storage information
            disk = psutil.disk_usage('/')
            system_info.update({
                "disk_total_gb": round(disk.total / (1024**3), 2),
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "disk_percent_used": round((disk.used / disk.total) * 100, 2)
            })
            
            # Raspberry Pi specific detection
            system_info["is_raspberry_pi"] = self._is_raspberry_pi()
            
            self.logger.info("System detection completed successfully")
            return system_info
            
        except Exception as e:
            self.logger.error(f"Error detecting system: {e}")
            # Return minimal fallback info
            return {
                "platform": platform.system(),
                "total_memory_gb": 4.0,  # Conservative fallback
                "cpu_count": 2,
                "has_cuda": False,
                "is_raspberry_pi": False
            }
    
    def _detect_gpu(self) -> Dict[str, any]:
        """Detect GPU capabilities."""
        gpu_info = {
            "has_cuda": False,
            "has_rocm": False,
            "has_metal": False,
            "gpu_memory_gb": 0,
            "gpu_devices": []
        }
        
        try:
            # NVIDIA CUDA detection
            try:
                import torch
                if torch.cuda.is_available():
                    gpu_info["has_cuda"] = True
                    gpu_info["gpu_devices"] = [
                        {
                            "name": torch.cuda.get_device_name(i),
                            "memory_gb": round(torch.cuda.get_device_properties(i).total_memory / (1024**3), 2)
                        }
                        for i in range(torch.cuda.device_count())
                    ]
                    gpu_info["gpu_memory_gb"] = sum(device["memory_gb"] for device in gpu_info["gpu_devices"])
            except ImportError:
                # Try nvidia-smi command
                try:
                    result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader,nounits'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        gpu_info["has_cuda"] = True
                        lines = result.stdout.strip().split('\n')
                        for line in lines:
                            if line.strip():
                                name, memory = line.split(', ')
                                gpu_info["gpu_devices"].append({
                                    "name": name.strip(),
                                    "memory_gb": round(int(memory) / 1024, 2)
                                })
                        gpu_info["gpu_memory_gb"] = sum(device["memory_gb"] for device in gpu_info["gpu_devices"])
                except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                    pass
            
            # AMD ROCm detection
            try:
                result = subprocess.run(['rocm-smi', '--showproductname'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    gpu_info["has_rocm"] = True
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                pass
            
            # Apple Metal detection (macOS)
            if platform.system() == "Darwin":
                try:
                    import torch
                    if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                        gpu_info["has_metal"] = True
                except ImportError:
                    pass
            
        except Exception as e:
            self.logger.warning(f"GPU detection failed: {e}")
        
        return gpu_info
    
    def _is_raspberry_pi(self) -> bool:
        """Detect if running on Raspberry Pi."""
        try:
            # Check for Raspberry Pi specific files and hardware
            rpi_indicators = [
                '/proc/device-tree/model',
                '/proc/cpuinfo',
                '/sys/firmware/devicetree/base/model'
            ]
            
            for indicator_file in rpi_indicators:
                try:
                    with open(indicator_file, 'r') as f:
                        content = f.read().lower()
                        if any(keyword in content for keyword in [
                            'raspberry pi', 'bcm2708', 'bcm2709', 'bcm2710', 'bcm2711', 'bcm2835'
                        ]):
                            return True
                except (FileNotFoundError, PermissionError):
                    continue
            
            # Check for Raspberry Pi specific hardware identifiers
            if platform.machine().lower() in ['armv6l', 'armv7l', 'aarch64']:
                # Additional check for Raspberry Pi specific GPIO
                gpio_paths = ['/sys/class/gpio', '/dev/gpiomem']
                if any(Path(path).exists() for path in gpio_paths):
                    return True
            
            return False
            
        except Exception:
            # Fallback to basic ARM detection
            return platform.machine().startswith('arm') or platform.machine().startswith('aarch64')
    
    def _get_raspberry_pi_model(self) -> str:
        """Get the specific Raspberry Pi model."""
        try:
            # Try to read from device tree model file
            model_files = [
                '/proc/device-tree/model',
                '/sys/firmware/devicetree/base/model'
            ]
            
            for model_file in model_files:
                try:
                    with open(model_file, 'r') as f:
                        model = f.read().strip().lower()
                        if 'raspberry pi 5' in model:
                            return 'Pi 5'
                        elif 'raspberry pi 4' in model:
                            return 'Pi 4'
                        elif 'raspberry pi 3' in model:
                            return 'Pi 3'
                        elif 'raspberry pi 2' in model:
                            return 'Pi 2'
                        elif 'raspberry pi' in model:
                            return 'Pi'
                except (FileNotFoundError, PermissionError):
                    continue
            
            # Fallback to cpuinfo parsing
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read().lower()
                if 'bcm2712' in cpuinfo:  # Pi 5
                    return 'Pi 5'
                elif 'bcm2711' in cpuinfo:  # Pi 4
                    return 'Pi 4'
                elif 'bcm2710' in cpuinfo or 'bcm2837' in cpuinfo:  # Pi 3
                    return 'Pi 3'
                elif 'bcm2709' in cpuinfo or 'bcm2836' in cpuinfo:  # Pi 2
                    return 'Pi 2'
                elif 'bcm2708' in cpuinfo or 'bcm2835' in cpuinfo:  # Pi 1/Zero
                    return 'Pi'
            
            return 'Pi (Unknown)'
            
        except Exception:
            return 'Pi (Unknown)'
    
    def assess_capabilities(self) -> Dict[str, any]:
        """Assess system capabilities and recommend configurations."""
        capabilities = {
            "performance_tier": "low",
            "recommended_llm_size": "tiny",
            "max_context_length": 2048,
            "tts_quality": "medium",
            "can_run_local_llm": True,
            "can_run_local_tts": True,
            "recommended_quantization": "q8_0"
        }
        
        memory_gb = self.system_info.get("total_memory_gb", 4)
        cpu_count = self.system_info.get("cpu_count", 2)
        has_gpu = any([
            self.system_info.get("has_cuda", False),
            self.system_info.get("has_rocm", False),
            self.system_info.get("has_metal", False)
        ])
        is_raspberry_pi = self.system_info.get("is_raspberry_pi", False)
        
        # Determine performance tier
        if is_raspberry_pi:
            # Raspberry Pi specific optimizations
            rpi_model = self._get_raspberry_pi_model()
            if rpi_model in ['Pi 5', 'Pi 4']:
                if memory_gb >= 8:
                    capabilities["performance_tier"] = "medium"
                    capabilities["recommended_llm_size"] = "small"
                    capabilities["max_context_length"] = 4096
                    capabilities["recommended_quantization"] = "q4_0"
                    capabilities["tts_quality"] = "medium"
                elif memory_gb >= 4:
                    capabilities["performance_tier"] = "low-medium"
                    capabilities["recommended_llm_size"] = "tiny"
                    capabilities["max_context_length"] = 2048
                    capabilities["recommended_quantization"] = "q4_0"
                    capabilities["tts_quality"] = "medium"
                else:
                    capabilities["performance_tier"] = "low"
                    capabilities["recommended_llm_size"] = "tiny"
                    capabilities["max_context_length"] = 1024
                    capabilities["recommended_quantization"] = "q4_0"
                    capabilities["tts_quality"] = "low"
            else:
                # Older Raspberry Pi models (Pi 3 and earlier)
                capabilities["performance_tier"] = "low"
                capabilities["recommended_llm_size"] = "tiny"
                capabilities["max_context_length"] = 1024
                capabilities["recommended_quantization"] = "q4_0"
                capabilities["tts_quality"] = "low"
                if memory_gb < 2:
                    capabilities["can_run_local_llm"] = False
        else:
            if memory_gb >= 16 and has_gpu:
                capabilities["performance_tier"] = "high"
                capabilities["recommended_llm_size"] = "large"
                capabilities["max_context_length"] = 8192
                capabilities["tts_quality"] = "high"
                capabilities["recommended_quantization"] = "q5_1"
            elif memory_gb >= 8:
                capabilities["performance_tier"] = "medium"
                capabilities["recommended_llm_size"] = "medium"
                capabilities["max_context_length"] = 4096
                capabilities["recommended_quantization"] = "q4_0"
            else:
                capabilities["performance_tier"] = "low"
                capabilities["recommended_llm_size"] = "tiny"
                capabilities["max_context_length"] = 2048
                capabilities["recommended_quantization"] = "q4_0"
        
        # Additional checks
        if memory_gb < 2:
            capabilities["can_run_local_llm"] = False
            capabilities["can_run_local_tts"] = False
        elif memory_gb < 4:
            capabilities["can_run_local_tts"] = False
        
        return capabilities
    
    def get_recommended_models(self) -> Dict[str, Dict[str, str]]:
        """Get recommended model configurations based on system capabilities."""
        tier = self.capabilities["performance_tier"]
        is_rpi = self.system_info.get("is_raspberry_pi", False)
        
        if is_rpi:
            rpi_model = self._get_raspberry_pi_model()
            if rpi_model in ['Pi 5', 'Pi 4'] and self.system_info.get("total_memory_gb", 4) >= 8:
                # High-end Raspberry Pi with sufficient memory
                model_config = {
                    "llm_model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                    "llm_file": "model.gguf",
                    "tts_model": "kokoro-v0_19",
                    "tts_voice": "af_sarah",
                    "context_length": "2048"
                }
            else:
                # Standard Raspberry Pi or lower memory
                model_config = {
                    "llm_model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                    "llm_file": "model.gguf",
                    "tts_model": "kokoro-v0_19",
                    "tts_voice": "af_sarah",
                    "context_length": "1024"
                }
        else:
            # Standard model recommendations for other systems
            model_recommendations = {
                "low": {
                    "llm_model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                    "llm_file": "model.gguf",
                    "tts_model": "kokoro-v0_19",
                    "tts_voice": "af_heart",
                    "context_length": "2048"
                },
                "low-medium": {
                    "llm_model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                    "llm_file": "model.gguf",
                    "tts_model": "kokoro-v0_19",
                    "tts_voice": "af_heart",
                    "context_length": "2048"
                },
                "medium": {
                    "llm_model": "QuantFactory/DarkIdol-Llama-3.1-8B-Instruct-1.2-Uncensored-GGUF",
                    "llm_file": "model.gguf",
                    "tts_model": "kokoro-v0_19",
                    "tts_voice": "af_heart",
                    "context_length": "4096"
                },
                "high": {
                    "llm_model": "TheBloke/Wizard-Vicuna-13B-Uncensored-GGUF",
                    "llm_file": "model.gguf",
                    "tts_model": "kokoro-v0_19",
                    "tts_voice": "af_heart",
                    "context_length": "8192"
                }
            }
            
            model_config = model_recommendations.get(tier, model_recommendations["low"])
        
        return model_config
    
    def get_optimization_flags(self) -> Dict[str, any]:
        """Get optimization flags for model loading."""
        flags = {
            "n_threads": min(self.system_info.get("cpu_count", 2), 8),
            "n_gpu_layers": 0,
            "use_mmap": True,
            "use_mlock": False,
            "low_vram": False
        }
        
        # Raspberry Pi specific optimizations
        if self.system_info.get("is_raspberry_pi", False):
            rpi_model = self._get_raspberry_pi_model()
            if rpi_model in ['Pi 5', 'Pi 4']:
                flags["n_threads"] = min(4, self.system_info.get("cpu_count", 2))
                flags["use_mmap"] = True
                flags["use_mlock"] = False  # Conservative memory usage
                if self.system_info.get("total_memory_gb", 4) < 4:
                    flags["low_vram"] = True
            else:
                # Older Pi models - very conservative
                flags["n_threads"] = min(2, self.system_info.get("cpu_count", 1))
                flags["use_mmap"] = True
                flags["use_mlock"] = False
                flags["low_vram"] = True
        
        # GPU optimizations
        elif self.system_info.get("has_cuda", False):
            gpu_memory = self.system_info.get("gpu_memory_gb", 0)
            if gpu_memory >= 4:
                flags["n_gpu_layers"] = 32
            elif gpu_memory >= 2:
                flags["n_gpu_layers"] = 16
                flags["low_vram"] = True
        
        # General memory optimizations
        elif self.system_info.get("total_memory_gb", 4) < 8:
            flags["use_mlock"] = False
            flags["low_vram"] = True
        else:
            flags["use_mlock"] = True
        
        return flags
    
    def get_system_summary(self) -> str:
        """Get a human-readable system summary."""
        info = self.system_info
        caps = self.capabilities
        
        summary = f"""
System Summary:
- Platform: {info.get('platform', 'Unknown')} ({info.get('architecture', 'Unknown')})
- Memory: {info.get('total_memory_gb', 'Unknown')} GB total
- CPU: {info.get('cpu_count', 'Unknown')} cores
- GPU: {'Yes' if any([info.get('has_cuda'), info.get('has_rocm'), info.get('has_metal')]) else 'No'}
- Performance Tier: {caps['performance_tier'].title()}
- Recommended LLM: {caps['recommended_llm_size'].title()}
- Can run local AI: {'Yes' if caps['can_run_local_llm'] else 'No'}
"""
        
        if info.get("is_raspberry_pi"):
            summary += "- Device: Raspberry Pi detected\n"
        
        return summary.strip()
    
    def save_system_info(self, filepath: str = "system_info.json"):
        """Save system information to a JSON file."""
        try:
            data = {
                "system_info": self.system_info,
                "capabilities": self.capabilities,
                "recommended_models": self.get_recommended_models(),
                "optimization_flags": self.get_optimization_flags()
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"System information saved to {filepath}")
        except Exception as e:
            self.logger.error(f"Failed to save system info: {e}")


def main():
    """CLI interface for system detection."""
    detector = SystemDetector()
    print(detector.get_system_summary())
    print("\nRecommended Models:")
    models = detector.get_recommended_models()
    for key, value in models.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
