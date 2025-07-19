#!/usr/bin/env python3
"""
Custom install hooks for AI2D Chat package installation.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def post_install_hook():
    """
    Post-install hook that runs after package installation.
    This function is called automatically after pip/pipx install.
    """
    try:
        print("🚀 AI2D Chat post-installation setup starting...")
        
        # Import and run the configuration manager setup
        from config.config_manager import ConfigManager
        
        # Create fresh installation with configuration
        config_manager = ConfigManager.setup_fresh_installation(clean_databases=True)
        print("✅ Configuration manager initialized successfully!")
        print("📁 Configuration files created in user directories")
        
        # Check if we should run full setup automatically
        if should_run_auto_setup():
            print("🔧 Running automated setup (models, databases, Live2D)...")
            run_automated_setup()
        else:
            print("📋 Skipping automated setup (run 'ai2d_chat-setup' manually if needed)")
            print("💡 To enable auto-setup: export AI2D_CHAT_AUTO_SETUP=1")
        
        print("🎉 AI2D Chat installation completed!")
        
    except ImportError as e:
        print(f"⚠️  Could not import setup modules: {e}")
        print("🔧 You may need to run 'ai2d_chat-setup' manually")
    except Exception as e:
        print(f"⚠️  Post-install setup failed: {e}")
        print("🔧 You can run setup manually with: ai2d_chat-setup")

def should_run_auto_setup() -> bool:
    """Check if automated setup should be run."""
    # Check environment variable to enable auto-setup
    if os.environ.get('AI2D_CHAT_AUTO_SETUP', '').lower() in ('1', 'true', 'yes'):
        return True
    
    # Check environment variable to explicitly skip setup
    if os.environ.get('AI2D_CHAT_SKIP_SETUP', '').lower() in ('1', 'true', 'yes'):
        return False
    
    # For pipx installations, don't run auto-setup by default (too heavy)
    if 'pipx' in sys.executable or '/pipx/' in sys.executable:
        return False
    
    # For regular pip installs, don't run auto-setup by default either
    # (let users opt-in with environment variable)
    return False

def run_automated_setup():
    """Run the automated setup process."""
    try:
        # Import the setup script
        from scripts.setup_live2d import Live2DSetup
        
        # Run the setup with minimal options for automated install
        setup = Live2DSetup()
        success = setup.run_setup(force_rebuild=False)
        
        if success:
            print("✅ Automated setup completed successfully!")
        else:
            print("⚠️  Automated setup failed - run 'ai2d_chat-setup' manually")
            
    except ImportError:
        print("⚠️  Setup modules not available - run 'ai2d_chat-setup' manually")
    except Exception as e:
        print(f"⚠️  Automated setup failed: {e}")
        print("🔧 Run 'ai2d_chat-setup' manually to complete setup")
