#!/usr/bin/env python3
"""
Development CLI for AI2D Chat
Provides development-specific configuration and features for testing
"""

import os
import sys
import argparse
import logging
import signal
import subprocess
from pathlib import Path

# Set development configuration
os.environ['AI2D_ENV'] = 'development'
os.environ['AI2D_DEBUG'] = 'true'

def setup_development_logging():
    """Setup enhanced logging for development"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('ai2d_chat_dev.log')
        ]
    )

def main():
    """Main development CLI entry point"""
    parser = argparse.ArgumentParser(
        description='AI2D Chat Development CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Development Commands:
  server     Start development server with debug enabled
  test       Run development tests
  reset      Reset development databases and configurations
  debug      Start with maximum debugging output

Server Options:
  --background, -b    Run server in background (daemon mode)
  --foreground, -f    Run server in foreground (override config)
  --stop              Stop running development server
  --status            Check development server status
  --port PORT         Specify port (default: from config or 19081)
  --host HOST         Specify host (default: 127.0.0.1)

Examples:
  ai2d_chat_dev server                    # Start development server (background by default)
  ai2d_chat_dev server --foreground       # Start development server (foreground)
  ai2d_chat_dev server --background       # Start development server (background, explicit)
  ai2d_chat_dev server --port 19081       # Start on specific port
  ai2d_chat_dev server --stop             # Stop running development server
  ai2d_chat_dev server --status           # Check server status
  ai2d_chat_dev test                      # Run tests
  ai2d_chat_dev debug                     # Debug mode
        """
    )
    
    parser.add_argument('command', 
                       choices=['server', 'test', 'reset', 'debug'],
                       help='Development command to run')
    parser.add_argument('--port', type=int, default=None,
                       help='Port for development server (default: from config or 19081)')
    parser.add_argument('--host', default=None,
                       help='Host for development server (default: from config or 127.0.0.1)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--background', '-b', action='store_true',
                       help='Run server in background (daemon mode) - this is the default')
    parser.add_argument('--foreground', '-f', action='store_true',
                       help='Run server in foreground (override default background mode)')
    parser.add_argument('--stop', action='store_true',
                       help='Stop running development server')
    parser.add_argument('--status', action='store_true',
                       help='Check development server status')
    
    args = parser.parse_args()
    
    # Setup development environment
    setup_development_logging()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.command == 'server':
        if args.stop:
            stop_development_server()
        elif args.status:
            check_development_server_status()
        else:
            # Determine background mode from config and command line args
            background_mode = determine_background_mode(args)
            start_development_server(args.host, args.port, background_mode)
    elif args.command == 'test':
        run_development_tests()
    elif args.command == 'reset':
        reset_development_environment()
    elif args.command == 'debug':
        start_debug_mode()

def determine_background_mode(args):
    """Determine background mode from config and command line arguments"""
    # Command line arguments take precedence
    if args.foreground:
        return False
    if args.background:
        return True
    
    # Check config file for background setting
    try:
        from config.config_manager import ConfigManager
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Get background setting from server config
        server_config = config.get('server', {})
        background_from_config = server_config.get('background', True)  # Default to True (background)
        
        print(f"📋 Background mode from config: {background_from_config}")
        return background_from_config
        
    except Exception as e:
        print(f"⚠️  Could not read background setting from config: {e}")
        return True  # Default to background if config can't be read

