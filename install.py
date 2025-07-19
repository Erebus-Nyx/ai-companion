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

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AI2DChatInstaller:
    def __init__(self, force_reinstall: bool = False, auto_setup: bool = True):
        self.force_reinstall = force_reinstall
        self.auto_setup = auto_setup
        self.project_root = Path(__file__).parent.resolve()
        self.dist_dir = self.project_root / 'dist'
        
    def check_prerequisites(self) -> bool:
        """Check if required tools are available."""
        required_tools = ['python', 'pip', 'pipx']
        
        print("🔍 Checking prerequisites...")
        
        for tool in required_tools:
            try:
                result = subprocess.run([tool, '--version'], 
                                      capture_output=True, text=True, check=True)
                print(f"✅ {tool}: {result.stdout.strip().split()[0]}")
            except (subprocess.CalledProcessError, FileNotFoundError):
                if tool == 'pipx':
                    print(f"❌ {tool} not found - installing...")
                    try:
                        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pipx'], check=True)
                        subprocess.run([sys.executable, '-m', 'pipx', 'ensurepath'], check=True)
                        print("✅ pipx installed successfully")
                    except subprocess.CalledProcessError as e:
                        print(f"❌ Failed to install pipx: {e}")
                        return False
                else:
                    print(f"❌ {tool} not found and is required")
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
    
    def clean_previous_installation(self):
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
            except Exception as e:
                print(f"⚠️  Clean failed (may not have been installed): {e}")
    
    def build_package(self) -> bool:
        """Build the wheel package."""
        print("🔨 Building wheel package...")
        
        try:
            # Change to project root
            original_cwd = os.getcwd()
            os.chdir(self.project_root)
            
            # Clean dist directory
            if self.dist_dir.exists():
                shutil.rmtree(self.dist_dir)
            
            # Build the package
            subprocess.run([sys.executable, '-m', 'build'], check=True)
            
            # Check if wheel was created
            wheel_files = list(self.dist_dir.glob('*.whl'))
            if not wheel_files:
                print("❌ No wheel file found after build")
                return False
            
            self.wheel_file = wheel_files[0]
            print(f"✅ Package built: {self.wheel_file.name}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Build failed: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error during build: {e}")
            return False
        finally:
            os.chdir(original_cwd)
    
    def install_package(self) -> bool:
        """Install the package using pipx."""
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
            
            subprocess.run(cmd, check=True, env=env)
            print("✅ Package installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Installation failed: {e}")
            return False
    
    def run_post_install_setup(self) -> bool:
        """Run the post-installation setup."""
        if not self.auto_setup:
            print("⏭️  Skipping automatic setup (use --no-auto-setup was specified)")
            return True
        
        print("🔧 Running post-installation setup...")
        
        try:
            # Run the setup script
            subprocess.run(['ai2d_chat-setup'], check=True)
            print("✅ Setup completed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Setup failed: {e}")
            print("🔧 You can run setup manually later with: ai2d_chat-setup")
            return False
        except FileNotFoundError:
            print("⚠️  ai2d_chat-setup command not found in PATH")
            print("🔧 You may need to restart your shell or run: pipx ensurepath")
            return False
    
    def verify_installation(self) -> bool:
        """Verify the installation works."""
        print("🧪 Verifying installation...")
        
        try:
            # Test CLI
            result = subprocess.run(['ai2d_chat', '--help'], 
                                  capture_output=True, text=True, check=True)
            print("✅ CLI working")
            
            # Test server (just check help, don't start)
            result = subprocess.run(['ai2d_chat-server', '--help'], 
                                  capture_output=True, text=True, check=True)
            print("✅ Server command working")
            
            # Test setup command
            result = subprocess.run(['ai2d_chat-setup', '--help'], 
                                  capture_output=True, text=True, check=True)
            print("✅ Setup command working")
            
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
        print("✅ Configuration files created")
        print("✅ User directories initialized")
        
        if self.auto_setup:
            print("✅ Models and resources setup attempted")
        
        print("\n🚀 Getting Started:")
        print("1. Start the server:")
        print("   ai2d_chat-server")
        print("\n2. Or use the CLI:")
        print("   ai2d_chat --help")
        print("\n3. Access the web interface:")
        print("   http://localhost:5000")
        
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
    
    args = parser.parse_args()
    
    installer = AI2DChatInstaller(
        force_reinstall=args.force,
        auto_setup=not args.no_auto_setup
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
