#!/usr/bin/env python3
"""
AI Companion CLI Interface

Provides command-line access to AI Companion functionality including
server management, API documentation, and system utilities.
"""

import argparse
import sys
import json
import os
from typing import Dict, Any, List, Optional
import subprocess
import signal
import time

try:
    from __version__ import __version__, get_version_info, get_version_string, API_VERSION_FULL
except ImportError:
    try:
        from .__version__ import __version__, get_version_info, get_version_string, API_VERSION_FULL
    except ImportError:
        # Fallback for development
        __version__ = "0.4.0"
        API_VERSION_FULL = "1.0.0"
        def get_version_info():
            return {"version": __version__, "api_version": API_VERSION_FULL}
        def get_version_string():
            return f"AI Companion v{__version__}"


def get_config_defaults():
    """Get default configuration values for CLI argument defaults."""
    try:
        from .config.config_manager import ConfigManager
    except ImportError:
        try:
            from config.config_manager import ConfigManager
        except ImportError:
            try:
                # For installed package
                from src.config.config_manager import ConfigManager
            except ImportError:
                # Return hardcoded fallbacks if config manager not available
                return {'host': 'localhost', 'port': 4011}
    
    try:
        manager = ConfigManager()
        config = manager.load_config()
        server_config = config.get('server', {})
        return {
            'host': server_config.get('host', 'localhost'),
            'port': server_config.get('port', 4011)
        }
    except Exception:
        # Return hardcoded fallbacks if config loading fails
        return {'host': 'localhost', 'port': 4011}


