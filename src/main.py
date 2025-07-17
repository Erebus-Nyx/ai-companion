#!/usr/bin/env python3
"""
AI Companion Main Entry Point

This module provides the primary entry point for the AI Companion application.
It can be run directly or used as a module.
"""

import sys
import os

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def main():
    """Main entry point that delegates to CLI interface."""
    try:
        from cli import main as cli_main
        cli_main()
    except ImportError:
        # Fallback to direct app launch
        print("CLI module not available, starting server directly...")
        try:
            from app import app, socketio
            print("🚀 Starting AI Companion Server on localhost:19443")
            print("🎭 Live2D interface: http://localhost:19443/live2d")
            print("⚡ Press Ctrl+C to stop the server")
            socketio.run(app, host='localhost', port=19443, debug=False, allow_unsafe_werkzeug=True)
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            sys.exit(1)

if __name__ == '__main__':
    main()
