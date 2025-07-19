#!/usr/bin/env python3
"""
AI Companion Production Installation Script

This script handles complete production installation:
1. Building the wheel package
2. Installing with pipx in isolated environment
3. Running first-time setup automatically
4. Configuring the application for immediate use

This is the MAIN installation script for end users.

Key features:
- Installs AI Companion as a system-wide application
- Uses production port (19080) 
- Command available: ai2d_chat
- Isolated environment via pipx
- Automatic configuration setup

Data locations:
- Config: ~/.config/ai2d_chat/config.yaml
- Data: ~/.local/share/ai2d_chat/
- Cache: ~/.cache/ai2d_chat/

Usage:
    python scripts/install.py [options]
    
Options:
    --force         Force clean installation (remove existing)
    --skip-build    Skip building the wheel (use existing)
    --skip-setup    Skip post-install setup

For development setup from repository:
    python scripts/dev_install.py
"""

import os
import sys
import subprocess
import shutil
import logging
import argparse
import tempfile
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProductionInstaller:
    def __init__(self, force=False, skip_build=False, skip_setup=False):
        self.base_path = Path(__file__).parent.parent
        self.force = force
        self.skip_build = skip_build
        self.skip_setup = skip_setup
        
        # Package info
        self.package_name = "ai2d_chat"
        self.package_version = "0.4.0"
        self.wheel_name = f"{self.package_name}-{self.package_version}-py3-none-any.whl"
        
    def check_prerequisites(self) -> bool:
        """Check if required tools are available"""
        required_tools = ['python3', 'pip', 'pipx']
        
        if self.skip_build:
            required_tools = ['pipx']  # Only need pipx if skipping build
        
        missing_tools = []
        for tool in required_tools:
            try:
                result = subprocess.run([tool, '--version'], 
                                      capture_output=True, text=True, check=True)
                logger.info(f"{tool} version: {result.stdout.strip()}")
            except (subprocess.CalledProcessError, FileNotFoundError):
                missing_tools.append(tool)
        
        if missing_tools:
            logger.error(f"Missing required tools: {', '.join(missing_tools)}")
            logger.error("Please install missing tools:")
            for tool in missing_tools:
                if tool == 'pipx':
                    logger.error(f"  {tool}: python -m pip install --user pipx")
                else:
                    logger.error(f"  {tool}: Install from your system package manager")
            return False
            
        return True
    
    def clean_existing_installation(self) -> bool:
        """Remove existing installation if force is enabled"""
        if not self.force:
            return True
            
        try:
            logger.info("Cleaning existing installation...")
            
            # Uninstall existing package
            subprocess.run(['pipx', 'uninstall', self.package_name], 
                         capture_output=True, check=False)
            
            # Clean user data directories
            user_dirs = [
                Path.home() / '.config' / 'ai2d_chat',
                Path.home() / '.local' / 'share' / 'ai2d_chat', 
                Path.home() / '.cache' / 'ai2d_chat'
            ]
            
            for user_dir in user_dirs:
                if user_dir.exists():
                    logger.info(f"Removing user directory: {user_dir}")
                    shutil.rmtree(user_dir, ignore_errors=True)
            
            logger.info("Existing installation cleaned")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clean existing installation: {e}")
            return False
    
    def build_package(self) -> bool:
        """Build the wheel package"""
        if self.skip_build:
            logger.info("Skipping package build as requested")
            return True
            
        try:
            logger.info("Building wheel package...")
            
            # Change to project root
            original_cwd = os.getcwd()
            os.chdir(self.base_path)
            
            # Clean existing build artifacts
            build_dirs = ['build', 'dist', '*.egg-info']
            for pattern in build_dirs:
                for path in self.base_path.glob(pattern):
                    if path.is_dir():
                        shutil.rmtree(path, ignore_errors=True)
                    else:
                        path.unlink(missing_ok=True)
            
            # Build the package
            subprocess.run([sys.executable, '-m', 'build'], check=True)
            
            # Verify wheel was created
            wheel_path = self.base_path / 'dist' / self.wheel_name
            if not wheel_path.exists():
                logger.error(f"Wheel file not found: {wheel_path}")
                return False
                
            logger.info(f"Package built successfully: {wheel_path}")
            os.chdir(original_cwd)
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Package build failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during build: {e}")
            return False
        finally:
            try:
                os.chdir(original_cwd)
            except:
                pass
    
    def install_package(self) -> bool:
        """Install the package using pipx"""
        try:
            wheel_path = self.base_path / 'dist' / self.wheel_name
            
            if not wheel_path.exists() and not self.skip_build:
                logger.error(f"Wheel file not found: {wheel_path}")
                return False
            
            logger.info("Installing with pipx...")
            install_cmd = ['pipx', 'install', str(wheel_path)]
            if self.force:
                install_cmd.append('--force')
            subprocess.run(install_cmd, check=True)
            
            logger.info("Package installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Package installation failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during installation: {e}")
            return False
    
    def run_post_install_setup(self) -> bool:
        """Run post-installation setup"""
        if self.skip_setup:
            logger.info("Skipping post-install setup as requested")
            return True
            
        try:
            logger.info("Running post-installation setup...")
            
            # Run the setup through the installed package's CLI
            try:
                # First, try to run the setup command if available
                subprocess.run(['ai2d_chat', '--setup'], check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Fallback: run the configuration setup manually
                logger.info("Setting up configuration manually...")
                
                # Import and setup configuration using the pipx environment
                setup_code = '''
import sys
import subprocess
import glob
from pathlib import Path

# Find the correct pipx venv path dynamically
home = Path.home()
venv_base = home / ".local" / "share" / "pipx" / "venvs" / "ai2d-chat"
python_exe = venv_base / "bin" / "python"

# Also find site-packages for backup method
venv_path = list(venv_base.glob("lib/python*/site-packages"))

try:
    # Use the pipx environment's python to run the setup
    result = subprocess.run([
        str(python_exe), 
        "-c", 
        """
try:
    from ai2d_chat.config.config_manager import ConfigManager
    config_manager = ConfigManager.setup_fresh_installation(clean_databases=True)
    print("Configuration setup completed successfully!")
except Exception as e:
    print(f"Configuration setup failed: {e}")
    exit(1)
"""
    ], capture_output=True, text=True, check=True)
    print(result.stdout)
except subprocess.CalledProcessError as e:
    print(f"Setup failed: {e}")
    if e.stderr:
        print(f"Error: {e.stderr}")
    sys.exit(1)
except Exception as e:
    print(f"Configuration setup failed: {e}")
    sys.exit(1)
'''
                subprocess.run([sys.executable, '-c', setup_code], check=True)
            
            logger.info("Post-installation setup completed")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Post-installation setup failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during setup: {e}")
            return False
    
    def verify_installation(self) -> bool:
        """Verify the installation was successful"""
        try:
            logger.info("Verifying installation...")
            
            # Test if the command is available
            result = subprocess.run(['ai2d_chat', '--version'], 
                                  capture_output=True, text=True, check=True)
            logger.info(f"Installation verified: {result.stdout.strip()}")
            
            # Test configuration loading using the pipx environment
            try:
                from pathlib import Path
                home = Path.home()
                python_exe = home / ".local" / "share" / "pipx" / "venvs" / "ai2d-chat" / "bin" / "python"
                
                result = subprocess.run([
                    str(python_exe), 
                    "-c", 
                    """
try:
    from ai2d_chat.config.config_manager import ConfigManager
    config_manager = ConfigManager()
    config = config_manager.load_config()
    print(f"Configuration loaded successfully - Server port: {config.get('server', {}).get('port', 'unknown')}")
except Exception as e:
    print(f"Configuration test failed: {e}")
    exit(1)
"""
                ], capture_output=True, text=True, check=True)
                logger.info(f"Configuration test: {result.stdout.strip()}")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Configuration test failed, but installation may still be functional: {e}")
                # Don't fail the installation for this
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Installation verification failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during verification: {e}")
            return False
    
    def print_completion_message(self):
        """Print installation completion message"""
        print("\n" + "="*70)
        print("🎉 AI Companion Installation Completed Successfully!")
        print("="*70)
        
        print("\n📦 Production Installation:")
        print("   - Package installed via pipx in isolated environment")
        print("   - Command available system-wide: ai2d_chat")
        print("   - Start with: ai2d_chat")
        
        print("\n🚀 Next Steps:")
        print("1. Edit configuration: ~/.config/ai2d_chat/config.yaml")
        print("2. Update secrets: ~/.config/ai2d_chat/.secrets")
        print("3. Add API keys (HuggingFace token required for some models)")
        print("4. Place Live2D models in: ~/.local/share/ai2d_chat/live2d_models/")
        
        # Get server URL from config
        try:
            config_code = '''
from config.config_manager import ConfigManager
config = ConfigManager().load_config()
server = config.get("server", {})
host = server.get("host", "localhost")
port = server.get("port", 19080)
if host == "0.0.0.0":
    host = "localhost"
print(f"http://{host}:{port}")
'''
            result = subprocess.run([sys.executable, '-c', config_code], 
                                  capture_output=True, text=True, check=False)
            if result.returncode == 0:
                server_url = result.stdout.strip()
            else:
                server_url = "http://localhost:19080"
        except:
            server_url = "http://localhost:19080"
        
        print(f"\n5. Start the application and visit: {server_url}")
        
        if self.force:
            print("\n🔄 Force Installation Notes:")
            print("   - All existing configuration and data was cleaned")
            print("   - Fresh setup completed with default settings")
            print("   - Please reconfigure as needed")
        
        print("\n" + "="*70)
    
    def run_complete_installation(self) -> bool:
        """Run the complete installation process"""
        logger.info("Starting complete AI Companion installation...")
        
        steps = [
            ("Checking prerequisites", self.check_prerequisites),
            ("Cleaning existing installation", self.clean_existing_installation),
            ("Building package", self.build_package),
            ("Installing package", self.install_package),
            ("Running post-install setup", self.run_post_install_setup),
            ("Verifying installation", self.verify_installation)
        ]
        
        for step_name, step_function in steps:
            logger.info(f"Step: {step_name}")
            try:
                success = step_function()
                if not success:
                    logger.error(f"Installation failed at step: {step_name}")
                    return False
            except Exception as e:
                logger.error(f"Installation failed at step: {step_name} - {e}")
                return False
        
        self.print_completion_message()
        return True

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='AI Companion Production Installation')
    parser.add_argument('--force', action='store_true',
                       help='Force clean installation (remove existing)')
    parser.add_argument('--skip-build', action='store_true',
                       help='Skip building the wheel (use existing)')
    parser.add_argument('--skip-setup', action='store_true',
                       help='Skip post-install setup')
    
    args = parser.parse_args()
    
    installer = ProductionInstaller(
        force=args.force,
        skip_build=args.skip_build,
        skip_setup=args.skip_setup
    )
    
    success = installer.run_complete_installation()
    
    if not success:
        print("\n❌ Production installation failed!")
        print("Check the logs above for error details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
