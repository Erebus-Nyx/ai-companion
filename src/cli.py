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

class AICompanionCLI:
    """Main CLI interface for AI Companion."""
    
    def __init__(self):
        self.server_process = None
        
    def get_api_endpoints(self) -> Dict[str, Any]:
        """Return comprehensive API documentation."""
        return {
            "version": API_VERSION_FULL,
            "base_url": "http://localhost:19443",
            "endpoints": {
                "chat": {
                    "url": "/api/chat",
                    "methods": ["POST"],
                    "description": "Send chat messages to AI companion",
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
                "url": "ws://localhost:19443/socket.io/",
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
            print("\n📖 For detailed API documentation, use: ai-companion api --format json")
    
    def check_and_download_models(self):
        """Check and download ALL required models during server startup."""
        print("🔍 Checking and downloading AI models...")
        print("💡 NOTE: All models MUST be downloaded at startup for reliable operation.")
        
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
                return True
            
        except ImportError as e:
            print(f"❌ CRITICAL: Model management modules not found: {e}")
            print("💡 Cannot proceed without core modules. Check your installation.")
            return False
        except Exception as e:
            print(f"❌ CRITICAL: An unexpected error occurred during model check: {e}")
            print("💡 Aborting server startup.")
            return False

    def start_server(self, port: int = 19443, host: str = "localhost", dev: bool = False):
        """Start the AI Companion server."""
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
    
    def show_status(self):
        """Show system status."""
        print(f"📊 {get_version_string()}")
        print("=" * 50)
        
        # Check if server is running
        try:
            import requests
            response = requests.get("http://localhost:19443/api/system/status", timeout=2)
            if response.status_code == 200:
                status = response.json()
                print("🟢 Server Status: RUNNING")
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

    def handle_setup_command(self, args):
        """Handle the setup command for AI Companion configuration."""
        print("🔧 AI Companion Setup")
        print("=====================")
        
        try:
            from .config_manager import ConfigManager
        except ImportError:
            try:
                from config_manager import ConfigManager
            except ImportError:
                # For installed package
                from src.config_manager import ConfigManager
            
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
            print("   2. Run 'ai-companion models --download' to get AI models")
            print("   3. Run 'ai-companion server' to start the application")
            
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

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AI Companion - Interactive AI with Live2D Avatar",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ai-companion server                    # Start server on default port
  ai-companion server --port 8080       # Start server on custom port
  ai-companion server --dev             # Start in development mode
  ai-companion api                       # Show API documentation
  ai-companion api --format json        # Show API docs in JSON format
  ai-companion status                    # Show system status
  ai-companion version                   # Show version information
  ai-companion models                    # Show model information
  ai-companion models --list             # List available models
  ai-companion models --paths            # Show model storage paths
  ai-companion models                    # Show model storage paths
  ai-companion models --list             # List all available models
        """
    )
    
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=get_version_string()
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Server command
    server_parser = subparsers.add_parser("server", help="Start the AI Companion server")
    server_parser.add_argument("--port", "-p", type=int, default=19443, help="Port to run server on (default: 19443)")
    server_parser.add_argument("--host", default="localhost", help="Host to bind to (default: localhost)")
    server_parser.add_argument("--dev", action="store_true", help="Run in development mode")
    
    # API documentation command
    api_parser = subparsers.add_parser("api", help="Show API documentation")
    api_parser.add_argument("--format", "-f", choices=["text", "json", "yaml"], default="text", help="Output format")
    
    # Status command
    subparsers.add_parser("status", help="Show system status")
    
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
    
    elif args.command == "setup":
        cli.handle_setup_command(args)
    
    elif args.command == "version":
        version_info = get_version_info()
        print(json.dumps(version_info, indent=2))
    
    elif args.command == "models":
        cli.show_models(list_models=getattr(args, 'list', False), download_missing=getattr(args, 'download', False))
    
    elif args.command == "live2d":
        cli.handle_live2d_command(args)
    
    else:
        # No command specified, show help
        parser.print_help()
        print(f"\n💡 Quick start: {get_version_string()}")
        print("   Run 'ai-companion server' to start the application")

if __name__ == "__main__":
    main()