def kill_process_on_port(port):
    """Kill any process using the specified port"""
    import subprocess
    import time
    
    try:
        # Find processes using the port
        result = subprocess.run(
            ['lsof', '-ti', f':{port}'], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid.strip():
                    try:
                        pid_int = int(pid.strip())
                        print(f"🔪 Killing process {pid_int} on port {port}")
                        
                        # Try graceful termination first
                        os.kill(pid_int, signal.SIGTERM)
                        time.sleep(1)
                        
                        # Check if process is still running
                        try:
                            os.kill(pid_int, 0)  # Test if process exists
                            print(f"   Process {pid_int} still running, forcing termination...")
                            os.kill(pid_int, signal.SIGKILL)
                            time.sleep(0.5)
                        except OSError:
                            # Process is gone
                            pass
                            
                        print(f"✅ Process {pid_int} terminated")
                        
                    except (ValueError, OSError) as e:
                        print(f"⚠️  Could not kill process {pid}: {e}")
        else:
            print(f"📋 No existing processes found on port {port}")
            
    except subprocess.TimeoutExpired:
        print(f"⚠️  Timeout checking for processes on port {port}")
    except subprocess.CalledProcessError:
        print(f"📋 No existing processes found on port {port} (lsof not available or no matches)")
    except Exception as e:
        print(f"⚠️  Error checking port {port}: {e}")

def start_development_server(host=None, port=None, background=False):
    """Start the development server with enhanced debugging"""
    
    # Get port and host from config if not specified
    try:
        from config.config_manager import ConfigManager
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Extract dev_port and host from config
        server_config = config.get('server', {})
        
        if port is None:
            port = server_config.get('dev_port', 19081)
            print(f"📋 Development port from config: {port}")
        
        if host is None:
            host = server_config.get('host', '127.0.0.1')
            print(f"📋 Development host from config: {host}")
            
    except Exception as e:
        if port is None:
            port = 19081
        if host is None:
            host = '127.0.0.1'
        print(f"⚠️  Error reading config, using defaults - host: {host}, port: {port} ({e})")
    
    # Kill any process using the target port
    kill_process_on_port(port)
    
    print(f"🚀 Starting AI2D Chat Development Server on {host}:{port}")
    print("📋 Development features enabled:")
    print("   - Debug mode: ON")
    print("   - Enhanced logging: ON")
    print("   - Hot reload: ON") 
    print("   - TTS debugging: ON")
    print(f"   - Background mode: {'ON' if background else 'OFF'}")
    
    # Handle background mode for development
    if background:
        pid_file = get_dev_pid_file()
        
        # Check if already running
        if os.path.exists(pid_file):
            try:
                with open(pid_file, 'r') as f:
                    old_pid = int(f.read().strip())
                
                # Check if process is still running
                try:
                    os.kill(old_pid, 0)  # Test if process exists
                    print(f"⚠️  Development server already running (PID: {old_pid})")
                    print(f"   URL: http://{host}:{port}")
                    print(f"   Use 'ai2d_chat_dev server --stop' to stop it")
                    return
                except OSError:
                    # Process doesn't exist, remove stale PID file
                    os.remove(pid_file)
                    print("Removed stale PID file")
            except (ValueError, FileNotFoundError):
                # Invalid or missing PID file
                if os.path.exists(pid_file):
                    os.remove(pid_file)
        
        # Daemonize for background mode (Unix/Linux only)
        if os.name == 'posix':
            print("📦 Daemonizing development server...")
            daemonize_dev_server()
            
            # Write PID file after daemonizing
            with open(pid_file, 'w') as f:
                f.write(str(os.getpid()))
            print(f"✅ Development server started in background (PID: {os.getpid()})")
            print(f"   URL: http://{host}:{port}")
            print(f"   PID file: {pid_file}")
        else:
            print("⚠️  Background mode not supported on Windows, running in foreground")
            background = False
    
    # Import and start the Flask app with development settings
    try:
        from app import create_app
        app = create_app(debug=True, auto_initialize=True)
        
        # Enable development-specific features
        app.config['DEBUG'] = True
        app.config['TESTING'] = False
        app.config['ENV'] = 'development'
        
        # Get the SocketIO instance from app_globals (which is set by create_app)
        from app_globals import socketio
        
        # Set up signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logging.info(f"Development server received signal {signum}, shutting down...")
            
            # Clean up PID file
            if background:
                pid_file = get_dev_pid_file()
                if os.path.exists(pid_file):
                    try:
                        os.remove(pid_file)
                        logging.info("Development PID file removed")
                    except Exception as e:
                        logging.error(f"Failed to remove development PID file: {e}")
            
            logging.info("Development server shutdown complete")
            sys.exit(0)
        
        # Register signal handlers
        import signal
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        # Start server WITHOUT reloader to prevent duplicate initialization
        socketio.run(app, 
                    host=host, 
                    port=port, 
                    debug=False,  # Disable Flask debug mode to prevent reloader
                    use_reloader=False,  # Explicitly disable reloader
                    log_output=True)
        
    except Exception as e:
        logging.error(f"Failed to start development server: {e}")
        print(f"❌ Server startup failed: {e}")
        sys.exit(1)

def get_dev_pid_file():
    """Get the PID file path for development server"""
    pid_dir = os.path.expanduser("~/.local/share/ai2d_chat/run")
    os.makedirs(pid_dir, exist_ok=True)
    return os.path.join(pid_dir, "ai2d_chat_dev.pid")

def daemonize_dev_server():
    """Daemonize the development server process (Unix/Linux only)"""
    try:
        # First fork
        pid = os.fork()
        if pid > 0:
            # Parent process - exit
            sys.exit(0)
    except OSError as e:
        logging.error(f"Development server fork #1 failed: {e}")
        sys.exit(1)
    
    # Become session leader
    os.setsid()
    
    # Second fork
    try:
        pid = os.fork()
        if pid > 0:
            # Parent process - exit
            sys.exit(0)
    except OSError as e:
        logging.error(f"Development server fork #2 failed: {e}")
        sys.exit(1)
    
    # Change working directory to project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    
    # Set file creation mask
    os.umask(0)

def stop_development_server():
    """Stop the running development server"""
    pid_file = get_dev_pid_file()
    
    if not os.path.exists(pid_file):
        print("⚠️  No development server PID file found")
        print("   Development server may not be running")
        return
    
    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        
        # Try to kill the process
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"✅ Development server stopped (PID: {pid})")
            
            # Wait a moment and check if it's really stopped
            import time
            time.sleep(2)
            
            try:
                os.kill(pid, 0)  # Test if process still exists
                print("⚠️  Process still running, forcing termination...")
                os.kill(pid, signal.SIGKILL)
                time.sleep(1)
                print("✅ Development server force-stopped")
            except OSError:
                # Process is gone
                pass
                
        except OSError:
            print("⚠️  Development server process not found (may have already stopped)")
        
        # Remove PID file
        os.remove(pid_file)
        print("🗑️  PID file removed")
        
    except (ValueError, FileNotFoundError) as e:
        print(f"❌ Error reading PID file: {e}")
        if os.path.exists(pid_file):
            os.remove(pid_file)
            print("🗑️  Invalid PID file removed")

