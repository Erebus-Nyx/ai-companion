#!/usr/bin/env python3
"""    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=19443, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode') Companion - Main Entry Point
Production-ready launcher for AI Companion with Live2D integration
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

def setup_logging(level='INFO'):
    """Set up logging configuration"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )

def main():
    """Main entry point for AI Companion"""
    parser = argparse.ArgumentParser(description='AI Companion with Live2D Integration')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=19443, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--config', choices=['development', 'production', 'cloudflare'], 
                       default='production', help='Configuration profile')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Logging level')
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Print startup banner
    print("🤖 AI Companion - Live2D Integration")
    print("=" * 40)
    print(f"🔧 Configuration: {args.config}")
    print(f"🌐 Server: {args.host}:{args.port}")
    print(f"🐛 Debug Mode: {args.debug}")
    print(f"📝 Log Level: {args.log_level}")
    print("=" * 40)
    
    try:
        # Import and configure the Flask app
        from production_config import get_config
        config = get_config(args.config)
        
        # Override with command line arguments
        if args.host:
            config.HOST = args.host
        if args.port:
            config.PORT = args.port
        if args.debug:
            config.DEBUG = True
        
        # Import the main app
        from app import app, socketio
        
        # Apply configuration
        app.config.update(config.get_config_dict())
        
        logger.info(f"🚀 Starting AI Companion on {config.HOST}:{config.PORT}")
        logger.info(f"🎭 Live2D Integration: Enabled")
        logger.info(f"💬 Chat System: Enabled")
        logger.info(f"🔊 Voice Recording: Enabled")
        logger.info(f"🎵 TTS Audio: Enabled")
        
        # Start the server
        socketio.run(
            app, 
            host=config.HOST, 
            port=config.PORT, 
            debug=config.DEBUG,
            allow_unsafe_werkzeug=True  # For development
        )
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.error("💡 Make sure you're in the correct directory and all dependencies are installed")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down AI Companion...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Failed to start AI Companion: {e}")
        sys.exit(1)

def create_systemd_service():
    """Create a systemd service file for production deployment"""
    service_content = """[Unit]
Description=AI Companion Live2D Service
After=network.target

[Service]
Type=simple
User=ai-companion
WorkingDirectory=/opt/ai-companion
Environment=PATH=/home/ai-companion/.local/bin
ExecStart=/home/ai-companion/.local/bin/ai-companion-main --config production
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    with open('ai-companion.service', 'w') as f:
        f.write(service_content)
    
    print("📄 Created ai-companion.service file")
    print("🔧 To install:")
    print("   sudo cp ai-companion.service /etc/systemd/system/")
    print("   sudo systemctl daemon-reload")
    print("   sudo systemctl enable ai-companion")
    print("   sudo systemctl start ai-companion")

def show_deployment_info():
    """Show deployment information"""
    print("\n🚀 AI Companion Deployment Guide")
    print("=" * 40)
    print("\n📦 1. Install with pipx:")
    print("   pipx install .")
    print("   # or for development:")
    print("   pipx install -e .")
    
    print("\n🔧 2. Configuration:")
    print("   # Create configuration file:")
    print("   python src/production_config.py")
    print("   # Edit .env file with your settings")
    
    print("\n🌐 3. Run in different modes:")
    print("   # Development:")
    print("   ai-companion-main --config development --debug")
    print("   # Production:")
    print("   ai-companion-main --config production")
    print("   # Cloudflare-ready:")
    print("   ai-companion-main --config cloudflare --port 8080")
    
    print("\n☁️  4. Cloudflare Setup:")
    print("   # Install cloudflared tunnel")
    print("   # Point DNS A record to your server IP")
    print("   # Configure SSL/TLS encryption")
    
    print("\n🔐 5. Security:")
    print("   # Update SECRET_KEY in .env")
    print("   # Configure CORS_ORIGINS")
    print("   # Set up reverse proxy (nginx/apache)")

if __name__ == '__main__':
    # Check for special commands
    if len(sys.argv) > 1:
        if sys.argv[1] == 'create-service':
            create_systemd_service()
            sys.exit(0)
        elif sys.argv[1] == 'deployment-info':
            show_deployment_info()
            sys.exit(0)
    
    main()
