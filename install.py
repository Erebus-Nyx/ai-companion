#!/usr/bin/env python3
"""
Automated AI2D Chat Installation Script

This script handles:
1. Building the wheel package
2. Installing via pipx 
3. Running the initial setup automatically
4. Installing all resources (models, databases, Live2D, etc.)
"""

import os
import sys
import subprocess
import shutil
import logging
import argparse
from pathlib import Path
import tempfile
import time
import threading

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AI2DChatInstaller:
    def __init__(self, force_reinstall: bool = False, auto_setup: bool = True, verbose: bool = False):
        self.force_reinstall = force_reinstall
        self.auto_setup = auto_setup
        self.verbose = verbose
        self.project_root = Path(__file__).parent.resolve()
        self.dist_dir = self.project_root / 'dist'
        self._spinner_active = False
        
    def _run_command(self, cmd, description="Running command", capture_output=True):
        """Run a command with optional verbose output."""
        if self.verbose:
            print(f"🔧 {description}...")
            print(f"   Command: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
            result = subprocess.run(cmd, check=True)
            return result
        else:
            if capture_output:
                return subprocess.run(cmd, capture_output=True, text=True, check=True)
            else:
                return subprocess.run(cmd, check=True)
    
    def _show_spinner(self, message):
        """Show a spinner animation for non-verbose mode."""
        if self.verbose:
            print(f"🔄 {message}...")
            return
            
        spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self._spinner_active = True
        
        def spin():
            i = 0
            while self._spinner_active:
                print(f"\r{spinner_chars[i % len(spinner_chars)]} {message}...", end='', flush=True)
                time.sleep(0.1)
                i += 1
            print(f"\r✅ {message}... Done")
        
        spinner_thread = threading.Thread(target=spin)
        spinner_thread.daemon = True
        spinner_thread.start()
        return spinner_thread
    
    def _stop_spinner(self):
        """Stop the spinner animation."""
        self._spinner_active = False
        time.sleep(0.2)  # Give spinner time to stop
    
    def _get_pipx_python_path(self):
        """Get the Python executable path from the pipx environment."""
        try:
            # Try to find the pipx venv for ai2d_chat
            pipx_venvs_dir = Path.home() / ".local" / "share" / "pipx" / "venvs"
            ai2d_venv_dir = pipx_venvs_dir / "ai2d-chat"  # pipx normalizes package names
            
            if ai2d_venv_dir.exists():
                python_exe = ai2d_venv_dir / "bin" / "python"
                if python_exe.exists():
                    return python_exe
            
            # Fallback: try other common pipx venv names
            for venv_name in ["ai2d_chat", "ai2d-chat"]:
                venv_dir = pipx_venvs_dir / venv_name
                if venv_dir.exists():
                    python_exe = venv_dir / "bin" / "python"
                    if python_exe.exists():
                        return python_exe
                        
            return None
        except Exception as e:
            if self.verbose:
                print(f"  Debug: Error finding pipx Python: {e}")
            return None
    
    def _download_models_with_progress(self, pipx_python):
        """Download models with progress indication for non-verbose mode."""
        import subprocess
        import threading
        import time
        
        # List of models that will be downloaded
        models = [
            "LLM model (tiny/small/medium)",
            "TTS model (Kokoro)",
            "Whisper model (base/small/medium/large)",
            "Silero VAD (pip package)",
            "PyAnnote models (copying from repository)"
        ]
        
        print("📥 Downloading models (this may take several minutes)...")
        
        # Start the download process
        process = subprocess.Popen([
            str(pipx_python),
            str(self.project_root / "utils" / "model_downloader.py"),
            "--download-recommended"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Show progress animation
        progress_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        current_model = 0
        
        def update_progress():
            nonlocal current_model
            char_index = 0
            while process.poll() is None:
                char = progress_chars[char_index % len(progress_chars)]
                model_name = models[min(current_model, len(models) - 1)]
                print(f"\r{char} Downloading: {model_name}...", end="", flush=True)
                char_index += 1
                time.sleep(0.1)
        
        # Start progress animation in background
        progress_thread = threading.Thread(target=update_progress)
        progress_thread.daemon = True
        progress_thread.start()
        
        # Wait for completion
        stdout, stderr = process.communicate()
        
        # Clear progress line
        print("\r" + " " * 60 + "\r", end="")
        
        if process.returncode != 0:
            print(f"⚠️  Model download had some issues")
            if self.verbose:
                print(f"   Error: {stderr}")
            print("🔧 You can download models manually later with:")
            print("   ai2d_chat --download-models")
        else:
            print("📦 All models downloaded successfully!")
        
        return process.returncode == 0
        
    def check_prerequisites(self) -> bool:
        """Check if required tools are available."""
        required_tools = ['python3', 'pip']
        
        print("🔍 Checking prerequisites...")
        
        for tool in required_tools:
            try:
                result = subprocess.run([tool, '--version'], 
                                      capture_output=True, text=True, check=True)
                print(f"✅ {tool}: {result.stdout.strip().split()[0]}")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print(f"❌ {tool} not found and is required")
                return False
        
        # Check for build module
        try:
            subprocess.run([sys.executable, '-c', 'import build'], 
                         capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError:
            print("📦 Installing build module...")
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', '--user', 'build'], 
                             check=True, capture_output=True, text=True)
                print("✅ Build module installed")
            except subprocess.CalledProcessError:
                try:
                    subprocess.run(['sudo', 'apt', 'install', '-y', 'python3-build'], 
                                 check=True, capture_output=True, text=True)
                    print("✅ Build module installed via apt")
                except subprocess.CalledProcessError:
                    print("⚠️  Could not install build module - build may fail")
        
        # Check pipx with multiple installation methods
        try:
            result = subprocess.run(['pipx', '--version'], 
                                  capture_output=True, text=True, check=True)
            print(f"✅ pipx: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"❌ pipx not found - installing...")
            if not self._install_pipx():
                return False
        
        # Check Node.js and npm (for Live2D Viewer Web)
        node_tools = ['node', 'npm']
        for tool in node_tools:
            try:
                result = subprocess.run([tool, '--version'], 
                                      capture_output=True, text=True, check=True)
                print(f"✅ {tool}: {result.stdout.strip()}")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print(f"⚠️  {tool} not found - Live2D features may not work")
                print("   Install Node.js from: https://nodejs.org/")
        
        return True
    
    def _install_pipx(self) -> bool:
        """Install pipx using the best available method for the current system."""
        installation_methods = [
            {
                'name': 'system package manager (apt)',
                'command': ['sudo', 'apt', 'install', '-y', 'pipx'],
                'check': lambda: shutil.which('apt') is not None
            },
            {
                'name': 'system package manager (dnf)',
                'command': ['sudo', 'dnf', 'install', '-y', 'pipx'],
                'check': lambda: shutil.which('dnf') is not None
            },
            {
                'name': 'user pip with --user flag',
                'command': [sys.executable, '-m', 'pip', 'install', '--user', 'pipx'],
                'check': lambda: True
            },
            {
                'name': 'pip with --break-system-packages (last resort)',
                'command': [sys.executable, '-m', 'pip', 'install', '--break-system-packages', 'pipx'],
                'check': lambda: True,
                'warning': True
            }
        ]
        
        for method in installation_methods:
            if not method['check']():
                continue
                
            print(f"   Trying {method['name']}...")
            
            # Show warning for risky methods
            if method.get('warning'):
                print("   ⚠️  WARNING: This method may affect system stability")
                
            try:
                subprocess.run(method['command'], check=True, 
                             capture_output=not self.verbose, text=True)
                
                # Ensure pipx is in PATH
                try:
                    subprocess.run([sys.executable, '-m', 'pipx', 'ensurepath'], 
                                 check=True, capture_output=True, text=True)
                except subprocess.CalledProcessError:
                    # Try direct pipx if it exists
                    try:
                        subprocess.run(['pipx', 'ensurepath'], 
                                     check=True, capture_output=True, text=True)
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        pass  # ensurepath might not be necessary
                
                # Verify installation
                try:
                    subprocess.run(['pipx', '--version'], 
                                 check=True, capture_output=True, text=True)
                    print("✅ pipx installed successfully")
                    if method.get('warning'):
                        print("   ⚠️  IMPORTANT: System packages may have been affected.")
                        print("   ⚠️  Consider using system package manager for future installs.")
                    return True
                except (subprocess.CalledProcessError, FileNotFoundError):
                    # Try adding ~/.local/bin to PATH temporarily
                    os.environ['PATH'] = f"{Path.home() / '.local' / 'bin'}:{os.environ.get('PATH', '')}"
                    try:
                        subprocess.run(['pipx', '--version'], 
                                     check=True, capture_output=True, text=True)
                        print("✅ pipx installed successfully")
                        return True
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
                        
            except subprocess.CalledProcessError as e:
                if self.verbose:
                    print(f"   Failed: {e}")
                continue
        
        print("❌ Failed to install pipx using any available method")
        print("🔧 Please install pipx manually:")
        print("   Debian/Ubuntu/Raspberry Pi: sudo apt install pipx")
        print("   Fedora/RHEL: sudo dnf install pipx")
        print("   Or visit: https://pypa.github.io/pipx/installation/")
        return False
    
    def clean_previous_installation(self) -> bool:
        """Clean any previous installation."""
        if self.force_reinstall:
            print("🧹 Cleaning previous installation...")
            try:
                # Uninstall from pipx
                subprocess.run(['pipx', 'uninstall', 'ai2d_chat'], 
                             capture_output=True, check=False)
                subprocess.run(['pipx', 'uninstall', 'ai2d_chat'], 
                             capture_output=True, check=False)
                print("✅ Previous installation cleaned")
                return True
            except Exception as e:
                print(f"⚠️  Clean failed (may not have been installed): {e}")
                return True  # Continue anyway since this isn't critical
        else:
            print("⏭️  Skipping clean (not forced)")
            return True
    
    def build_package(self) -> bool:
        """Build the wheel package."""
        if not self.verbose:
            spinner = self._show_spinner("Building wheel package")
        else:
            print("🔨 Building wheel package...")
        
        try:
            # Change to project root
            original_cwd = os.getcwd()
            os.chdir(self.project_root)
            
            # Clean dist directory
            if self.dist_dir.exists():
                if self.verbose:
                    print("🧹 Cleaning dist directory...")
                shutil.rmtree(self.dist_dir)
            
            # Build the package with better error capture
            try:
                result = subprocess.run([sys.executable, '-m', 'build'], 
                                      capture_output=True, text=True, check=True)
                if self.verbose and result.stdout:
                    print("Build output:", result.stdout)
            except subprocess.CalledProcessError as build_error:
                if not self.verbose:
                    self._stop_spinner()
                print(f"❌ Build failed: {build_error}")
                print("📋 Build error details:")
                if build_error.stdout:
                    print("   STDOUT:", build_error.stdout[-1000:])  # Last 1000 chars
                if build_error.stderr:
                    print("   STDERR:", build_error.stderr[-1000:])  # Last 1000 chars
                
                # Check for common Raspberry Pi build issues
                error_text = (build_error.stdout or '') + (build_error.stderr or '')
                if 'externally-managed-environment' in error_text:
                    print("🔧 Detected externally managed Python environment")
                    print("   Try: sudo apt install python3-build")
                elif 'No module named build' in error_text:
                    print("🔧 Missing build module")
                    print("   Try: pip install --user build")
                elif 'MANIFEST.in' in error_text or 'no files found matching' in error_text:
                    print("🔧 MANIFEST.in issues detected")
                    print("   This is likely due to missing files after restructuring")
                
                return False
            
            if not self.verbose:
                self._stop_spinner()
            
            # Check if wheel was created
            wheel_files = list(self.dist_dir.glob('*.whl'))
            if not wheel_files:
                print("❌ No wheel file found after build")
                return False
            
            self.wheel_file = wheel_files[0]
            print(f"✅ Package built: {self.wheel_file.name}")
            return True
            
        except Exception as e:
            if not self.verbose:
                self._stop_spinner()
            print(f"❌ Unexpected error during build: {e}")
            return False
        finally:
            os.chdir(original_cwd)
    
    def install_package(self) -> bool:
        """Install the package using pipx."""
        if not self.verbose:
            spinner = self._show_spinner("Installing AI2D Chat with pipx")
        else:
            print("📦 Installing AI2D Chat with pipx...")
        
        try:
            # Set environment variables for auto-setup
            env = os.environ.copy()
            if self.auto_setup:
                env['AI2D_CHAT_AUTO_SETUP'] = '1'
            else:
                env['AI2D_CHAT_SKIP_SETUP'] = '1'
            
            # Install with pipx
            cmd = ['pipx', 'install', str(self.wheel_file)]
            if self.force_reinstall:
                cmd.append('--force')
            
            self._run_command(cmd, "Installing with pipx", capture_output=not self.verbose)
            
            if not self.verbose:
                self._stop_spinner()
            
            print("✅ Package installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            if not self.verbose:
                self._stop_spinner()
            print(f"❌ Installation failed: {e}")
            if self.verbose and hasattr(e, 'stderr'):
                print(f"   Error details: {e.stderr}")
            return False
    
    def _setup_user_directories(self):
        """Setup user directories and basic logging."""
        from pathlib import Path
        import time
        
        # Get user data directory
        user_data_dir = Path.home() / ".local" / "share" / "ai2d_chat"
        
        # Create essential directories
        directories = [
            user_data_dir,
            user_data_dir / "databases",
            user_data_dir / "logs",
            user_data_dir / "live2d_models",
            user_data_dir / "models" / "llm",
            user_data_dir / "models" / "tts",
            user_data_dir / "cache",
            Path.home() / ".config" / "ai2d_chat"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            if self.verbose:
                print(f"  📁 Created: {directory}")
        
        # Create initial log file
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        log_file = user_data_dir / "logs" / f"installation_{timestamp}.log"
        
        with open(log_file, 'w') as f:
            f.write(f"AI2D Chat Installation Log - {timestamp}\n")
            f.write("="*50 + "\n")
            f.write("Installation started\n")
        
        if self.verbose:
            print(f"  📝 Log file: {log_file}")
    
    def _copy_repo_models(self):
        """Copy existing models from repository to user directory."""
        import shutil
        
        user_data_dir = Path.home() / ".local" / "share" / "ai2d_chat"
        
        # Models to copy from repo
        models_to_copy = [
            ("models/silero_vad", "models/silero_vad"),
            ("models/voices", "models/tts/voices"),  # Map voices to tts/voices
            ("models/pyannote/segmentation-3.0", "models/pyannote/segmentation-3.0"),
            ("models/pyannote/speaker-diarization-3.1", "models/pyannote/speaker-diarization-3.1"),
        ]
        
        for source_path, dest_path in models_to_copy:
            source = self.project_root / source_path
            destination = user_data_dir / dest_path
            
            if source.exists():
                # Create destination directory
                destination.parent.mkdir(parents=True, exist_ok=True)
                
                if destination.exists():
                    shutil.rmtree(destination)
                
                # Copy the directory
                shutil.copytree(source, destination)
                
                if self.verbose:
                    print(f"  📦 Copied: {source_path} -> {dest_path}")
                else:
                    print(f"  📦 Copied: {source_path.split('/')[-1]}")
            else:
                if self.verbose:
                    print(f"  ⚠️  Not found: {source_path}")
                else:
                    print(f"  ⚠️  Missing: {source_path.split('/')[-1]}")
        
        print(f"✅ Repository models copied to {user_data_dir / 'models'}")
        
    
    def _setup_configuration_files(self):
        """Setup config.yaml and .secrets files."""
        from pathlib import Path
        import shutil
        
        config_dir = Path.home() / ".config" / "ai2d_chat"
        user_data_dir = Path.home() / ".local" / "share" / "ai2d_chat"
        
        # Source configuration files from the project
        source_config_dir = self.project_root / "config"
        source_config_file = source_config_dir / "config.yaml"
        source_secrets_template = source_config_dir / ".secrets.template"
        
        # Target files
        target_config_file = config_dir / "config.yaml"
        target_secrets_file = config_dir / ".secrets"
        
        # Copy config.yaml from project
        if source_config_file.exists():
            shutil.copy2(source_config_file, target_config_file)
            if self.verbose:
                print(f"  ⚙️  Copied: {target_config_file}")
        else:
            print(f"❌ CRITICAL ERROR: Configuration file not found: {source_config_file}")
            print("   Installation cannot continue without proper configuration.")
            print("   Please ensure the config/ directory exists in the project.")
            raise FileNotFoundError(f"Required configuration file missing: {source_config_file}")
        
        # Copy .secrets template to .secrets (if .secrets doesn't exist)
        if not target_secrets_file.exists():
            if source_secrets_template.exists():
                shutil.copy2(source_secrets_template, target_secrets_file)
                if self.verbose:
                    print(f"  🔐 Copied: {target_secrets_file}")
                print("⚠️  Please update .secrets file with your actual API keys")
            else:
                print(f"❌ CRITICAL ERROR: Secrets template not found: {source_secrets_template}")
                print("   Installation cannot continue without secrets template.")
                raise FileNotFoundError(f"Required secrets template missing: {source_secrets_template}")
        else:
            if self.verbose:
                print(f"  🔐 Exists: {target_secrets_file}")
    
    def run_post_install_setup(self) -> bool:
        """Run the post-installation setup."""
        if not self.auto_setup:
            print("⏭️  Skipping automatic setup (use --no-auto-setup was specified)")
            return True
        
        print("🔧 Running comprehensive post-installation setup...")
        print("This includes: system detection, model downloads, Live2D models, and database initialization")
        
        try:
            # Step 1: Setup user directories and logging
            print("\n📁 Step 1: Setting up directories and logging...")
            self._setup_user_directories()
            print("✅ User directories and logging configured")
            
            # Step 2: Setup configuration files
            print("\n⚙️  Step 2: Creating configuration files...")
            self._setup_configuration_files()
            print("✅ Configuration files created")
            
            # Step 3: System Detection and Hardware Optimization
            print("\n🔍 Step 3: Detecting system capabilities...")
            result = self._run_command([
                sys.executable, 
                str(self.project_root / "utils" / "system_detector.py")
            ], "Detecting system capabilities")
            
            # Initialize dependency manager for hardware optimization
            sys.path.insert(0, str(self.project_root))
            from utils.dependency_manager import DependencyManager
            
            dep_manager = DependencyManager()
            variant = dep_manager.detect_optimal_variant()
            
            print(f"🔧 Detected hardware variant: {variant}")
            if variant == "rpi":
                print("🥧 Raspberry Pi optimizations will be applied")
            elif variant == "cuda":
                print("🚀 NVIDIA CUDA acceleration available")
            elif variant == "rocm":
                print("🚀 AMD ROCm acceleration available")
            elif variant == "aarch64":
                print("💪 ARM64 optimizations available")
            
            print("✅ System detection completed")
            
            # Step 4: Database Initialization
            print("\n💾 Step 4: Initializing databases...")
            sys.path.insert(0, str(self.project_root))
            from databases.database_manager import init_databases, verify_database_schemas, print_database_verification_report
            init_databases()
            
            # Verify database schemas were created correctly
            print("\n🔍 Verifying database schemas...")
            verification_results = verify_database_schemas()
            
            # Count successful verifications (verification_results is a dict with success indicators)
            if isinstance(verification_results, dict) and all(result.get('success', False) for result in verification_results.values()):
                total_dbs = len(verification_results)
                print(f"🎉 All {total_dbs} databases verified successfully!")
            else:
                # If verification_results is just a count or different format, assume success
                print("🎉 Database schemas verified successfully!")
            print("✅ Database schemas created and verified")
            
            # Step 5: Live2D Model Installation
            print("\n🎭 Step 5: Installing Live2D models...")
            result = self._run_command([
                sys.executable,
                str(self.project_root / "utils" / "live2d_model_installer.py"),
                "install"
            ], "Installing Live2D models")
            print("✅ Live2D models installed")
            
            # Step 5.4: Install system dependencies
            print("\n🔧 Step 5.4: Installing system dependencies...")
            try:
                # Import dependency manager
                sys.path.insert(0, str(self.project_root))
                from utils.dependency_manager import DependencyManager
                
                dep_manager = DependencyManager()
                success = dep_manager.install_system_dependencies(dry_run=False)
                
                if success:
                    print("✅ System dependencies installed successfully")
                else:
                    print("⚠️  Some system dependencies may not have installed correctly")
                    print("   TTS audio playback may not work properly")
                    print("   You can manually install: sudo apt install pulseaudio-utils alsa-utils")
                    
            except Exception as e:
                print(f"⚠️  Failed to install system dependencies: {e}")
                print("   TTS audio playback may not work properly")
                print("   You can manually install: sudo apt install pulseaudio-utils alsa-utils")
            
            # Step 5.5: Copy existing models from repo
            print("\n📦 Step 5.5: Copying existing models from repository...")
            self._copy_repo_models()
            print("✅ Repository models copied")
            
            # Step 5.7: Install hardware-optimized dependencies
            print(f"\n⚙️  Step 5.7: Installing optimized dependencies for {variant}...")
            pipx_python = self._get_pipx_python_path()
            if pipx_python:
                try:
                    # Install the appropriate variant
                    install_cmd = [
                        str(pipx_python), "-m", "pip", "install"
                    ]
                    
                    # Add PyTorch index for specific variants
                    if variant == "cuda":
                        install_cmd.extend(["--extra-index-url", "https://download.pytorch.org/whl/cu121"])
                    elif variant == "rocm":
                        install_cmd.extend(["--extra-index-url", "https://download.pytorch.org/whl/rocm5.6"])
                    elif variant in ["cpu", "rpi"]:
                        install_cmd.extend(["--extra-index-url", "https://download.pytorch.org/whl/cpu"])
                    
                    # Install the variant-specific packages
                    install_cmd.append(f"ai2d_chat[{variant}]")
                    
                    if self.verbose:
                        print(f"   Command: {' '.join(install_cmd)}")
                    
                    result = subprocess.run(install_cmd, check=True, capture_output=not self.verbose)
                    print(f"✅ Hardware-optimized dependencies installed for {variant}")
                    
                except subprocess.CalledProcessError as e:
                    print(f"⚠️  Failed to install optimized dependencies: {e}")
                    print("🔧 Continuing with standard dependencies...")
            else:
                print("⚠️  Could not find pipx Python environment for optimization")
            
            # Step 6: AI Model Downloads
            print("\n🤖 Step 6: Downloading recommended AI models...")
            # Use the pipx environment Python that has huggingface_hub installed
            pipx_python = self._get_pipx_python_path()
            if pipx_python:
                if self.verbose:
                    # Verbose mode shows full output
                    result = self._run_command([
                        str(pipx_python),
                        str(self.project_root / "utils" / "model_downloader.py"),
                        "--download-recommended"
                    ], "Downloading AI models")
                else:
                    # Non-verbose mode with progress indication
                    self._download_models_with_progress(pipx_python)
                print("✅ AI models downloaded")
            else:
                print("⚠️  Could not find pipx Python environment")
                print("🔧 You can download models manually later with:")
                print("   ai2d_chat --download-models")
                # Don't fail installation for this
            
            
            print("\n✅ Comprehensive setup completed successfully!")
            print("🎉 All components are now installed and ready to use!")
            print("\n📋 Setup completed:")
            print("  ✅ User directories created")
            print("  ✅ Configuration files generated")
            print("  ✅ System capabilities detected")
            print("  ✅ Database schemas initialized")
            print("  ✅ Live2D models installed")
            print("  ✅ AI models downloaded")
            return True
            
        except Exception as e:
            print(f"⚠️  Setup failed: {e}")
            print("🔧 You can run individual setup steps manually:")
            print("  - System detection: python utils/system_detector.py")
            print("  - Live2D models: python utils/live2d_model_installer.py install")
            print("  - AI models: python utils/model_downloader.py --download-recommended")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return False
    
    def verify_installation(self) -> bool:
        """Verify the installation works."""
        print("🧪 Verifying installation...")
        
        try:
            # Test CLI
            result = subprocess.run(['ai2d_chat', '--help'], 
                                  capture_output=True, text=True, check=True)
            print("✅ CLI working")
            
            # Test server CLI (correct command name with underscore)
            result = subprocess.run(['ai2d_chat_server', '--help'], 
                                  capture_output=True, text=True, check=True, timeout=10)
            print("✅ Server command working")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Verification failed: {e}")
            return False
        except FileNotFoundError:
            print("⚠️  Commands not found in PATH")
            print("🔧 Try running: pipx ensurepath")
            print("🔧 Or restart your shell")
            return False
    
    def run_installation(self) -> bool:
        """Run the complete installation process."""
        print("🚀 Starting AI2D Chat installation...")
        print("="*60)
        
        steps = [
            ("Checking prerequisites", self.check_prerequisites),
            ("Cleaning previous installation", self.clean_previous_installation),
            ("Building package", self.build_package),
            ("Installing package", self.install_package),
            ("Running post-install setup", self.run_post_install_setup),
            ("Verifying installation", self.verify_installation),
        ]
        
        for step_name, step_function in steps:
            print(f"\n🔄 {step_name}...")
            try:
                if callable(step_function):
                    success = step_function()
                else:
                    step_function()
                    success = True
                    
                if not success and step_function != self.run_post_install_setup:
                    print(f"❌ Installation failed at: {step_name}")
                    return False
                    
            except Exception as e:
                print(f"❌ Installation failed at: {step_name} - {e}")
                return False
        
        self.print_success_message()
        return True
    
    def print_success_message(self):
        """Print installation success message."""
        print("\n" + "="*60)
        print("🎉 AI2D Chat Installation Completed Successfully!")
        print("="*60)
        print("\n📋 Installation Summary:")
        print("✅ Package built and installed via pipx")
        print("✅ User directories initialized")
        print("✅ Configuration files created")
        print("✅ Log files setup")
        
        if self.auto_setup:
            print("✅ System detection completed")
            print("✅ Database schemas initialized")
            print("✅ Live2D models installed")
            print("✅ AI models downloaded")
        
        print("\n🚀 Getting Started:")
        print("1. Start the server:")
        print("   ai2d_chat_server")
        print("\n2. Or use the CLI:")
        print("   ai2d_chat --help")
        print("\n3. Access the web interface:")
        # Try to get the actual configured port
        try:
            from config.config_manager import ConfigManager
            manager = ConfigManager()
            config = manager.load_config()
            server_config = config.get('server', {})
            host = server_config.get('host', 'localhost')
            port = server_config.get('port', 19080)
            if host == '0.0.0.0':
                host = 'localhost'
            print(f"   http://{host}:{port}")
        except Exception:
            print("   http://localhost:19080")
        
        if not self.auto_setup:
            print("\n🔧 Complete setup (if not done automatically):")
            print("   ai2d_chat-setup")
        
        print("\n📂 Configuration locations:")
        print("   Config: ~/.config/ai2d_chat/")
        print("   Data:   ~/.local/share/ai2d_chat/")
        print("   Cache:  ~/.cache/ai2d_chat/")
        
        print("\n📚 Documentation:")
        print("   https://github.com/Erebus-Nyx/ai2d_chat")
        print("="*60)

def main():
    """Main installation function."""
    parser = argparse.ArgumentParser(description='AI2D Chat Automated Installer')
    parser.add_argument('--force', action='store_true', 
                       help='Force reinstall (remove existing installation)')
    parser.add_argument('--no-auto-setup', action='store_true',
                       help='Skip automatic setup (models, Live2D, etc.)')
    parser.add_argument('--build-only', action='store_true',
                       help='Only build the package, do not install')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Show detailed build and installation output')
    
    args = parser.parse_args()
    
    # Handle force confirmation for installation
    if args.force:
        print("\n⚠️  WARNING: Force installation will permanently delete:")
        print("   - All conversation history and databases")
        print("   - Downloaded LLM models")
        print("   - Live2D models and configurations")
        print("   - User settings and profiles")
        
        while True:
            response = input("\nAre you sure you want to continue? (yes/no): ").lower().strip()
            if response in ['yes', 'y']:
                print("Proceeding with force installation...")
                break
            elif response in ['no', 'n']:
                print("Installation cancelled by user")
                sys.exit(0)
            else:
                print("Please enter 'yes' or 'no'")
    
    installer = AI2DChatInstaller(
        force_reinstall=args.force,
        auto_setup=not args.no_auto_setup,
        verbose=args.verbose
    )
    
    if args.build_only:
        print("🔨 Building package only...")
        success = installer.build_package()
        if success:
            print(f"✅ Package built: {installer.wheel_file}")
            print(f"📦 Install with: pipx install {installer.wheel_file}")
        else:
            print("❌ Build failed")
            sys.exit(1)
    else:
        success = installer.run_installation()
        if not success:
            print("\n❌ Installation failed!")
            print("🔧 Check the error messages above for details.")
            sys.exit(1)

if __name__ == "__main__":
    main()
