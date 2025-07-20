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
    python scripts/dev_install.py [options]
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from config.config_manager import ConfigManager
from setup_live2d import Live2DSetup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AICompanionInstaller:
    def __init__(self, force_first_run=False):
        self.base_path = Path(__file__).parent.parent
        self.config = ConfigManager()
        self.force_first_run = force_first_run
        
    def force_first_run_setup(self):
        """Force first-run setup by cleaning existing configurations"""
        try:
            logger.info("Force first-run setup requested...")
            
            # Clean existing configuration and databases
            if not self.config.is_dev_mode:
                # Production mode - clean user directories
                logger.info("Cleaning existing user configuration...")
                config_path = self.config.get_config_path()
                secrets_path = self.config.get_secrets_path()
                
                # Remove existing config files
                if config_path.exists():
                    config_path.unlink()
                    logger.info(f"Removed existing config: {config_path}")
                
                if secrets_path.exists():
                    secrets_path.unlink()
                    logger.info(f"Removed existing secrets: {secrets_path}")
                
                # Clean databases
                self.config.clean_install_databases()
                
                # Force reinstall of configuration
                self.config.install_configuration_files(clean_databases=True)
                
            else:
                # Development mode - just clean databases
                logger.info("Development mode - cleaning databases only...")
                self.config.clean_install_databases()
                
            logger.info("Force first-run setup completed")
            return True
            
        except Exception as e:
            logger.error(f"Force first-run setup failed: {e}")
            return False
    
    def setup_directories(self):
        """Create necessary directories"""
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
    
    def install_python_dependencies(self):
        """Install Python dependencies using Poetry"""
        try:
            logger.info("Installing Python dependencies...")
            subprocess.run(['poetry', 'install'], cwd=self.base_path, check=True)
            logger.info("Python dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install Python dependencies: {e}")
            return False
        except FileNotFoundError:
            logger.error("Poetry not found. Please install Poetry first:")
            logger.error("curl -sSL https://install.python-poetry.org | python3 -")
            return False
    
    def setup_live2d(self):
        """Setup Live2D Viewer Web if enabled"""
        if not self.config.is_live2d_enabled():
            logger.info("Live2D is disabled in configuration, skipping setup")
            return True
        
        if not self.config.should_auto_setup_live2d():
            logger.info("Live2D auto-setup is disabled, skipping")
            return True
        
        logger.info("Setting up Live2D Viewer Web...")
        live2d_setup = Live2DSetup(self.config)
        return live2d_setup.run_setup()
    
    def initialize_databases(self):
        """Initialize SQLite databases"""
        try:
            logger.info("Initializing databases...")
            
            # Import database initialization functions
            from database.live2d_models_separated import initialize_live2d_database
            
            # Initialize databases
            initialize_live2d_database()
            
            logger.info("Databases initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize databases: {e}")
            return False
    
    def run_installation(self):
        """Run complete installation process"""
        logger.info("Starting AI Companion installation...")
        
        # Build steps list based on options
        steps = []
        
        # Add force first run step if requested
        if self.force_first_run:
            steps.append(("Force first-run setup", self.force_first_run_setup))
        
        # Add standard installation steps
        steps.extend([
            ("Setting up directories", self.setup_directories),
            ("Installing Python dependencies", self.install_python_dependencies),
            ("Setting up Live2D Viewer Web", self.setup_live2d),
            ("Initializing databases", self.initialize_databases)
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
            server_url = "http://localhost:19081"  # Default dev port
        
        print("\n" + "="*60)
        print("🎉 Development Installation Complete!")
        print("="*60)
        print("\n📝 Development Mode:")
        print("   - Code runs from repository source")
        print("   - Changes are reflected immediately")
        print("   - Uses development port to avoid conflicts")
        print("\nData locations (same as production):")
        print(f"   - Config: {self.config.config_dir}")
        print(f"   - Data: {self.config.data_dir}")
        print(f"   - Models: {self.config.models_dir}")
        print(f"   - Live2D: {self.config.live2d_models_dir}")
        print("\nNext steps:")
        print("1. Activate the virtual environment:")
        print("   poetry shell")
        print("\n2. Start the AI Companion (development mode):")
        print("   python app.py")
        print(f"\n3. Open your browser and go to:")
        print(f"   {server_url}")
        
        # Check if Live2D is enabled and print appropriate message
        try:
            live2d_enabled = self.config.is_live2d_enabled()
            if live2d_enabled:
                print("\n4. Live2D features are enabled!")
                print(f"   - Place Live2D models in: {self.config.live2d_models_dir}")
                print(f"   - Access Live2D viewer at: {server_url}/live2d")
        except Exception as e:
            logger.warning(f"Could not check Live2D status: {e}")
        
        if self.force_first_run:
            print("\n🔄 Force first-run setup completed!")
            print("   - Configuration files have been recreated")
            print("   - Databases have been cleaned and reinitialized")
            print("   - Please update .secrets file with your API keys")
        
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
    parser.add_argument('--force', action='store_true',
                       help='Force first-run setup (clean existing config and databases)')
    parser.add_argument('--skip-live2d', action='store_true',
                       help='Skip Live2D Viewer Web setup')
    parser.add_argument('--skip-deps', action='store_true', 
                       help='Skip Python dependency installation')
    
    args = parser.parse_args()
    
    print("🔧 AI Companion Development Installation")
    print("This sets up AI Companion for development from repository source")
    print("Uses development port (19081) to avoid conflicts with production install")
    
    if args.force:
        print("🔄 Force first-run setup requested - will clean existing configuration...")
    
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
            print("python scripts/dev_install.py --force")
        
        sys.exit(1)

if __name__ == "__main__":
    main()
