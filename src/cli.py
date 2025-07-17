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
    
    def start_server(self, port: int = 19443, host: str = "localhost", dev: bool = False):
        """Start the AI Companion server."""
        print(f"🚀 Starting AI Companion Server on {host}:{port}")
        
        # Import and start the Flask app
        try:
            import sys
            import os
            
            # Add src directory to path
            src_path = os.path.join(os.path.dirname(__file__))
            if src_path not in sys.path:
                sys.path.insert(0, src_path)
            
            from app import app, socketio
            
            print("✅ AI Companion modules loaded successfully")
            print(f"🌐 Server will be available at: http://{host}:{port}")
            print("🎭 Live2D interface: http://localhost:19443/live2d")
            print("⚡ Press Ctrl+C to stop the server")
            
            # Set environment
            if dev:
                os.environ['FLASK_ENV'] = 'development'
                app.debug = True
            
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
            print("💡 Make sure you're in the correct directory and dependencies are installed")
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
    
    # Version command
    subparsers.add_parser("version", help="Show detailed version information")
    
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
    
    elif args.command == "version":
        version_info = get_version_info()
        print(json.dumps(version_info, indent=2))
    
    else:
        # No command specified, show help
        parser.print_help()
        print(f"\n💡 Quick start: {get_version_string()}")
        print("   Run 'ai-companion server' to start the application")

if __name__ == "__main__":
    main()
