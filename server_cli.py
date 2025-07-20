#!/usr/bin/env python3
"""
AI2D Chat Server CLI

Command-line interface for starting the AI2D Chat server with proper argument parsing.
"""

import argparse
import sys
import os
import subprocess
import signal
import atexit
from pathlib import Path
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
    # Return hardcoded defaults to avoid triggering app initialization during argument parsing
    return {
        'host': '0.0.0.0',
        'port': 19080,
        'debug': False
    }


def get_config_values():
    """Get actual configuration values from config file."""
    try:
        from config.config_manager import ConfigManager
        manager = ConfigManager()
        config = manager.load_config()
        server_config = config.get('server', {})
        return {
            'host': server_config.get('host', '0.0.0.0'),
            'port': server_config.get('port', 19080),
            'debug': server_config.get('debug', False)
        }
    except Exception:
        # Return hardcoded fallbacks if config manager not available
        return get_config_defaults()


def has_systemd():
    """Check if systemd is available on the system."""
    try:
        # Check if systemctl command exists and systemd is running
        result = subprocess.run(['systemctl', '--version'], 
                              capture_output=True, text=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_systemd_service_path():
    """Get the path to the systemd service file."""
    # Check user systemd directory first
    user_service_dir = Path.home() / ".config" / "systemd" / "user"
    user_service_path = user_service_dir / "ai2d-chat.service"
    
    # Check system systemd directory
    system_service_path = Path("/etc/systemd/system/ai2d-chat.service")
    
    if user_service_path.exists():
        return user_service_path, "user"
    elif system_service_path.exists():
        return system_service_path, "system"
    else:
        return user_service_path, "user"  # Default to user service


def install_systemd_service():
    """Install systemd service for AI2D Chat."""
    service_path, service_type = get_systemd_service_path()
    
    # Get the path to the current executable
    ai2d_chat_server_cmd = subprocess.run(['which', 'ai2d_chat_server'], 
                                         capture_output=True, text=True).stdout.strip()
    if not ai2d_chat_server_cmd:
        ai2d_chat_server_cmd = str(Path.home() / ".local" / "bin" / "ai2d_chat_server")
    
    service_content = f"""[Unit]
Description=AI2D Chat Server
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'ai2d')}
ExecStart={ai2d_chat_server_cmd} --foreground
Restart=always
RestartSec=3
Environment=PATH=/usr/local/bin:/usr/bin:/bin:{Path.home() / '.local' / 'bin'}

[Install]
WantedBy=default.target
"""
    
    # Create service directory if it doesn't exist
    service_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write service file
    service_path.write_text(service_content)
    
    # Reload systemd and enable service
    try:
        if service_type == "user":
            subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
            subprocess.run(['systemctl', '--user', 'enable', 'ai2d-chat.service'], check=True)
        else:
            subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
            subprocess.run(['sudo', 'systemctl', 'enable', 'ai2d-chat.service'], check=True)
        
        return True, service_type
    except subprocess.CalledProcessError as e:
        return False, str(e)


def start_systemd_service():
    """Start the AI2D Chat systemd service."""
    service_path, service_type = get_systemd_service_path()
    
    if not service_path.exists():
        print("📦 Installing systemd service...")
        success, result = install_systemd_service()
        if not success:
            print(f"❌ Failed to install systemd service: {result}")
            return False
        print(f"✅ Systemd service installed ({result} service)")
    
    try:
        if service_type == "user":
            subprocess.run(['systemctl', '--user', 'start', 'ai2d-chat.service'], check=True)
            subprocess.run(['systemctl', '--user', 'status', 'ai2d-chat.service', '--no-pager'], check=True)
        else:
            subprocess.run(['sudo', 'systemctl', 'start', 'ai2d-chat.service'], check=True)
            subprocess.run(['sudo', 'systemctl', 'status', 'ai2d-chat.service', '--no-pager'], check=True)
        
        print(f"✅ AI2D Chat server started via systemd ({service_type} service)")
        print(f"📊 Check status: systemctl {'--user ' if service_type == 'user' else ''}status ai2d-chat.service")
        print(f"📋 View logs: journalctl {'--user ' if service_type == 'user' else ''}-u ai2d-chat.service -f")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start systemd service: {e}")
        return False


def daemonize():
    """Fork the process to run as a daemon."""
    try:
        # First fork
        pid = os.fork()
        if pid > 0:
            # Parent process exits
            sys.exit(0)
    except OSError as e:
        print(f"❌ First fork failed: {e}")
        sys.exit(1)
    
    # Decouple from parent environment
    os.chdir("/")
    os.setsid()
    os.umask(0)
    
    try:
        # Second fork
        pid = os.fork()
        if pid > 0:
            # Second parent exits
            sys.exit(0)
    except OSError as e:
        print(f"❌ Second fork failed: {e}")
        sys.exit(1)
    
    # Redirect standard file descriptors
    sys.stdout.flush()
    sys.stderr.flush()
    
    # Create log directory
    log_dir = Path.home() / ".local" / "share" / "ai2d_chat" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Redirect stdout and stderr to log files
    stdout_log = log_dir / "server.log"
    stderr_log = log_dir / "server_error.log"
    
    with open(stdout_log, 'a+') as f:
        os.dup2(f.fileno(), sys.stdout.fileno())
    with open(stderr_log, 'a+') as f:
        os.dup2(f.fileno(), sys.stderr.fileno())
    
    # Write PID file
    pid_file = log_dir / "server.pid"
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))
    
    # Register cleanup function
    atexit.register(lambda: pid_file.unlink(missing_ok=True))
    
    print(f"🔧 Daemon started with PID {os.getpid()}")
    print(f"📋 Logs: {stdout_log}")
    print(f"📋 Errors: {stderr_log}")
    print(f"📋 PID file: {pid_file}")
    
    return True


