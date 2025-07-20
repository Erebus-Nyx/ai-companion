#!/usr/bin/env python3
"""
AI2D Chat Server CLI

Command-line interface for starting the AI2D Chat server with proper argument parsing.
"""

import argparse
import sys
from typing import Optional

try:
    from __version__ import __version__, get_version_string
except ImportError:
    try:
        from .__version__ import __version__, get_version_string
    except ImportError:
        # Fallback for development
        __version__ = "0.4.0"
        def get_version_string():
            return f"AI2D Chat v{__version__}"


def get_config_defaults():
    """Get default configuration values for server arguments."""
    try:
        from config.config_manager import ConfigManager
        manager = ConfigManager()
        config = manager.load_config()
        return {
            'host': config.get('host', '0.0.0.0'),
            'port': config.get('port', 19080),
            'debug': config.get('debug', False)
        }
    except Exception:
        # Return hardcoded fallbacks if config manager not available
        return {
            'host': '0.0.0.0',
            'port': 19080,
            'debug': False
        }


def create_parser():
    """Create argument parser for server CLI."""
    defaults = get_config_defaults()
    
    parser = argparse.ArgumentParser(
        prog='ai2d_chat_server',
        description='AI2D Chat Server - Start the AI companion server with Live2D avatar',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  ai2d_chat_server                    # Start server with default settings
  ai2d_chat_server --port 8080       # Start server on port 8080
  ai2d_chat_server --host 127.0.0.1  # Start server on localhost only
  ai2d_chat_server --debug           # Start server in debug mode

{get_version_string()}
For more information, visit: https://github.com/Erebus-Nyx/ai2d_chat
        """
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version=f'AI2D Chat Server {__version__}'
    )
    
    parser.add_argument(
        '--host',
        default=defaults['host'],
        help=f'Host to bind the server to (default: {defaults["host"]})'
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=defaults['port'],
        help=f'Port to bind the server to (default: {defaults["port"]})'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        default=defaults['debug'],
        help='Run server in debug mode with auto-reload'
    )
    
    parser.add_argument(
        '--dev',
        action='store_true',
        help='Run in development mode (alias for --debug)'
    )
    
    return parser


def main():
    """Main entry point for server CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Import and start server with parsed arguments
    try:
        # First, update configuration with command line arguments if provided
        from config.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Update server configuration with CLI arguments
        server_config = config.get('server', {})
        
        # Only update if values differ from defaults
        defaults = get_config_defaults()
        if args.host != defaults['host']:
            server_config['host'] = args.host
        if args.port != defaults['port']:
            server_config['port'] = args.port
        if args.debug or args.dev:
            server_config['debug'] = True
        
        # Save updated config
        config['server'] = server_config
        config_manager.save_config(config)
        
        # Import and run server
        from app import run_server
        
        print(f"🚀 Starting {get_version_string()}")
        print(f"🌐 Server will be available at: http://{args.host}:{args.port}")
        if args.debug or args.dev:
            print("🔧 Debug mode enabled")
        print("📡 Press Ctrl+C to stop the server")
        print("-" * 50)
        
        # Start the server (it will read from updated config)
        run_server()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
        sys.exit(0)
    except ImportError as e:
        print(f"❌ Error importing server components: {e}")
        print("🔧 Make sure AI2D Chat is properly installed")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
