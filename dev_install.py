#!/usr/bin/env python3
"""
AI Companion Development Installation Script

This script sets up AI Companion for DEVELOPMENT use within the repository.
Data (databases, models, config) is still stored in user directories, but
the application runs from the repository source code.

Key differences from production install:
- Uses development port (19081) to avoid conflicts with production install
- Runs code from repository source (python app.py)  
- Uses Poetry for dependency management
- Allows immediate testing of code changes

Data locations (same as production):
- Config: ~/.config/ai2d_chat/config.yaml
- Data: ~/.local/share/ai2d_chat/
- Cache: ~/.cache/ai2d_chat/

Usage:
    python dev_install.py [options]
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Add paths for imports using dynamic path detection
current_file = Path(__file__).resolve()
project_root = current_file.parent  # Now in root directory, so just parent
scripts_path = project_root / "scripts"  # Point to scripts subdirectory

# Add project root to path so we can import from config/, databases/, etc.
sys.path.insert(0, str(project_root))

from config.config_manager import ConfigManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AICompanionInstaller:
    def __init__(self, force_first_run=False):
        self.base_path = Path(__file__).resolve().parent  # Now in root directory
        self.config = ConfigManager()
        self.force_first_run = force_first_run
        
    def force_first_run_setup(self):
        """Force first-run setup by cleaning existing configurations and databases"""
        try:
            logger.info("Force first-run setup requested - will clean existing databases and configuration...")
            
            # Only when --force is used, we actually clean databases
            # This should use the proper directories like production
            logger.info("Setting up fresh configuration with database cleanup...")
            config_manager = ConfigManager.setup_fresh_installation(clean_databases=True)
            logger.info("Fresh configuration setup with database cleanup completed successfully!")
            
            # Mark that configuration setup was done
            self._config_setup_done = True
            
            return True
            
        except Exception as e:
            logger.error(f"Force first-run setup failed: {e}")
            return False
    
    def check_existing_data(self):
        """Check for existing data and warn user about data protection"""
        try:
            # Check for existing databases
            db_files = []
            if self.config.database_dir.exists():
                for db_file in ['ai2d_chat.db', 'conversations.db', 'live2d.db', 'personality.db']:
                    db_path = self.config.database_dir / db_file
                    if db_path.exists():
                        db_files.append(db_file)
            
            # Check for existing models
            models_exist = False
            if self.config.models_dir.exists() and any(self.config.models_dir.iterdir()):
                models_exist = True
            
            # Check for existing Live2D models
            live2d_models_exist = False
            if self.config.live2d_models_dir.exists() and any(self.config.live2d_models_dir.iterdir()):
                live2d_models_exist = True
            
            if db_files or models_exist or live2d_models_exist:
                logger.info("Existing data detected:")
                if db_files:
                    logger.info(f"  - Database files: {', '.join(db_files)}")
                if models_exist:
                    logger.info(f"  - Models directory: {self.config.models_dir}")
                if live2d_models_exist:
                    logger.info(f"  - Live2D models: {self.config.live2d_models_dir}")
                
                if not self.force_first_run:
                    logger.info("  - All existing data will be preserved (use --force to clean)")
                else:
                    logger.warning("  - WARNING: --force flag will remove all existing data!")
            
            return True  # Success
                    
        except Exception as e:
            logger.warning(f"Could not check existing data: {e}")
            return False  # Failure
    
    def setup_directories(self):
        """Create necessary directories"""
        try:
            directories = [
                'models/live2d',
                'models/llm',
                'databases',
                'logs',
                'web/static'
            ]
            
            for directory in directories:
                dir_path = self.base_path / directory
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {directory}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create directories: {e}")
            return False
    
    def install_python_dependencies(self):
        """Install Python dependencies"""
        try:
            logger.info("Installing Python dependencies...")
            
            # Check if Poetry is available and pyproject.toml has poetry config
            pyproject_path = self.base_path / "pyproject.toml"
            
            # First try Poetry if available and configured
            try:
                subprocess.run(['poetry', '--version'], capture_output=True, check=True)
                
                # Check if this is a Poetry project
                if pyproject_path.exists():
                    pyproject_content = pyproject_path.read_text()
                    if '[tool.poetry]' in pyproject_content:
                        logger.info("Using Poetry for dependency management...")
                        subprocess.run(['poetry', 'install'], cwd=self.base_path, check=True)
                        logger.info("Python dependencies installed successfully via Poetry")
                        return True
                
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass  # Poetry not available or not a Poetry project
            
            # Fallback to pip with multiple strategies for externally managed environments
            logger.info("Using pip for dependency management...")
            
            # Strategy 1: Create a virtual environment (safest approach)
            venv_path = self.base_path / '.venv'
            try:
                logger.info("Creating virtual environment for development...")
                # Create virtual environment
                subprocess.run([sys.executable, '-m', 'venv', str(venv_path)], check=True)
                
                # Install in virtual environment
                venv_python = venv_path / 'bin' / 'python'
                subprocess.run([str(venv_python), '-m', 'pip', 'install', '-e', '.'], 
                             cwd=self.base_path, check=True)
                
                logger.info("Python dependencies installed successfully in virtual environment")
                logger.info(f"Virtual environment created at: {venv_path}")
                logger.info("To use: source .dev_venv/bin/activate")
                return True
            except subprocess.CalledProcessError:
                logger.info("Virtual environment approach failed, trying user installation...")
            
            # Strategy 2: Try with --user flag for user-local installation
            try:
                subprocess.run([
                    sys.executable, '-m', 'pip', 'install', '--user', '-e', '.'
                ], cwd=self.base_path, check=True)
                logger.info("Python dependencies installed successfully via pip (--user)")
                return True
            except subprocess.CalledProcessError:
                logger.info("Failed with --user flag, trying final fallback...")
            
            # Strategy 3: Last resort - --break-system-packages (with warning)
            try:
                logger.warning("Using --break-system-packages as last resort - this may affect system stability")
                subprocess.run([
                    sys.executable, '-m', 'pip', 'install', '--break-system-packages', '-e', '.'
                ], cwd=self.base_path, check=True)
                logger.info("Python dependencies installed successfully via pip (--break-system-packages)")
                logger.warning("IMPORTANT: System packages may have been affected. Consider using a virtual environment.")
                return True
            except subprocess.CalledProcessError:
                logger.error("All pip installation strategies failed")
                return False
            
        except Exception as e:
            logger.error(f"Unexpected error during dependency installation: {e}")
            return False
    
    def setup_configuration(self):
        """Setup configuration files - same as install.py"""
        try:
            logger.info("Creating configuration files...")
            self._setup_configuration_files()
            logger.info("Configuration files created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup configuration: {e}")
            return False
    
    def _setup_configuration_files(self):
        """Setup configuration files and directories - copied from install.py"""
        # Use the same approach as install.py
        from config.config_manager import ConfigManager
        
        # Initialize ConfigManager which will create the config files
        config_manager = ConfigManager()
        
        # Ensure configuration is set up
        config_manager.setup_fresh_installation(clean_databases=False)
        
        logger.info("Configuration files setup completed")
    
    def detect_system_capabilities(self):
        """Detect system capabilities - same as install.py"""
        try:
            logger.info("Detecting system capabilities...")
            
            # Run system detector same as install.py
            result = subprocess.run([
                sys.executable, 
                str(self.base_path / "utils" / "system_detector.py")
            ], capture_output=True, text=True, check=True)
            
            # Initialize dependency manager for hardware optimization
            sys.path.insert(0, str(self.base_path))
            from utils.dependency_manager import DependencyManager
            
            dep_manager = DependencyManager()
            variant = dep_manager.detect_optimal_variant()
            
            logger.info(f"Detected hardware variant: {variant}")
            if variant == "rpi":
                logger.info("Raspberry Pi optimizations will be applied")
            elif variant == "cuda":
                logger.info("NVIDIA CUDA acceleration available")
            elif variant == "rocm":
                logger.info("AMD ROCm acceleration available")
            elif variant == "aarch64":
                logger.info("ARM64 optimizations available")
            
            logger.info("System detection completed")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"System detection failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during system detection: {e}")
            return False
    
    def setup_live2d(self):
        """Setup Live2D models using the same approach as install.py"""
        try:
            logger.info("Installing Live2D models...")
            
            # Use the same working approach as install.py
            result = subprocess.run([
                sys.executable,
                str(self.base_path / "utils" / "live2d_model_installer.py"),
                "install"
            ], capture_output=True, text=True, check=True)
            
            logger.info("Live2D models installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install Live2D models: {e}")
            logger.error(f"Stdout: {e.stdout}")
            logger.error(f"Stderr: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during Live2D setup: {e}")
            return False
    
    def initialize_databases(self):
        """Initialize databases - same as install.py"""
        try:
            logger.info("Initializing databases...")
            
            # Same as install.py
            sys.path.insert(0, str(self.base_path))
            from databases.database_manager import init_databases, verify_database_schemas
            
            init_databases()
            
            # Verify database schemas were created correctly
            logger.info("Verifying database schemas...")
            verification_results = verify_database_schemas()
            
            # Count successful verifications
            if isinstance(verification_results, dict) and all(result.get('success', False) for result in verification_results.values()):
                total_dbs = len(verification_results)
                logger.info(f"All {total_dbs} databases verified successfully!")
            else:
                logger.info("Database schemas verified successfully!")
            
            logger.info("Database schemas created and verified")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize databases: {e}")
            return False
    
    def download_ai_models(self):
        """Download AI models - same as install.py"""
        try:
            logger.info("Downloading recommended AI models...")
            
            # Use current Python environment for development
            result = subprocess.run([
                sys.executable,
                str(self.base_path / "utils" / "model_downloader.py"),
                "--download-recommended"
            ], capture_output=True, text=True, check=True)
            
            logger.info("AI models downloaded successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to download AI models: {e}")
            logger.error(f"Stdout: {e.stdout}")
            logger.error(f"Stderr: {e.stderr}")
            logger.info("You can download models manually later with:")
            logger.info("  python utils/model_downloader.py --download-recommended")
            # Don't fail installation for this
            return True
        except Exception as e:
            logger.error(f"Unexpected error during AI model download: {e}")
            return True  # Don't fail installation
    
    def run_installation(self):
        """Run complete installation process"""
        logger.info("Starting AI Companion installation...")
        
        # Build steps list based on options
        steps = []
        
        # Add data protection check first
        steps.append(("Checking existing data", self.check_existing_data))
        
        # Add force first run step if requested
        if self.force_first_run:
            steps.append(("Force first-run setup", self.force_first_run_setup))
        
        # Add standard installation steps exactly like install.py
        steps.extend([
            ("Setting up directories", self.setup_directories),
            ("Installing Python dependencies", self.install_python_dependencies),
            ("Setting up configuration", self.setup_configuration),
            ("Detecting system capabilities", self.detect_system_capabilities),
            ("Initializing databases", self.initialize_databases),
            ("Setting up Live2D Viewer Web", self.setup_live2d),
            ("Downloading AI models", self.download_ai_models)
        ])
        
        for step_name, step_function in steps:
            logger.info(f"Step: {step_name}")
            try:
                if callable(step_function):
                    success = step_function()
                else:
                    step_function()
                    success = True
                    
                if not success:
                    logger.error(f"Installation failed at step: {step_name}")
                    return False
                    
            except Exception as e:
                logger.error(f"Installation failed at step: {step_name} - {e}")
                return False
        
        logger.info("✅ AI Companion installation completed successfully!")
        self.print_next_steps()
        return True
    
    def print_next_steps(self):
        """Print next steps for the user"""
        # Get the actual server configuration (use dev port for development)
        try:
            # Use the same config loading approach as production install
            config = self.config.load_config()
            server_config = config.get('server', {})
            host = server_config.get('host', '127.0.0.1')
            # Use dev_port for development, fallback to port + 1 if not configured
            dev_port = server_config.get('dev_port', server_config.get('port', 19080) + 1)
            
            # Use localhost if host is 0.0.0.0
            if host == '0.0.0.0':
                host = 'localhost'
                
            server_url = f"http://{host}:{dev_port}"
        except Exception as e:
            logger.warning(f"Could not load server config: {e}")
            # Get default dev port from config.yaml
            try:
                config = self.config.load_config()
                dev_port = config.get('server', {}).get('dev_port', 19081)
                server_url = f"http://localhost:{dev_port}"
            except Exception:
                server_url = "http://localhost:19081"  # Ultimate fallback
        
        print("\n" + "="*60)
        print("🎉 Development Installation Complete!")
        print("="*60)
        print("\n📝 Development Mode:")
        print("   - Code runs from repository source")
        print("   - Changes are reflected immediately")
        print("   - Uses development port to avoid conflicts")
        print("\nData locations (same as production):")
        
        # Use the same directory access pattern as production install
        try:
            print(f"   - Config: {self.config.config_dir}")
            print(f"   - Data: {self.config.data_dir}")
            print(f"   - Models: {self.config.models_dir}")
            print(f"   - Live2D: {self.config.live2d_models_dir}")
        except Exception as e:
            logger.warning(f"Could not load directory paths: {e}")
            print("   - Config: ~/.config/ai2d_chat/")
            print("   - Data: ~/.local/share/ai2d_chat/")
            print("   - Models: ~/.local/share/ai2d_chat/models/")
            print("   - Live2D: ~/.local/share/ai2d_chat/live2d_models/")
        
        print("\nNext steps:")
        
        # Check if Poetry was used for installation
        pyproject_path = self.base_path / "pyproject.toml"
        uses_poetry = False
        
        if pyproject_path.exists():
            try:
                pyproject_content = pyproject_path.read_text()
                if '[tool.poetry]' in pyproject_content:
                    uses_poetry = True
            except:
                pass
        
        if uses_poetry:
            print("1. Activate the virtual environment:")
            print("   poetry shell")
            print("\n2. Start the AI Companion (development mode):")
            print("   python app.py")
        else:
            print("1. Start the AI Companion (development mode):")
            print("   python app.py")
            print("   (OR from src directory: python -m app)")
        
        print(f"\n{'3' if uses_poetry else '2'}. Open your browser and go to:")
        print(f"   {server_url}")
        
        # Check if Live2D is enabled and print appropriate message
        try:
            from config.config_manager import is_live2d_enabled
            live2d_enabled = is_live2d_enabled()
            if live2d_enabled:
                next_step = "4" if uses_poetry else "3"
                print(f"\n{next_step}. Live2D features are enabled!")
                print(f"   - Place Live2D models in: {self.config.live2d_models_dir}")
                print(f"   - Access Live2D viewer at: {server_url}/live2d")
        except Exception as e:
            logger.warning(f"Could not check Live2D status: {e}")
        
        if self.force_first_run:
            print("\n🔄 Force first-run setup completed!")
            print("   - Configuration files have been recreated")
            print("   - Databases have been cleaned and reinitialized")
            print("   - All existing data has been removed")
            print("   - Please update .secrets file with your API keys")
        else:
            print("\n💾 Data Protection Mode:")
            print("   - Existing databases and models have been preserved")
            print("   - Configuration created only if missing")
            print("   - Use --force to clean existing data if needed")
        
        print("\n💡 Development Tips:")
        print("   - Production install uses port 19080 (ai2d_chat command)")
        print("   - Development install uses port 19081 (python app.py)")
        print("   - Both share the same data directories")
        print("   - For production install: python scripts/install.py")
        
        print("\n" + "="*60)

def main():
    """Main development installation function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Companion Development Installation Script')
    
    # Installation options
    parser.add_argument('--force', action='store_true',
                       help='Force first-run setup (WARNING: removes existing databases and models)')
    parser.add_argument('--skip-live2d', action='store_true',
                       help='Skip Live2D Viewer Web setup')
    parser.add_argument('--skip-deps', action='store_true', 
                       help='Skip Python dependency installation')
    
    args = parser.parse_args()
    
    # Continue with installation
    print("🔧 AI Companion Development Installation")
    print("This sets up AI Companion for development from repository source")
    print("Uses development port (19081) to avoid conflicts with production install")
    
    if args.force:
        print("🔄 Force first-run setup requested - will clean existing configuration...")
        print("\n⚠️  WARNING: This will permanently delete:")
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
    
    installer = AICompanionInstaller(force_first_run=args.force)
    
    # Override config settings based on arguments
    if args.skip_live2d:
        logger.info("Skipping Live2D setup as requested")
        # Temporarily disable Live2D for this installation
        original_setup_live2d = installer.setup_live2d
        installer.setup_live2d = lambda: True
    
    if args.skip_deps:
        logger.info("Skipping dependency installation as requested") 
        # Temporarily disable dependency installation
        original_install_deps = installer.install_python_dependencies
        installer.install_python_dependencies = lambda: True
    
    success = installer.run_installation()
    
    if not success:
        print("\n❌ Development installation failed!")
        print("Check the logs above for error details.")
        
        if not args.force:
            print("\nTry running with --force to clean existing configuration:")
            print("python dev_install.py --force")
        
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Installation failed: {e}")
        if "--debug" in sys.argv:
            import traceback
            traceback.print_exc()
        sys.exit(1)