def create_parser():
    """Create argument parser for server CLI."""
    parser = argparse.ArgumentParser(
        prog='ai2d_chat_server',
        description='AI2D Chat Server - Start the AI companion server with Live2D avatar',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  ai2d_chat_server                      # Start server (background via systemd/daemon)
  ai2d_chat_server --foreground         # Start server in foreground for testing
  ai2d_chat_server --port 8080          # Start server on port 8080
  ai2d_chat_server --host 127.0.0.1     # Start server on localhost only
  ai2d_chat_server --debug --foreground # Start server in debug mode, foreground

Default behavior:
  - Detects systemd and runs as systemd service if available
  - Falls back to daemon mode if systemd not available
  - Use --foreground to disable background mode for testing

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
        help='Host to bind the server to (default: from config or 0.0.0.0)'
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        help='Port to bind the server to (default: from config or 19080)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Run server in debug mode with auto-reload'
    )
    
    parser.add_argument(
        '--dev',
        action='store_true',
        help='Run in development mode (alias for --debug)'
    )
    
    parser.add_argument(
        '--foreground', '-f',
        action='store_true',
        help='Run server in foreground (disable systemd/daemon mode) - useful for testing'
    )
    
    parser.add_argument(
        '--no-daemon',
        action='store_true',
        help='Disable daemon mode (alias for --foreground)'
    )
    
    return parser


def main():
    """Main entry point for server CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Try to get config values from file, fall back to defaults if not available
    try:
        config_values = get_config_values()
    except Exception:
        config_values = get_config_defaults()
    
    # Use config values if CLI args are not provided
    host = args.host if args.host is not None else config_values['host']
    port = args.port if args.port is not None else config_values['port']
    debug = args.debug or args.dev or config_values['debug']
    
    # Determine if we should run in foreground
    run_foreground = args.foreground or args.no_daemon or debug
    
    # Set environment variables for the server to pick up
    defaults = get_config_defaults()
    if host != defaults['host']:
        os.environ['AI2D_SERVER_HOST'] = host
    if port != defaults['port']:
        os.environ['AI2D_SERVER_PORT'] = str(port)
    if debug:
        os.environ['AI2D_DEBUG'] = 'true'
    
    # Import and start server with parsed arguments
    try:
        if run_foreground:
            # Run in foreground mode
            print(f"🚀 Starting {get_version_string()} (foreground mode)")
            print(f"🌐 Server will be available at: http://{host}:{port}")
            if debug:
                print("🔧 Debug mode enabled")
            print("📡 Press Ctrl+C to stop the server")
            print("-" * 50)
            
            # Import and run server directly
            from app import run_server
            run_server()
            
        else:
            # Run in background mode (default)
            print(f"🚀 Starting {get_version_string()} (background mode)")
            print(f"🌐 Server will be available at: http://{host}:{port}")
            
            # Check for systemd first
            if has_systemd():
                print("📦 Systemd detected - starting as systemd service")
                if start_systemd_service():
                    print("✅ Server started successfully via systemd")
                    return
                else:
                    print("⚠️  Systemd service failed, falling back to daemon mode")
            
            # Fall back to daemon mode
            print("🔧 Starting as daemon process")
            
            # Fork to daemon
            if daemonize():
                # We're now in the daemon process
                from app import run_server
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