class AICompanionCLI:
    """Main CLI interface for AI Companion."""
    
    def __init__(self):
        self.server_process = None
        
    def get_api_endpoints(self) -> Dict[str, Any]:
        """Return comprehensive API documentation."""
        # Get config defaults for base URL
        config_defaults = get_config_defaults()
        base_url = f"http://{config_defaults['host']}:{config_defaults['port']}"
        
        return {
            "version": API_VERSION_FULL,
            "base_url": base_url,
            "endpoints": {
                "chat": {
                    "url": "/api/chat",
                    "methods": ["POST"],
                    "description": "Send chat messages to AI live2d chat",
                    "parameters": {
                        "message": "string - The user message",
                        "conversation_id": "string - Optional conversation ID"
                    },
                    "response": {
                        "reply": "string - AI response",
                        "conversation_id": "string - Conversation identifier",
                        "emotion": "string - Detected emotion",
                        "timestamp": "string - Response timestamp"
                    }
                },
                "tts": {
                    "url": "/api/tts",
                    "methods": ["POST"],
                    "description": "Convert text to speech with emotional TTS",
                    "parameters": {
                        "text": "string - Text to synthesize",
                        "emotion": "string - Emotion for TTS (optional)",
                        "voice": "string - Voice model (optional)"
                    },
                    "response": {
                        "audio_url": "string - URL to audio file",
                        "duration": "float - Audio duration in seconds"
                    }
                },
                "live2d": {
                    "models": {
                        "url": "/api/live2d/models",
                        "methods": ["GET"],
                        "description": "List available Live2D models",
                        "response": {
                            "models": "array - List of available models",
                            "count": "integer - Number of models"
                        }
                    },
                    "load": {
                        "url": "/api/live2d/load",
                        "methods": ["POST"],
                        "description": "Load a specific Live2D model",
                        "parameters": {
                            "model_name": "string - Name of model to load"
                        }
                    },
                    "motion": {
                        "url": "/api/live2d/motion",
                        "methods": ["POST"],
                        "description": "Trigger Live2D model motion",
                        "parameters": {
                            "motion_group": "string - Motion group name",
                            "motion_index": "integer - Motion index (optional)",
                            "priority": "integer - Motion priority (optional)"
                        }
                    },
                    "expression": {
                        "url": "/api/live2d/expression",
                        "methods": ["POST"],
                        "description": "Set Live2D model expression",
                        "parameters": {
                            "expression_id": "string - Expression identifier"
                        }
                    }
                },
                "audio": {
                    "record": {
                        "url": "/api/audio/record",
                        "methods": ["POST"],
                        "description": "Start/stop audio recording",
                        "parameters": {
                            "action": "string - 'start' or 'stop'"
                        }
                    },
                    "upload": {
                        "url": "/api/audio/upload",
                        "methods": ["POST"],
                        "description": "Upload audio file for processing",
                        "parameters": {
                            "audio": "file - Audio file to process"
                        },
                        "response": {
                            "transcript": "string - Speech-to-text result",
                            "confidence": "float - Recognition confidence"
                        }
                    }
                },
                "system": {
                    "status": {
                        "url": "/api/system/status",
                        "methods": ["GET"],
                        "description": "Get system status and health",
                        "response": {
                            "status": "string - System status",
                            "uptime": "float - Server uptime in seconds",
                            "memory_usage": "object - Memory statistics",
                            "models_loaded": "array - Currently loaded models"
                        }
                    },
                    "version": {
                        "url": "/api/system/version",
                        "methods": ["GET"],
                        "description": "Get version information",
                        "response": get_version_info()
                    }
                }
            },
            "websocket": {
                "url": f"ws://{config_defaults['host']}:{config_defaults['port']}/socket.io/",
                "events": {
                    "chat_response": "Receive AI chat responses",
                    "motion_trigger": "Receive Live2D motion triggers",
                    "audio_status": "Receive audio processing status",
                    "system_status": "Receive system status updates"
                }
            },
            "authentication": {
                "type": "None",
                "description": "Currently no authentication required for local deployment"
            },
            "rate_limits": {
                "chat": "10 requests/minute",
                "tts": "5 requests/minute",
                "audio_upload": "20 MB max file size"
            }
        }
    
    def print_api_list(self, format_type: str = "text"):
        """Print API endpoints in specified format."""
        api_docs = self.get_api_endpoints()
        
        if format_type == "json":
            print(json.dumps(api_docs, indent=2))
        elif format_type == "yaml":
            try:
                import yaml
                print(yaml.dump(api_docs, default_flow_style=False))
            except ImportError:
                print("YAML format requires PyYAML. Install with: pip install PyYAML")
                print("Falling back to JSON format:")
                print(json.dumps(api_docs, indent=2))
        else:  # text format
            print(f"\n🤖 {get_version_string()}")
            print("=" * 60)
            print(f"Base URL: {api_docs['base_url']}")
            print(f"API Version: {api_docs['version']}")
            print("\n📋 Available Endpoints:")
            print("-" * 40)
            
            for category, endpoints in api_docs["endpoints"].items():
                print(f"\n📁 {category.upper()}")
                if isinstance(endpoints, dict) and "url" in endpoints:
                    # Single endpoint
                    endpoints = {"main": endpoints}
                
                for name, endpoint in endpoints.items():
                    if isinstance(endpoint, dict) and "url" in endpoint:
                        methods = ", ".join(endpoint.get("methods", ["GET"]))
                        print(f"  • {endpoint['url']} ({methods})")
                        print(f"    {endpoint.get('description', 'No description')}")
            
            print(f"\n🔌 WebSocket: {api_docs['websocket']['url']}")
            print("\n📖 For detailed API documentation, use: ai2d_chat api --format json")
    
    def check_and_download_models(self):
        """Check and download ALL required models during server startup."""
        print("🔍 Checking and downloading AI models...")
        print("💡 NOTE: All models MUST be downloaded at startup for reliable operation.")
        print("🔧 Starting comprehensive model download process...")
        
        try:
            # Use local imports to avoid circular dependencies and keep CLI fast
            try:
                from utils.model_downloader import ModelDownloader
                from utils.system_detector import SystemDetector
            except ImportError:
                from src.utils.model_downloader import ModelDownloader
                from src.utils.system_detector import SystemDetector
            
            system_detector = SystemDetector()
            downloader = ModelDownloader()
            
            # Get system-appropriate models
            recommended_models = downloader.get_recommended_models()
            
            # Show system info
            sys_info = system_detector.get_system_info()
            print(f"💻 System: {sys_info['platform']} {sys_info['architecture']}")
            print(f"🧠 RAM: {sys_info['total_memory_gb']:.1f} GB")
            print(f"🎯 Performance Tier: {sys_info.get('performance_tier', 'standard')}")
            
            if sys_info.get('cuda_available'):
                print(f"🚀 CUDA GPU: {sys_info.get('cuda_device_name', 'Available')}")
            
            print(f"\n📋 Required models for your system:")
            for model_type, variant in recommended_models.items():
                print(f"  • {model_type}: {variant}")
            
            # Check which models need downloading
            models_to_download = []
            models_already_downloaded = []
            
            for model_type, variant in recommended_models.items():
                if not downloader.check_model_exists(model_type, variant):
                    models_to_download.append((model_type, variant))
                else:
                    models_already_downloaded.append((model_type, variant))
            
            # Show status of already downloaded models
            if models_already_downloaded:
                print(f"\n✅ Already downloaded ({len(models_already_downloaded)} models):")
                for model_type, variant in models_already_downloaded:
                    print(f"  • {model_type}/{variant}")
            
            if not models_to_download:
                print("\n🎉 All required models are present!")
                return True
            
            print(f"\n📥 DOWNLOADING {len(models_to_download)} required models...")
            print("⚠️  Server startup requires ALL models to be downloaded.")
            print("💡 This may take several minutes depending on your internet connection.")
            
            successful_downloads = []
            failed_downloads = []
            
            # Download models with progress
            for i, (model_type, variant) in enumerate(models_to_download, 1):
                print(f"\n📦 [{i}/{len(models_to_download)}] Downloading {model_type}/{variant}...")
                
                def progress_callback(current, total, desc=""):
                    if total > 0:
                        percentage = (current / total) * 100
                        bar_length = 40
                        filled_length = int(bar_length * current // total)
                        bar = '█' * filled_length + '▒' * (bar_length - filled_length)
                        print(f"\r    [{bar}] {percentage:.1f}% {desc}", end='', flush=True)
                
                try:
                    model_info = downloader.model_registry.get(model_type, {}).get(variant, {})
                    estimated_size = model_info.get('size_mb', 0)
                    
                    if estimated_size > 0:
                        print(f"    📏 Estimated size: {estimated_size} MB")
                    
                    success = downloader.download_model(model_type, variant, progress_callback)
                    
                    if success:
                        print(f"\n    ✅ {model_type}/{variant} downloaded successfully")
                        successful_downloads.append((model_type, variant))
                    else:
                        print(f"\n    ❌ {model_type}/{variant} download FAILED")
                        failed_downloads.append((model_type, variant))
                        
                except Exception as e:
                    print(f"\n    ❌ Error downloading {model_type}/{variant}: {e}")
                    failed_downloads.append((model_type, variant))
            
            # Final report
            print("\n" + "="*60)
            print("📊 Download Results:")
            print(f"  ✅ Successful: {len(successful_downloads)}")
            print(f"  ❌ Failed:     {len(failed_downloads)}")
            
            if failed_downloads:
                print("\n⚠️  CRITICAL: Some models failed to download:")
                for model_type, variant in failed_downloads:
                    print(f"    • {model_type}/{variant}")
                print("\n💡 Server cannot start without all required models.")
                print("🔄 Please check your internet connection and try again.")
                return False
            else:
                print("\n🎉 All required models downloaded successfully!")
                
                # ADDITIONAL: Download Live2D models and setup databases
                print("\n📦 Setting up additional components...")
                
                # Download Live2D models
                try:
                    print("🎭 Installing Live2D models...")
                    try:
                        from utils.live2d_model_installer import Live2DModelInstaller
                    except ImportError:
                        from src.utils.live2d_model_installer import Live2DModelInstaller
                    
                    live2d_installer = Live2DModelInstaller()
                    live2d_results = live2d_installer.install_all_models()
                    successful_live2d = sum(1 for success in live2d_results.values() if success)
                    total_live2d = len(live2d_results)
                    print(f"🎭 Live2D models: {successful_live2d}/{total_live2d} successful")
                    
                    if successful_live2d < total_live2d:
                        failed_live2d = [name for name, success in live2d_results.items() if not success]
                        print(f"⚠️  Failed Live2D models: {', '.join(failed_live2d)}")
                        
                except Exception as e:
                    print(f"⚠️  Live2D installation error: {e}")
                
                # Initialize databases
                try:
                    print("💾 Initializing databases...")
                    try:
                        from databases.db_manager import DBManager
                    except ImportError:
                        from src.databases.db_manager import DBManager
                    
                    db_manager = DBManager()
                    print("✅ Database manager initialized")
                    
                except Exception as e:
                    print(f"⚠️  Database initialization error: {e}")
                
                return True
            
        except ImportError as e:
            print(f"❌ CRITICAL: Model management modules not found: {e}")
            print("💡 Cannot proceed without core modules. Check your installation.")
            return False
        except Exception as e:
            print(f"❌ CRITICAL: An unexpected error occurred during model check: {e}")
            print("💡 Aborting server startup.")
            return False

    def start_server(self, port: int = None, host: str = None, dev: bool = False):
        """Start the AI Companion server."""
        
        # Load config to get default values if not provided
        try:
            from .config.config_manager import ConfigManager
        except ImportError:
            try:
                from config.config_manager import ConfigManager
            except ImportError:
                # For installed package
                from src.config.config_manager import ConfigManager
        
        # Get configuration values with fallbacks
        try:
            manager = ConfigManager()
            config = manager.load_config()
            server_config = config.get('server', {})
            
            # Use config defaults if values not provided via CLI
            if port is None:
                port = server_config.get('port', 4011)
            if host is None:
                host = server_config.get('host', 'localhost')
                
        except Exception as e:
            print(f"⚠️  Warning: Could not load config ({e}), using hardcoded defaults")
            if port is None:
                port = 4011
            if host is None:
                host = 'localhost'
        
        print(f"🚀 Starting AI Companion Server on {host}:{port}")
        print("=" * 60)
        
        # Step 1: Check and download models (skip in dev mode)
        if dev:
            print("📋 Step 1: Skipping model checks (dev mode)")
            print("⚠️  WARNING: Running in dev mode - models may not be available")
        else:
            print("📋 Step 1: Preparing AI models...")
            models_ready = self.check_and_download_models()
            
            if not models_ready:
                print("\n❌ Aborting server startup due to model download failure.")
                sys.exit(1)
        
        # Step 2: Import and start the Flask app
        print("\n🔧 Step 2: Loading AI Companion modules...")
        try:
            # Use local imports to avoid loading heavy modules unless needed
            import os
            
            # Add src directory to path for packaged execution
            # This assumes cli.py is at the root of the package
            src_path = os.path.join(os.path.dirname(__file__), 'src')
            if src_path not in sys.path:
                sys.path.insert(0, src_path)

            # For development, handle the case where cli.py is at the project root
            if not os.path.exists(src_path):
                 src_path = os.path.join(os.path.dirname(__file__))
                 if src_path not in sys.path:
                    sys.path.insert(0, src_path)

            try:
                from app import app, socketio
            except ImportError:
                from src.app import app, socketio
            
            print("✅ AI Companion modules loaded successfully.")
            
            # Step 3: Start server
            print("\n🌐 Step 3: Starting web server...")
            print(f"   - Live2D: http://{host}:{port}/live2d")
            print(f"   - Chat:   http://{host}:{port}/")
            print(f"   - API:    http://{host}:{port}/api/docs")
            print(f"   - Status: http://{host}:{port}/status")
            print("\n⚡ Press Ctrl+C to stop the server.")
            print("=" * 60)
            
            # Set environment
            if dev:
                os.environ['FLASK_ENV'] = 'development'
                app.debug = True
                print("🛠️  Development mode enabled.")
            
            # Start server
            socketio.run(
                app,
                host=host,
                port=port,
                debug=dev,
                allow_unsafe_werkzeug=True
            )
            
        except ImportError as e:
            print(f"❌ Failed to import AI Companion modules: {e}")
            print("\n💡 Troubleshooting:")
            print("   1. Ensure you are in the project root directory.")
            print("   2. Install dependencies: pip install -e .")
            print(f"   3. Missing module details: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            sys.exit(1)
    
    def stop_server(self):
        """Stop the AI Companion server."""
        if self.server_process:
            print("🛑 Stopping AI Companion Server...")
            self.server_process.terminate()
            self.server_process.wait()
            print("✅ Server stopped")
        else:
            print("ℹ️  No server process found")
    
    def shutdown_servers(self, force=False):
        """Shutdown all running AI Companion servers."""
        import subprocess
        import time
        
        print("🔍 Searching for running AI Companion servers...")
        
        try:
            # Find AI live2d chat processes
            result = subprocess.run(
                ["ps", "aux"], 
                capture_output=True, 
                text=True
            )
            
            ai_processes = []
            for line in result.stdout.split('\n'):
                if 'ai2d_chat server' in line and 'grep' not in line:
                    parts = line.split()
                    if len(parts) > 1:
                        pid = parts[1]
                        ai_processes.append(pid)
            
            if not ai_processes:
                print("ℹ️  No running AI Companion servers found")
                return
            
            print(f"🎯 Found {len(ai_processes)} running AI Companion server(s)")
            
            for pid in ai_processes:
                print(f"🛑 Stopping server (PID: {pid})...")
                try:
                    if force:
                        subprocess.run(["kill", "-9", pid], check=True)
                        print(f"   ✅ Force killed process {pid}")
                    else:
                        subprocess.run(["kill", "-TERM", pid], check=True)
                        print(f"   ✅ Sent shutdown signal to process {pid}")
                except subprocess.CalledProcessError:
                    print(f"   ❌ Failed to stop process {pid}")
            
            if not force:
                print("⏳ Waiting for graceful shutdown...")
                time.sleep(2)
                
                # Check if processes are still running
                result = subprocess.run(
                    ["ps", "aux"], 
                    capture_output=True, 
                    text=True
                )
                
                still_running = []
                for line in result.stdout.split('\n'):
                    if 'ai2d_chat server' in line and 'grep' not in line:
                        parts = line.split()
                        if len(parts) > 1:
                            still_running.append(parts[1])
                
                if still_running:
                    print(f"⚠️  {len(still_running)} process(es) still running. Use --force to kill them.")
                else:
                    print("✅ All servers shutdown successfully")
            else:
                print("✅ All servers force-stopped")
                
        except Exception as e:
            print(f"❌ Error during shutdown: {e}")
            if not force:
                print("💡 Try using --force flag for forceful shutdown")
    
    def show_status(self):
        """Show system status."""
        print(f"📊 {get_version_string()}")
        print("=" * 50)
        
        # Get config defaults for status check URL
        config_defaults = get_config_defaults()
        status_url = f"http://{config_defaults['host']}:{config_defaults['port']}/api/system/status"
        
        # Check if server is running
        try:
            import requests
            response = requests.get(status_url, timeout=2)
            if response.status_code == 200:
                status = response.json()
                print("🟢 Server Status: RUNNING")
                print(f"🌐 Server URL: {config_defaults['host']}:{config_defaults['port']}")
                print(f"📈 Uptime: {status.get('uptime', 'Unknown')} seconds")
                print(f"🧠 Models Loaded: {len(status.get('models_loaded', []))}")
            else:
                print("🟡 Server Status: ACCESSIBLE (Non-200 response)")
        except:
            print("🔴 Server Status: NOT RUNNING")
        
        # Show version info
        version_info = get_version_info()
        print(f"\n📦 Version: {version_info['version']}")
        print(f"🔌 API Version: {version_info['api_version']}")
        
        if 'components' in version_info:
            print("\n🔧 Component Versions:")
            for component, version in version_info['components'].items():
                print(f"  • {component}: {version}")

    def handle_live2d_command(self, args):
        """Handle Live2D model management commands."""
        try:
            from utils.live2d_model_installer import Live2DModelInstaller
        except ImportError:
            from src.utils.live2d_model_installer import Live2DModelInstaller
        
        installer = Live2DModelInstaller()
        
        if args.live2d_action == "install":
            print("🎭 Installing all Live2D models...")
            results = installer.install_all_models()
            successful = sum(1 for success in results.values() if success)
            total = len(results)
            print(f"✅ Successfully installed {successful}/{total} models")
            
            if successful < total:
                failed = [name for name, success in results.items() if not success]
                print(f"❌ Failed models: {', '.join(failed)}")
        
        elif args.live2d_action == "refresh":
            print("🔄 Refreshing Live2D models...")
            results = installer.refresh_models()
            print(f"✅ Refresh complete:")
            print(f"   • New models installed: {results['new_installed']}")
            print(f"   • Models updated: {results['updated']}")
            if results['errors'] > 0:
                print(f"   • Errors: {results['errors']}")
        
        elif args.live2d_action == "list":
            available = installer.get_available_models_from_project()
            installed = installer.get_installed_models()
            
            print(f"🎭 Live2D Models")
            print(f"================")
            print(f"📦 Available in project: {len(available)}")
            for model in available:
                status = "✅" if any(m["name"] == model["name"] for m in installed) else "⭕"
                print(f"   {status} {model['name']} ({model['size_mb']} MB)")
            
            print(f"\n💾 Installed in user directory: {len(installed)}")
            for model in installed:
                print(f"   ✅ {model['name']} ({model['size_mb']} MB)")
        
        elif args.live2d_action == "install-single":
            model_name = args.model_name
            print(f"🎭 Installing model: {model_name}")
            success = installer.install_model(model_name)
            print(f"{'✅' if success else '❌'} Model installation: {model_name}")

    def handle_tunnel_command(self, args):
        """Handle Cloudflare tunnel management commands."""
        if args.tunnel_action == "install":
            self.install_cloudflared(force=args.force)
        elif args.tunnel_action == "setup":
            self.setup_tunnel()
        elif args.tunnel_action == "start":
            self.start_tunnel()
        elif args.tunnel_action == "stop":
            self.stop_tunnel()
        elif args.tunnel_action == "status":
            self.tunnel_status()
        else:
            print("❌ Unknown tunnel action. Use: install, setup, start, stop, or status")

    def handle_systemd_command(self, args):
        """Handle systemd service management commands."""
        if args.systemd_action == "install":
            self.install_systemd_service(force=getattr(args, 'force', False))
        elif args.systemd_action == "uninstall":
            self.uninstall_systemd_service()
        elif args.systemd_action == "status":
            self.systemd_status()
        elif args.systemd_action == "start":
            self.start_systemd_service()
        elif args.systemd_action == "stop":
            self.stop_systemd_service()
        elif args.systemd_action == "restart":
            self.restart_systemd_service()
        elif args.systemd_action == "enable":
            self.enable_systemd_service()
        elif args.systemd_action == "disable":
            self.disable_systemd_service()
        else:
            print("❌ Unknown systemd action. Use: install, uninstall, status, start, stop, restart, enable, or disable")

    def handle_uninstall_command(self, args):
        """Handle uninstallation commands."""
        if getattr(args, 'complete', False):
            self.complete_uninstall(force=getattr(args, 'force', False))
        elif getattr(args, 'system', False):
            self.system_uninstall(force=getattr(args, 'force', False))
        else:
            self.basic_uninstall()

    def install_systemd_service(self, force: bool = False):
        """Install AI Companion as a systemd service."""
        print("🔧 Installing AI Companion systemd service...")
        
        # Check if service already exists
        service_path = "/etc/systemd/system/ai2d_chat.service"
        if os.path.exists(service_path) and not force:
            print(f"✅ Service already exists: {service_path}")
            print("💡 Use --force to reinstall the service")
            return True
        
        try:
            import getpass
            import shutil
            
            # Load configuration to get server settings
            try:
                from .config.config_manager import ConfigManager
            except ImportError:
                try:
                    from config.config_manager import ConfigManager
                except ImportError:
                    # For installed package
                    from src.config.config_manager import ConfigManager
            
            # Get configuration values
            try:
                manager = ConfigManager()
                config = manager.load_config()
                
                # Get server settings from config with fallbacks
                server_config = config.get('server', {})
                host = server_config.get('host', '0.0.0.0')
                port = server_config.get('port', 4011)
                
                # Get service settings from config with fallbacks
                service_config = config.get('service', {})
                service_user = service_config.get('user', getpass.getuser())
                working_dir = service_config.get('working_directory', f"/home/{getpass.getuser()}")
                restart_policy = service_config.get('restart_policy', 'on-failure')
                auto_start = service_config.get('auto_start', False)
                
                # Expand tilde in working directory
                if working_dir.startswith('~'):
                    working_dir = os.path.expanduser(working_dir)
                
                print(f"📋 Using configuration values:")
                print(f"   🌐 Host: {host}")
                print(f"   🔌 Port: {port}")
                print(f"   👤 User: {service_user}")
                print(f"   📁 Working directory: {working_dir}")
                print(f"   🔄 Restart policy: {restart_policy}")
                
            except Exception as e:
                print(f"⚠️  Warning: Could not load config ({e}), using defaults")
                host = '0.0.0.0'
                port = 4011
                service_user = getpass.getuser()
                working_dir = f"/home/{service_user}"
                restart_policy = 'on-failure'
                auto_start = False
            
            # Get current user and ai2d_chat executable path
            current_user = getpass.getuser()
            
            # Find ai2d_chat executable
            ai2d_chat_path = shutil.which('ai2d_chat')
            if not ai2d_chat_path:
                print("❌ ai2d_chat executable not found in PATH")
                print("💡 Make sure ai2d_chat is installed via pipx")
                return False
            
            # Create service file content with config values
            service_content = f"""[Unit]
Description=AI Companion Server
After=network.target
Wants=network.target

[Service]
Type=simple
User={service_user}
Group={service_user}
WorkingDirectory={working_dir}
Environment=PATH=/home/{service_user}/.local/bin:/usr/local/bin:/usr/bin:/bin
ExecStart={ai2d_chat_path} server --host {host} --port {port}
Restart={restart_policy}
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ai2d_chat

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/home/{service_user}/.local/share/ai2d_chat
ReadWritePaths=/home/{service_user}/.config/ai2d_chat
ReadWritePaths=/home/{service_user}/.cache/ai2d_chat

[Install]
WantedBy=multi-user.target
"""
            
            # Write service file
            print(f"📝 Creating service file: {service_path}")
            with open('/tmp/ai2d_chat.service', 'w') as f:
                f.write(service_content)
            
            # Install service file with sudo
            subprocess.run(['sudo', 'cp', '/tmp/ai2d_chat.service', service_path], check=True)
            subprocess.run(['sudo', 'chmod', '644', service_path], check=True)
            subprocess.run(['rm', '/tmp/ai2d_chat.service'], check=True)
            
            # Reload systemd
            subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
            
            # Auto-enable if configured
            if auto_start:
                print("🔄 Auto-enabling service (configured in config.yaml)...")
                try:
                    subprocess.run(['sudo', 'systemctl', 'enable', 'ai2d_chat'], check=True)
                    print("✅ Service enabled for auto-start on boot")
                except subprocess.CalledProcessError as e:
                    print(f"⚠️  Warning: Could not auto-enable service: {e}")
            
            print("✅ Systemd service installed successfully")
            print(f"📍 Service file: {service_path}")
            print(f"👤 Running as user: {service_user}")
            print(f"🚀 Executable: {ai2d_chat_path}")
            print(f"🌐 Server address: {host}:{port}")
            print(f"📁 Working directory: {working_dir}")
            print(f"🔄 Restart policy: {restart_policy}")
            
            print("\n🎯 Next steps:")
            if auto_start:
                print("   ✅ Auto-start enabled (configured in config)")
                print("   • ai2d_chat systemd start     # Start the service now")
            else:
                print("   • ai2d_chat systemd enable    # Enable auto-start on boot")
                print("   • ai2d_chat systemd start     # Start the service now")
            print("   • ai2d_chat systemd status    # Check service status")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install systemd service: {e}")
            return False
        except Exception as e:
            print(f"❌ Installation error: {e}")
            return False

    def uninstall_systemd_service(self):
        """Uninstall AI Companion systemd service."""
        print("🗑️  Uninstalling AI Companion systemd service...")
        
        service_path = "/etc/systemd/system/ai2d_chat.service"
        
        if not os.path.exists(service_path):
            print("ℹ️  Systemd service not installed")
            return True
        
        try:
            # Stop and disable service first
            print("⏹️  Stopping service...")
            subprocess.run(['sudo', 'systemctl', 'stop', 'ai2d_chat'], capture_output=True)
            
            print("❌ Disabling service...")
            subprocess.run(['sudo', 'systemctl', 'disable', 'ai2d_chat'], capture_output=True)
            
            # Remove service file
            print(f"🗑️  Removing service file: {service_path}")
            subprocess.run(['sudo', 'rm', service_path], check=True)
            
            # Reload systemd
            subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
            subprocess.run(['sudo', 'systemctl', 'reset-failed'], capture_output=True)
            
            print("✅ Systemd service uninstalled successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to uninstall systemd service: {e}")
            return False
        except Exception as e:
            print(f"❌ Uninstallation error: {e}")
            return False

    def systemd_status(self):
        """Show systemd service status."""
        print("📊 AI Companion Systemd Service Status")
        print("=====================================")
        
        service_path = "/etc/systemd/system/ai2d_chat.service"
        
        # Check if service file exists
        if os.path.exists(service_path):
            print(f"✅ Service file: {service_path}")
        else:
            print("❌ Service file not found")
            print("💡 Run 'ai2d_chat systemd install' to install the service")
            return
        
        try:
            # Check service status
            result = subprocess.run(['systemctl', 'is-active', 'ai2d_chat'], 
                                  capture_output=True, text=True)
            active_status = result.stdout.strip()
            
            if active_status == "active":
                print("🟢 Service Status: ACTIVE")
            elif active_status == "inactive":
                print("🔴 Service Status: INACTIVE")
            elif active_status == "failed":
                print("🟡 Service Status: FAILED")
            else:
                print(f"🔄 Service Status: {active_status.upper()}")
            
            # Check if enabled
            result = subprocess.run(['systemctl', 'is-enabled', 'ai2d_chat'], 
                                  capture_output=True, text=True)
            enabled_status = result.stdout.strip()
            
            if enabled_status == "enabled":
                print("✅ Auto-start: ENABLED")
            else:
                print("❌ Auto-start: DISABLED")
            
            # Show recent logs
            print("\n📋 Recent logs (last 10 lines):")
            result = subprocess.run(['journalctl', '-u', 'ai2d_chat', '-n', '10', '--no-pager'], 
                                  capture_output=True, text=True)
            if result.stdout:
                print(result.stdout)
            else:
                print("   (No logs available)")
                
        except Exception as e:
            print(f"❌ Error checking service status: {e}")

    def start_systemd_service(self):
        """Start systemd service."""
        print("🚀 Starting AI Companion systemd service...")
        try:
            subprocess.run(['sudo', 'systemctl', 'start', 'ai2d_chat'], check=True)
            print("✅ Service started successfully")
            time.sleep(2)
            self.systemd_status()
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to start service: {e}")

    def stop_systemd_service(self):
        """Stop systemd service."""
        print("⏹️  Stopping AI Companion systemd service...")
        try:
            subprocess.run(['sudo', 'systemctl', 'stop', 'ai2d_chat'], check=True)
            print("✅ Service stopped successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to stop service: {e}")

    def restart_systemd_service(self):
        """Restart systemd service."""
        print("🔄 Restarting AI Companion systemd service...")
        try:
            subprocess.run(['sudo', 'systemctl', 'restart', 'ai2d_chat'], check=True)
            print("✅ Service restarted successfully")
            time.sleep(2)
            self.systemd_status()
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to restart service: {e}")

    def enable_systemd_service(self):
        """Enable systemd service for auto-start."""
        print("✅ Enabling AI Companion service for auto-start...")
        try:
            subprocess.run(['sudo', 'systemctl', 'enable', 'ai2d_chat'], check=True)
            print("✅ Service enabled for auto-start on boot")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to enable service: {e}")

    def disable_systemd_service(self):
        """Disable systemd service auto-start."""
        print("❌ Disabling AI Companion service auto-start...")
        try:
            subprocess.run(['sudo', 'systemctl', 'disable', 'ai2d_chat'], check=True)
            print("✅ Service disabled from auto-start")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to disable service: {e}")

    def basic_uninstall(self):
        """Basic uninstall - just remove pipx package."""
        print("🗑️  Basic AI Companion Uninstall")
        print("================================")
        
        try:
            # Check if installed
            result = subprocess.run(['pipx', 'list'], capture_output=True, text=True)
            if 'ai2d_chat' not in result.stdout:
                print("ℹ️  ai2d_chat not found in pipx installations")
                return
            
            print("📦 Uninstalling ai2d_chat package...")
            subprocess.run(['pipx', 'uninstall', 'ai2d_chat'], check=True)
            print("✅ AI Companion package uninstalled")
            
            print("\n💡 Note: User data and models are preserved")
            print("   Use 'ai2d_chat uninstall --complete' for full cleanup")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to uninstall package: {e}")
        except Exception as e:
            print(f"❌ Uninstall error: {e}")

    def system_uninstall(self, force: bool = False):
        """System uninstall - remove package and systemd service but keep user data."""
        print("🗑️  System AI Companion Uninstall")
        print("=================================")
        print("💡 Removing system components while preserving user data and models")
        
        if not force:
            try:
                confirmation = input("\nThis will remove:\n"
                                   "  • AI Companion package\n"
                                   "  • Systemd service (if installed)\n\n"
                                   "This will KEEP:\n"
                                   "  • Downloaded models\n"
                                   "  • Configuration files\n"
                                   "  • Conversation history\n\n"
                                   "Type 'REMOVE SYSTEM' to confirm: ")
                
                if confirmation != "REMOVE SYSTEM":
                    print("❌ Uninstall cancelled")
                    return
            except KeyboardInterrupt:
                print("\n❌ Uninstall cancelled")
                return
        
        print("\n🚀 Starting system uninstall...")
        
        try:
            # Stop systemd service if exists
            print("\n⏹️  Stopping systemd service...")
            try:
                subprocess.run(['sudo', 'systemctl', 'stop', 'ai2d_chat'], 
                             capture_output=True, timeout=10)
                print("   ✅ Service stopped")
            except:
                print("   ℹ️  No service to stop")
            
            # Remove systemd service
            print("\n🗑️  Removing systemd service...")
            try:
                self.uninstall_systemd_service()
                print("   ✅ Systemd service removed")
            except:
                print("   ℹ️  No systemd service to remove")
            
            # Uninstall pipx package
            print("\n📦 Uninstalling pipx package...")
            try:
                subprocess.run(['pipx', 'uninstall', 'ai2d_chat'], 
                             check=True, capture_output=True)
                print("   ✅ Package uninstalled")
            except subprocess.CalledProcessError:
                print("   ℹ️  Package not found or already uninstalled")
            
            print("\n✅ SYSTEM UNINSTALL COMPLETE")
            print("=" * 35)
            print("✅ AI Companion package removed")
            print("✅ Systemd service removed")
            print("💾 User data and models preserved")
            
            # Show preserved locations
            from pathlib import Path
            home = Path.home()
            preserved_dirs = [
                home / '.local' / 'share' / 'ai2d_chat',
                home / '.config' / 'ai2d_chat', 
                home / '.cache' / 'ai2d_chat'
            ]
            
            print("\n📁 Preserved directories:")
            for dir_path in preserved_dirs:
                if dir_path.exists():
                    # Calculate size
                    try:
                        size = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
                        size_mb = size / (1024 * 1024)
                        print(f"   📂 {dir_path} (~{size_mb:.1f} MB)")
                    except:
                        print(f"   📂 {dir_path}")
            
            print("\n💡 To completely remove all data, use: ai2d_chat uninstall --complete")
            
        except Exception as e:
            print(f"\n❌ Error during system uninstall: {e}")
            print("💡 You may need to manually remove remaining components")

    def complete_uninstall(self, force: bool = False):
        """Complete uninstall - remove everything including user data."""
        print("🗑️  COMPLETE AI Companion Uninstall")
        print("===================================")
        print("⚠️  WARNING: This will remove ALL AI Companion data!")
        
        if not force:
            try:
                confirmation = input("\nThis will delete:\n"
                                   "  • AI Companion package\n"
                                   "  • All downloaded models (~1-10 GB)\n"
                                   "  • Configuration files\n"
                                   "  • Conversation history\n"
                                   "  • Systemd service (if installed)\n\n"
                                   "Type 'DELETE EVERYTHING' to confirm: ")
                
                if confirmation != "DELETE EVERYTHING":
                    print("❌ Uninstall cancelled")
                    return
            except KeyboardInterrupt:
                print("\n❌ Uninstall cancelled")
                return
        
        print("\n🚀 Starting complete uninstall...")
        
        try:
            # Stop systemd service if exists
            print("\n⏹️  Stopping systemd service...")
            try:
                subprocess.run(['sudo', 'systemctl', 'stop', 'ai2d_chat'], 
                             capture_output=True, timeout=10)
                print("   ✅ Service stopped")
            except:
                print("   ℹ️  No service to stop")
            
            # Remove systemd service
            print("\n🗑️  Removing systemd service...")
            try:
                self.uninstall_systemd_service()
                print("   ✅ Systemd service removed")
            except:
                print("   ℹ️  No systemd service to remove")
            
            # Uninstall pipx package
            print("\n📦 Uninstalling pipx package...")
            try:
                subprocess.run(['pipx', 'uninstall', 'ai2d_chat'], 
                             check=True, capture_output=True)
                print("   ✅ Package uninstalled")
            except subprocess.CalledProcessError:
                print("   ℹ️  Package not found or already uninstalled")
            
            # Remove user data directories
            import shutil
            from pathlib import Path
            
            home = Path.home()
            dirs_to_remove = [
                home / '.local' / 'share' / 'ai2d_chat',
                home / '.config' / 'ai2d_chat', 
                home / '.cache' / 'ai2d_chat'
            ]
            
            total_size = 0
            for dir_path in dirs_to_remove:
                if dir_path.exists():
                    # Calculate size before deletion
                    try:
                        size = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
                        total_size += size
                    except:
                        pass
            
            if total_size > 0:
                size_mb = total_size / (1024 * 1024)
                print(f"\n🗑️  Removing user data directories (~{size_mb:.1f} MB)...")
                
                for dir_path in dirs_to_remove:
                    if dir_path.exists():
                        print(f"   • {dir_path}")
                        shutil.rmtree(dir_path)
                        print(f"     ✅ Removed")
                    else:
                        print(f"   • {dir_path} (not found)")
                
                print(f"\n✅ Freed {size_mb:.1f} MB of disk space")
            else:
                print("\n✅ No user data directories found")
            
            print("\n🎉 COMPLETE UNINSTALL FINISHED")
            print("=" * 40)
            print("✅ AI Companion completely removed from system")
            print("💾 All models and data have been deleted")
            print("🔧 Systemd service has been removed")
            print("📦 Package has been uninstalled")
            
        except Exception as e:
            print(f"\n❌ Error during complete uninstall: {e}")
            print("💡 You may need to manually remove remaining files")

    def install_cloudflared(self, force: bool = False):
        """Install cloudflared for tunnel functionality."""
        print("🌐 Installing Cloudflare Tunnel (cloudflared)...")
        
        # Check if already installed
        try:
            result = subprocess.run(['cloudflared', '--version'], capture_output=True, text=True)
            if result.returncode == 0 and not force:
                print(f"✅ cloudflared already installed: {result.stdout.strip()}")
                return True
        except FileNotFoundError:
            pass
        
        try:
            import platform
            system = platform.system().lower()
            
            if system == "linux":
                print("📦 Installing cloudflared for Linux...")
                subprocess.run([
                    'curl', '-L', '--output', '/tmp/cloudflared.deb',
                    'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb'
                ], check=True)
                subprocess.run(['sudo', 'dpkg', '-i', '/tmp/cloudflared.deb'], check=True)
                subprocess.run(['rm', '/tmp/cloudflared.deb'], check=True)
                
            elif system == "darwin":
                print("📦 Installing cloudflared for macOS...")
                subprocess.run(['brew', 'install', 'cloudflared'], check=True)
                
            else:
                print(f"❌ Automatic installation not supported for {system}")
                print("Please install cloudflared manually:")
                print("https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/")
                return False
                
            print("✅ cloudflared installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install cloudflared: {e}")
            return False
        except Exception as e:
            print(f"❌ Installation error: {e}")
            return False

    def setup_tunnel(self):
        """Setup Cloudflare tunnel configuration."""
        print("🔧 Setting up Cloudflare tunnel...")
        
        # Check if cloudflared is installed
        try:
            subprocess.run(['cloudflared', '--version'], capture_output=True, check=True)
        except FileNotFoundError:
            print("❌ cloudflared not found. Run 'ai2d_chat tunnel install' first")
            return False
        
        print("\n📋 Tunnel Setup Instructions:")
        print("=============================")
        print("\n1. First, authenticate with Cloudflare:")
        print("   cloudflared tunnel login")
        print("\n2. Create a tunnel:")
        print("   cloudflared tunnel create ai2d_chat")
        print("\n3. Configure the tunnel:")
        print("   Create ~/.cloudflared/config.yml with your tunnel ID")
        print("\n4. Route traffic through the tunnel:")
        print("   cloudflared tunnel route dns ai2d_chat your-domain.com")
        print("\n5. Test your tunnel:")
        print("   ai2d_chat tunnel start")
        
        print("\n💡 Example config.yml:")
        print("----------------------")
        config_example = """tunnel: YOUR_TUNNEL_ID
credentials-file: ~/.cloudflared/YOUR_TUNNEL_ID.json

ingress:
  - hostname: ai2d_chat.yourdomain.com
    service: http://localhost:19447
  - service: http_status:404"""
        print(config_example)
        
        return True

    def start_tunnel(self):
        """Start Cloudflare tunnel."""
        print("🚀 Starting Cloudflare tunnel...")
        
        try:
            # Check if cloudflared is installed
            subprocess.run(['cloudflared', '--version'], capture_output=True, check=True)
        except FileNotFoundError:
            print("❌ cloudflared not found. Run 'ai2d_chat tunnel install' first")
            return False
        
        # Check if config exists
        config_path = os.path.expanduser("~/.cloudflared/config.yml")
        if not os.path.exists(config_path):
            print("❌ Tunnel configuration not found at ~/.cloudflared/config.yml")
            print("💡 Run 'ai2d_chat tunnel setup' for configuration instructions")
            return False
        
        try:
            # Start tunnel in background
            process = subprocess.Popen(
                ['cloudflared', 'tunnel', 'run'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            
            # Give it a moment to start
            time.sleep(2)
            
            # Check if it's still running
            if process.poll() is None:
                print("✅ Cloudflare tunnel started successfully")
                print(f"📋 Process ID: {process.pid}")
                print("💡 Use 'ai2d_chat tunnel status' to check tunnel status")
                print("🛑 Use 'ai2d_chat tunnel stop' to stop the tunnel")
                return True
            else:
                stdout, stderr = process.communicate()
                print("❌ Failed to start tunnel")
                if stderr:
                    print(f"Error: {stderr.decode()}")
                return False
                
        except Exception as e:
            print(f"❌ Error starting tunnel: {e}")
            return False

    def stop_tunnel(self):
        """Stop Cloudflare tunnel."""
        print("🛑 Stopping Cloudflare tunnel...")
        
        try:
            # Find cloudflared processes
            result = subprocess.run(['pgrep', '-f', 'cloudflared.*tunnel.*run'], capture_output=True, text=True)
            
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        try:
                            subprocess.run(['kill', pid], check=True)
                            print(f"✅ Stopped tunnel process (PID: {pid})")
                        except subprocess.CalledProcessError:
                            print(f"❌ Failed to stop process {pid}")
                return True
            else:
                print("ℹ️  No running tunnel processes found")
                return True
                
        except Exception as e:
            print(f"❌ Error stopping tunnel: {e}")
            return False

    def tunnel_status(self):
        """Show Cloudflare tunnel status."""
        print("📊 Cloudflare Tunnel Status")
        print("===========================")
        
        # Check if cloudflared is installed
        try:
            result = subprocess.run(['cloudflared', '--version'], capture_output=True, text=True)
            print(f"✅ cloudflared installed: {result.stdout.strip()}")
        except FileNotFoundError:
            print("❌ cloudflared not installed")
            print("💡 Run 'ai2d_chat tunnel install' to install")
            return
        
        # Check for running processes
        try:
            result = subprocess.run(['pgrep', '-f', 'cloudflared.*tunnel.*run'], capture_output=True, text=True)
            
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                print(f"🚀 Running tunnel processes: {len(pids)}")
                for pid in pids:
                    if pid:
                        print(f"   • PID: {pid}")
            else:
                print("⏹️  No tunnel processes running")
                
        except Exception as e:
            print(f"❌ Error checking tunnel status: {e}")
        
        # Check config file
        config_path = os.path.expanduser("~/.cloudflared/config.yml")
        if os.path.exists(config_path):
            print(f"✅ Configuration file found: {config_path}")
        else:
            print(f"❌ Configuration file not found: {config_path}")
            print("💡 Run 'ai2d_chat tunnel setup' for setup instructions")

    def handle_setup_command(self, args):
        """Handle the setup command for AI Companion configuration."""
        print("🔧 AI Companion Setup")
        print("=====================")
        print("🔧 This will install configuration files and download all required models...")
        
        try:
            from .config.config_manager import ConfigManager
        except ImportError:
            try:
                from config.config_manager import ConfigManager
            except ImportError:
                # For installed package
                from src.config.config_manager import ConfigManager
            
        # Check if configuration already exists
        manager = ConfigManager()
        config_exists = manager.get_config_path().exists()
        secrets_exists = manager.get_secrets_path().exists()
        
        if config_exists and secrets_exists and not args.force:
            print("✅ Configuration files already exist:")
            print(f"   📝 Config: {manager.get_config_path()}")
            print(f"   🔑 Secrets: {manager.get_secrets_path()}")
            print("\n💡 Use --force to reinstall configuration")
            return
            
        if args.force:
            print("🔄 Force reinstalling configuration...")
            
        # Install configuration with clean database option
        clean_db = args.clean or args.force
        if clean_db:
            print("🗑️  Cleaning existing databases for fresh installation...")
            
        try:
            manager.install_configuration_files(clean_databases=clean_db)
            print("\n✅ Setup complete!")
            print(f"   📝 Config: {manager.get_config_path()}")
            print(f"   🔑 Secrets: {manager.get_secrets_path()}")
            
            # Show important security notes
            print("\n🔒 IMPORTANT SECURITY NOTES:")
            print("   1. Check your secrets file and update API keys as needed")
            print("   2. Change the auto-generated admin password immediately")
            print("   3. Set proper file permissions on secrets file")
            print(f"   4. Never commit {manager.get_secrets_path()} to version control")
            
            # Show next steps
            print("\n🚀 Next Steps:")
            print("   1. Update secrets file with your API keys")
            print("   2. Downloading AI models...")
            
            # Actually download models during setup
            print("\n🤖 Downloading required AI models...")
            models_ready = self.check_and_download_models()
            
            if models_ready:
                print("\n🎉 All models downloaded successfully!")
                print("   3. Run 'ai2d_chat server' to start the application")
            else:
                print("\n⚠️  Some models failed to download.")
                print("   3. Try 'ai2d_chat models --download' to retry model downloads")
                print("   4. Run 'ai2d_chat server' once all models are ready")
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return

    def show_models(self, list_models: bool = False, download_missing: bool = False):
        """Show model information and storage locations."""
        try:
            from utils.model_downloader import ModelDownloader, get_user_data_dir
        except ImportError:
            from src.utils.model_downloader import ModelDownloader, get_user_data_dir
        
        print("🧠 AI Companion Model Information")
        print("=" * 50)
        
        # Show storage paths
        data_dir = get_user_data_dir()
        print(f"\n📁 Model Storage Locations:")
        print(f"  • User Data Directory: {data_dir}")
        print(f"  • Models Directory: {data_dir / 'models'}")
        print(f"  • Cache Directory: {data_dir / 'cache'}")
        
        # Check if models exist
        models_exist = (data_dir / 'models').exists()
        cache_exists = (data_dir / 'cache').exists()
        print(f"\n📊 Directory Status:")
        print(f"  • Models Directory: {'✅ Exists' if models_exist else '❌ Not created yet'}")
        print(f"  • Cache Directory: {'✅ Exists' if cache_exists else '❌ Not created yet'}")
        
        # List available models
        if list_models:
            try:
                downloader = ModelDownloader()
                available_models = downloader.list_available_models()
                
                print(f"\n🎯 Available Models:")
                for model_type, variants in available_models.items():
                    print(f"\n  📦 {model_type.upper()} Models:")
                    for variant, downloaded in variants.items():
                        status = "✅ Downloaded" if downloaded else "⬇️  Available for download"
                        print(f"    • {variant}: {status}")
                        
                        if downloaded:
                            path = downloader.get_model_path(model_type, variant)
                            print(f"      📍 Path: {path}")
                
            except Exception as e:
                print(f"\n❌ Error checking models: {e}")
                print("💡 Models will be downloaded automatically when the server starts.")
        
        print(f"\n💡 Models are downloaded automatically when first needed.")
        print(f"📦 Total storage location: {get_user_data_dir()}")
        print(f"🗑️  To clear models: rm -rf {get_user_data_dir()}")
        
        # Handle download request
        if download_missing:
            print(f"\n📦 Starting model download process...")
            success = self.check_and_download_models()
            if success:
                print(f"\n✅ All models downloaded successfully!")
            else:
                print(f"\n⚠️  Some models failed to download. Check output above for details.")

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AI Companion - Interactive AI with Live2D Avatar",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Use 'ai2d_chat <command> --help' for more information on each command.
        """
    )
    
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=get_version_string()
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Get config defaults for server arguments
    config_defaults = get_config_defaults()
    
    # Server command
    server_parser = subparsers.add_parser("server", help="Start the AI Companion server")
    server_parser.add_argument("--port", "-p", type=int, default=config_defaults['port'], 
                              help=f"Port to run server on (default: {config_defaults['port']} from config)")
    server_parser.add_argument("--host", default=config_defaults['host'], 
                              help=f"Host to bind to (default: {config_defaults['host']} from config)")
    server_parser.add_argument("--dev", action="store_true", help="Run in development mode")
    
    # API documentation command
    api_parser = subparsers.add_parser("api", help="Show API documentation")
    api_parser.add_argument("--format", "-f", choices=["text", "json", "yaml"], default="text", help="Output format")
    
    # Status command
    subparsers.add_parser("status", help="Show system status")
    
    # Shutdown command
    shutdown_parser = subparsers.add_parser("shutdown", help="Shutdown running AI Companion servers")
    shutdown_parser.add_argument("--force", action="store_true", help="Force kill all AI live2d chat processes")
    shutdown_parser.add_argument("--all", action="store_true", help="Shutdown all AI live2d chat processes (same as --force)")
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Set up AI Companion configuration")
    setup_parser.add_argument("--clean", action="store_true", 
                             help="Clean existing databases for fresh installation")
    setup_parser.add_argument("--force", action="store_true",
                             help="Force reinstall configuration files")
    
    # Version command
    subparsers.add_parser("version", help="Show detailed version information")
    
    # Models command
    models_parser = subparsers.add_parser("models", help="Show model information and locations")
    models_parser.add_argument("--list", action="store_true", help="List all models")
    models_parser.add_argument("--download", action="store_true", help="Download missing models")
    
    # Live2D command
    live2d_parser = subparsers.add_parser("live2d", help="Live2D model management")
    live2d_subparsers = live2d_parser.add_subparsers(dest="live2d_action", help="Live2D actions")
    
    live2d_subparsers.add_parser("install", help="Install all Live2D models")
    live2d_subparsers.add_parser("refresh", help="Refresh Live2D models (install new/updated)")
    live2d_subparsers.add_parser("list", help="List available and installed Live2D models")
    
    install_parser = live2d_subparsers.add_parser("install-single", help="Install specific model")
    install_parser.add_argument("model_name", help="Name of model to install")
    
    # Tunnel command
    tunnel_parser = subparsers.add_parser("tunnel", help="Cloudflare tunnel management")
    tunnel_subparsers = tunnel_parser.add_subparsers(dest="tunnel_action", help="Tunnel actions")
    
    tunnel_subparsers.add_parser("start", help="Start Cloudflare tunnel")
    tunnel_subparsers.add_parser("stop", help="Stop Cloudflare tunnel")
    tunnel_subparsers.add_parser("status", help="Show tunnel status")
    tunnel_subparsers.add_parser("setup", help="Setup Cloudflare tunnel configuration")
    
    tunnel_install_parser = tunnel_subparsers.add_parser("install", help="Install cloudflared")
    tunnel_install_parser.add_argument("--force", action="store_true", help="Force reinstall cloudflared")
    
    # Systemd command
    systemd_parser = subparsers.add_parser("systemd", help="Systemd service management")
    systemd_subparsers = systemd_parser.add_subparsers(dest="systemd_action", help="Systemd actions")
    
    systemd_subparsers.add_parser("status", help="Show systemd service status")
    systemd_subparsers.add_parser("start", help="Start systemd service")
    systemd_subparsers.add_parser("stop", help="Stop systemd service")
    systemd_subparsers.add_parser("restart", help="Restart systemd service")
    systemd_subparsers.add_parser("enable", help="Enable service auto-start")
    systemd_subparsers.add_parser("disable", help="Disable service auto-start")
    systemd_subparsers.add_parser("uninstall", help="Uninstall systemd service")
    
    systemd_install_parser = systemd_subparsers.add_parser("install", help="Install systemd service")
    systemd_install_parser.add_argument("--force", action="store_true", help="Force reinstall service")
    
    # Uninstall command
    uninstall_parser = subparsers.add_parser("uninstall", help="Uninstall AI Companion")
    uninstall_parser.add_argument("--complete", action="store_true", 
                                 help="Complete uninstall including all user data and models")
    uninstall_parser.add_argument("--system", action="store_true",
                                 help="System uninstall - remove package and systemd service but keep user data")
    uninstall_parser.add_argument("--force", action="store_true",
                                 help="Skip confirmation prompts")
    
    args = parser.parse_args()
    
    cli = AICompanionCLI()
    
    if args.command == "server":
        try:
            cli.start_server(port=args.port, host=args.host, dev=args.dev)
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")
            sys.exit(0)
    
    elif args.command == "api":
        cli.print_api_list(args.format)
    
    elif args.command == "status":
        cli.show_status()
    
    elif args.command == "shutdown":
        cli.shutdown_servers(force=args.force or args.all)
    
    elif args.command == "setup":
        cli.handle_setup_command(args)
    
    elif args.command == "version":
        version_info = get_version_info()
        print(json.dumps(version_info, indent=2))
    
    elif args.command == "models":
        cli.show_models(list_models=getattr(args, 'list', False), download_missing=getattr(args, 'download', False))
    
    elif args.command == "live2d":
        cli.handle_live2d_command(args)
    
    elif args.command == "tunnel":
        cli.handle_tunnel_command(args)
    
    elif args.command == "systemd":
        cli.handle_systemd_command(args)
    
    elif args.command == "uninstall":
        cli.handle_uninstall_command(args)
    
    else:
        # No command specified, show help
        parser.print_help()
        print(f"\n💡 Quick start: {get_version_string()}")
        print("   Run 'ai2d_chat server' to start the application")

if __name__ == "__main__":
    main()