def check_development_server_status():
    """Check the status of the development server"""
    pid_file = get_dev_pid_file()
    
    if not os.path.exists(pid_file):
        print("📊 Development Server Status: STOPPED")
        print("   No PID file found")
        return
    
    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        
        # Check if process is running
        try:
            os.kill(pid, 0)  # Test if process exists
            print("📊 Development Server Status: RUNNING")
            print(f"   PID: {pid}")
            print(f"   PID file: {pid_file}")
            
            # Try to get port and host info
            try:
                from config.config_manager import ConfigManager
                config_manager = ConfigManager()
                config = config_manager.load_config()
                
                # Extract dev_port and host from config
                server_config = config.get('server', {})
                port = server_config.get('dev_port', 19081)
                host = server_config.get('host', '0.0.0.0')
                print(f"   URL: http://{host}:{port}")
                    
            except Exception:
                print(f"   URL: http://0.0.0.0:19081 (default)")

        except OSError:
            print("📊 Development Server Status: STOPPED")
            print(f"   Stale PID file found (PID {pid} not running)")
            print("   Use 'ai2d_chat_dev server --stop' to clean up PID file")
        
    except (ValueError, FileNotFoundError) as e:
        print("📊 Development Server Status: UNKNOWN")
        print(f"   Error reading PID file: {e}")
        print("   Use 'ai2d_chat_dev server --stop' to clean up invalid PID file")

def run_development_tests():
    """Run development tests"""
    print("🧪 Running Development Tests...")
    
    # Test TTS system
    try:
        from models.tts_handler import EmotionalTTSHandler
        tts = EmotionalTTSHandler()
        
        print("Testing TTS initialization...")
        if tts.initialize_model():
            print("✅ TTS model initialized successfully")
            
            # Test synthesis
            print("Testing TTS synthesis...")
            audio = tts.synthesize_emotional_speech("Hello, this is a test!", "happy", 0.7)
            if audio is not None:
                print(f"✅ TTS synthesis successful - generated {len(audio)} samples")
            else:
                print("❌ TTS synthesis failed")
        else:
            print("❌ TTS model failed to initialize")
            
    except Exception as e:
        print(f"❌ TTS test failed: {e}")
    
    # Test Live2D system
    try:
        from databases.live2d_models_separated import Live2DModelManager
        live2d = Live2DModelManager()
        models = live2d.get_available_models()
        print(f"✅ Live2D models available: {len(models)}")
        
    except Exception as e:
        print(f"❌ Live2D test failed: {e}")
    
    print("🏁 Development tests completed")

def reset_development_environment():
    """Reset development databases and configurations"""
    print("🔄 Resetting Development Environment...")
    
    try:
        # Reset databases
        from init_databases import main as init_db
        init_db()
        print("✅ Databases reset")
        
        # Clear logs
        log_files = ['ai2d_chat_dev.log', 'ai2d_chat.log']
        for log_file in log_files:
            if os.path.exists(log_file):
                os.remove(log_file)
                print(f"✅ Cleared {log_file}")
        
        print("🏁 Development environment reset completed")
        
    except Exception as e:
        print(f"❌ Reset failed: {e}")

def start_debug_mode():
    """Start with maximum debugging enabled"""
    print("🐛 Starting Debug Mode...")
    
    # Set maximum debug level
    os.environ['AI2D_DEBUG_LEVEL'] = 'TRACE'
    os.environ['FLASK_DEBUG'] = '1'
    
    # Start with debugging - use None for host and port to read from config
    start_development_server(None, None)

if __name__ == '__main__':
    main()
