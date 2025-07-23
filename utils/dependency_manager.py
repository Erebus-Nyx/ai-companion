"""
Dependency manager for AI2D Chat application.
Handles architecture-specific package installation and optimization.
"""

import platform
import subprocess
import logging
import os
import sys
from typing import List, Dict, Optional, Tuple
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.system_detector import SystemDetector


class DependencyManager:
    """
    Manages architecture-specific dependencies and optimizations.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.system_detector = SystemDetector()
        self.system_info = self.system_detector.get_system_info()
        
        # Package index URLs for different architectures
        self.package_indices = {
            "cuda": "https://download.pytorch.org/whl/cu121",
            "rocm": "https://download.pytorch.org/whl/rocm5.6", 
            "cpu": "https://download.pytorch.org/whl/cpu",
            "default": None
        }
    
    def detect_optimal_variant(self) -> str:
        """Detect the optimal package variant for current system."""
        system_info = self.system_info
        
        # Raspberry Pi detection
        if system_info.get("is_raspberry_pi", False):
            return "rpi"
        
        # ARM64/AArch64 detection (including Apple Silicon)
        if platform.machine().lower() in ['arm64', 'aarch64']:
            return "aarch64"
        
        # GPU detection
        if system_info.get("has_cuda", False):
            return "cuda"
        elif system_info.get("has_rocm", False):
            return "rocm"
        else:
            return "cpu"
    
    def get_optimized_requirements(self, variant: Optional[str] = None) -> List[str]:
        """Get optimized package requirements for a specific variant."""
        if variant is None:
            variant = self.detect_optimal_variant()
        
        requirements = []
        
        # Base requirements that apply to all variants
        base_requirements = [
            "flask>=2.3.0",
            "flask-socketio>=5.3.0", 
            "numpy>=1.21.0",
            "scipy>=1.10.0",
            "requests>=2.31.0",
            "pyyaml>=6.0",
            "psutil>=5.9.0",
            "sqlalchemy>=2.0.0",
        ]
        requirements.extend(base_requirements)
        
        # Variant-specific requirements with proper PyTorch versions
        if variant == "cuda":
            requirements.extend([
                "torch>=2.0.0",  # Will use CUDA index
                "torchaudio>=2.0.0",
                "llama-cpp-python>=0.2.0",
                "onnxruntime-gpu>=1.15.0",
            ])
        elif variant == "rocm":
            requirements.extend([
                "torch>=2.0.0",  # Will use ROCm index
                "torchaudio>=2.0.0",
                "llama-cpp-python>=0.2.0",
                "onnxruntime>=1.15.0",
            ])
        elif variant == "aarch64":
            requirements.extend([
                "torch>=2.0.0",
                "torchaudio>=2.0.0", 
                "llama-cpp-python>=0.2.0",
                "onnxruntime>=1.15.0",
                "pillow>=10.0.0",
            ])
        elif variant == "rpi":
            requirements.extend([
                "torch>=2.0.0",  # Will use CPU index
                "torchaudio>=2.0.0",
                "llama-cpp-python>=0.2.0",
                "onnxruntime>=1.15.0",
                "pillow>=10.0.0",
                "sounddevice>=0.4.6",
                "gpiozero>=1.6.0",
            ])
            # Add RPi.GPIO only on appropriate platforms
            if platform.machine().lower() in ['armv7l', 'aarch64']:
                requirements.append("RPi.GPIO>=0.7.1")
        else:  # cpu variant
            requirements.extend([
                "torch>=2.0.0",  # Will use CPU index
                "torchaudio>=2.0.0",
                "llama-cpp-python>=0.2.0",
                "onnxruntime>=1.15.0",
            ])
        
        return requirements
    
    def get_installation_command(self, variant: Optional[str] = None) -> List[str]:
        """Get the pip installation command with appropriate indices."""
        if variant is None:
            variant = self.detect_optimal_variant()
        
        cmd = [sys.executable, "-m", "pip", "install"]
        
        # Add package index for PyTorch variants
        if variant in self.package_indices and self.package_indices[variant]:
            cmd.extend(["--extra-index-url", self.package_indices[variant]])
        
        return cmd
    
    def install_optimized_dependencies(self, variant: Optional[str] = None, 
                                     dry_run: bool = False) -> bool:
        """Install optimized dependencies for the detected or specified variant."""
        if variant is None:
            variant = self.detect_optimal_variant()
        
        self.logger.info(f"Installing dependencies for variant: {variant}")
        
        try:
            # Get installation command
            cmd = self.get_installation_command(variant)
            
            # Add package name with variant
            cmd.append(f"ai2d_chat[{variant}]")
            
            if dry_run:
                self.logger.info(f"Dry run - would execute: {' '.join(cmd)}")
                print(f"Dry run - would execute: {' '.join(cmd)}")
                return True
            
            # Execute installation
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            self.logger.info("✅ Optimized dependencies installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"❌ Failed to install optimized dependencies: {e}")
            self.logger.error(f"Error output: {e.stderr}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Unexpected error during installation: {e}")
            return False
    
    def get_system_optimization_summary(self) -> Dict[str, any]:
        """Get a summary of system capabilities and recommended optimizations."""
        variant = self.detect_optimal_variant()
        
        summary = {
            "detected_variant": variant,
            "system_info": self.system_info,
            "recommended_packages": self.get_optimized_requirements(variant),
            "installation_command": self.get_installation_command(variant),
            "performance_notes": self._get_performance_notes(variant)
        }
        
        return summary
    
    def _get_performance_notes(self, variant: str) -> List[str]:
        """Get performance optimization notes for a specific variant."""
        notes = []
        
        if variant == "cuda":
            notes.extend([
                "CUDA acceleration enabled for optimal GPU performance",
                "Consider increasing GPU memory allocation for larger models",
                "Monitor GPU temperature during intensive operations"
            ])
        elif variant == "rocm":
            notes.extend([
                "ROCm acceleration enabled for AMD GPU performance",
                "Ensure ROCm drivers are properly installed",
                "Some operations may fall back to CPU if ROCm support is incomplete"
            ])
        elif variant == "rpi":
            notes.extend([
                "Raspberry Pi optimizations enabled",
                "Consider using swap file for larger models",
                "Monitor CPU temperature and consider cooling solutions",
                "Use smaller model variants to fit within memory constraints",
                "GPIO access available for hardware integrations"
            ])
        elif variant == "aarch64":
            notes.extend([
                "ARM64 optimizations enabled",
                "Metal acceleration available on Apple Silicon",
                "Consider using unified memory efficiently"
            ])
        else:  # cpu
            notes.extend([
                "CPU-only mode - no GPU acceleration",
                "Consider upgrading to GPU-accelerated hardware for better performance",
                "Use smaller models to improve response times"
            ])
        
        return notes
    
    def validate_installation(self) -> Tuple[bool, List[str]]:
        """Validate that key dependencies are properly installed."""
        issues = []
        
        # Check Python packages
        required_packages = ["torch", "numpy", "flask", "transformers"]
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                issues.append(f"Missing Python package: {package}")
        
        # Check system capabilities
        if not self.system_info.get("python_version_ok", True):
            issues.append("Python version may be incompatible")
        
        return len(issues) == 0, issues
    
    def install_system_dependencies(self, dry_run: bool = False) -> bool:
        """Install system-level dependencies required for audio and other features."""
        try:
            system = platform.system().lower()
            
            if system == "linux":
                return self._install_linux_system_deps(dry_run)
            elif system == "darwin":  # macOS
                return self._install_macos_system_deps(dry_run)
            elif system == "windows":
                return self._install_windows_system_deps(dry_run)
            else:
                self.logger.warning(f"System dependency installation not supported for {system}")
                return True  # Don't fail installation
                
        except Exception as e:
            self.logger.error(f"Failed to install system dependencies: {e}")
            return False
    
    def _install_linux_system_deps(self, dry_run: bool = False) -> bool:
        """Install Linux system dependencies."""
        # Core audio dependencies
        packages = [
            "pulseaudio-utils",    # For paplay (PulseAudio)
            "alsa-utils",          # For aplay (ALSA)
            "ffmpeg",              # For audio format conversion
            "portaudio19-dev",     # For PyAudio compilation
            "libsndfile1",         # For soundfile library
            "libasound2-dev",      # For ALSA development
        ]
        
        # Additional packages for different distros
        try:
            # Try to detect package manager
            if subprocess.run(["which", "apt"], capture_output=True).returncode == 0:
                return self._install_apt_packages(packages, dry_run)
            elif subprocess.run(["which", "dnf"], capture_output=True).returncode == 0:
                return self._install_dnf_packages(packages, dry_run)
            elif subprocess.run(["which", "yum"], capture_output=True).returncode == 0:
                return self._install_yum_packages(packages, dry_run)
            elif subprocess.run(["which", "pacman"], capture_output=True).returncode == 0:
                return self._install_pacman_packages(packages, dry_run)
            else:
                self.logger.warning("No supported package manager found")
                return True  # Don't fail installation
                
        except Exception as e:
            self.logger.error(f"Error installing Linux system dependencies: {e}")
            return False
    
    def _install_apt_packages(self, packages: List[str], dry_run: bool = False) -> bool:
        """Install packages using apt (Debian/Ubuntu)."""
        try:
            if dry_run:
                self.logger.info(f"Would install apt packages: {', '.join(packages)}")
                return True
            
            # Update package list
            subprocess.run(["sudo", "apt", "update"], check=True, capture_output=True)
            
            # Install packages
            cmd = ["sudo", "apt", "install", "-y"] + packages
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            self.logger.info(f"Successfully installed apt packages: {', '.join(packages)}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to install apt packages: {e}")
            if e.stderr:
                self.logger.error(f"Error details: {e.stderr}")
            return False
    
    def _install_dnf_packages(self, packages: List[str], dry_run: bool = False) -> bool:
        """Install packages using dnf (Fedora/RHEL)."""
        # Map some package names for dnf
        dnf_packages = []
        for pkg in packages:
            if pkg == "pulseaudio-utils":
                dnf_packages.append("pulseaudio-utils")
            elif pkg == "alsa-utils":
                dnf_packages.append("alsa-utils")
            elif pkg == "portaudio19-dev":
                dnf_packages.append("portaudio-devel")
            elif pkg == "libsndfile1":
                dnf_packages.append("libsndfile")
            elif pkg == "libasound2-dev":
                dnf_packages.append("alsa-lib-devel")
            else:
                dnf_packages.append(pkg)
        
        try:
            if dry_run:
                self.logger.info(f"Would install dnf packages: {', '.join(dnf_packages)}")
                return True
            
            cmd = ["sudo", "dnf", "install", "-y"] + dnf_packages
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            self.logger.info(f"Successfully installed dnf packages: {', '.join(dnf_packages)}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to install dnf packages: {e}")
            return False
    
    def _install_yum_packages(self, packages: List[str], dry_run: bool = False) -> bool:
        """Install packages using yum (older RHEL/CentOS)."""
        # Similar to dnf but using yum
        yum_packages = []
        for pkg in packages:
            if pkg == "portaudio19-dev":
                yum_packages.append("portaudio-devel")
            elif pkg == "libsndfile1":
                yum_packages.append("libsndfile")
            elif pkg == "libasound2-dev":
                yum_packages.append("alsa-lib-devel")
            else:
                yum_packages.append(pkg)
        
        try:
            if dry_run:
                self.logger.info(f"Would install yum packages: {', '.join(yum_packages)}")
                return True
            
            cmd = ["sudo", "yum", "install", "-y"] + yum_packages
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            self.logger.info(f"Successfully installed yum packages: {', '.join(yum_packages)}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to install yum packages: {e}")
            return False
    
    def _install_pacman_packages(self, packages: List[str], dry_run: bool = False) -> bool:
        """Install packages using pacman (Arch Linux)."""
        # Map package names for pacman
        pacman_packages = []
        for pkg in packages:
            if pkg == "pulseaudio-utils":
                pacman_packages.append("pulseaudio")
            elif pkg == "alsa-utils":
                pacman_packages.append("alsa-utils")
            elif pkg == "portaudio19-dev":
                pacman_packages.append("portaudio")
            elif pkg == "libsndfile1":
                pacman_packages.append("libsndfile")
            elif pkg == "libasound2-dev":
                pacman_packages.append("alsa-lib")
            else:
                pacman_packages.append(pkg)
        
        try:
            if dry_run:
                self.logger.info(f"Would install pacman packages: {', '.join(pacman_packages)}")
                return True
            
            cmd = ["sudo", "pacman", "-S", "--noconfirm"] + pacman_packages
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            self.logger.info(f"Successfully installed pacman packages: {', '.join(pacman_packages)}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to install pacman packages: {e}")
            return False
    
    def _install_macos_system_deps(self, dry_run: bool = False) -> bool:
        """Install macOS system dependencies using brew."""
        packages = [
            "portaudio",
            "ffmpeg",
            "libsndfile"
        ]
        
        try:
            # Check if brew is available
            if subprocess.run(["which", "brew"], capture_output=True).returncode != 0:
                self.logger.warning("Homebrew not found. Please install: https://brew.sh/")
                return True  # Don't fail installation
            
            if dry_run:
                self.logger.info(f"Would install brew packages: {', '.join(packages)}")
                return True
            
            cmd = ["brew", "install"] + packages
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            self.logger.info(f"Successfully installed brew packages: {', '.join(packages)}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to install brew packages: {e}")
            return False
    
    def _install_windows_system_deps(self, dry_run: bool = False) -> bool:
        """Install Windows system dependencies."""
        # On Windows, audio utilities are typically built-in or handled by Python packages
        self.logger.info("Windows audio dependencies are typically handled by Python packages")
        return True


def main():
    """CLI interface for dependency management."""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI2D Chat Dependency Manager')
    parser.add_argument('--detect', action='store_true', 
                       help='Detect optimal variant for current system')
    parser.add_argument('--install', type=str, nargs='?', const='auto',
                       help='Install dependencies for specified variant (auto-detect if not specified)')
    parser.add_argument('--install-system', action='store_true',
                       help='Install system-level dependencies (audio, etc.)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be installed without actually installing')
    parser.add_argument('--validate', action='store_true',
                       help='Validate current installation')
    parser.add_argument('--summary', action='store_true',
                       help='Show system optimization summary')
    
    args = parser.parse_args()
    
    dm = DependencyManager()
    
    if args.detect:
        variant = dm.detect_optimal_variant()
        print(f"Detected optimal variant: {variant}")
    
    if args.install_system:
        success = dm.install_system_dependencies(dry_run=args.dry_run)
        if success:
            print("✅ System dependencies installed successfully")
        else:
            print("❌ Failed to install system dependencies")
            sys.exit(1)
    
    if args.install:
        variant = None if args.install == 'auto' else args.install
        success = dm.install_optimized_dependencies(variant, dry_run=args.dry_run)
        if success:
            print("✅ Dependencies installed successfully")
        else:
            print("❌ Failed to install dependencies")
            sys.exit(1)
    
    if args.validate:
        valid, issues = dm.validate_installation()
        if valid:
            print("✅ Installation validation passed")
        else:
            print("❌ Installation validation failed:")
            for issue in issues:
                print(f"  - {issue}")
    
    if args.summary:
        summary = dm.get_system_optimization_summary()
        print("System Optimization Summary:")
        print(f"  Detected variant: {summary['detected_variant']}")
        print(f"  Platform: {summary['system_info'].get('platform', 'Unknown')}")
        print(f"  Architecture: {summary['system_info'].get('architecture', 'Unknown')}")
        print(f"  Memory: {summary['system_info'].get('total_memory_gb', 'Unknown')} GB")
        print(f"  GPU: {'Yes' if any([summary['system_info'].get('has_cuda'), summary['system_info'].get('has_rocm'), summary['system_info'].get('has_metal')]) else 'No'}")
        print("\nPerformance Notes:")
        for note in summary['performance_notes']:
            print(f"  - {note}")


if __name__ == "__main__":
    main()
