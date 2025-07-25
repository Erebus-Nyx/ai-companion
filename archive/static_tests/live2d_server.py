#!/usr/bin/env python3
"""
Simple HTTP server for Live2D viewer development
"""
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver
from urllib.parse import urlparse
from pathlib import Path

class Live2DHTTPRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Use relative path to find static directory
        script_dir = Path(__file__).parent.parent.parent  # Go up to repo root
        static_dir = str(script_dir / "src/web/static")
        super().__init__(*args, directory=static_dir, **kwargs)
    
    def end_headers(self):
        # Add CORS headers for local development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        
        # Set proper MIME types for Live2D files
        if self.path.endswith('.moc3'):
            self.send_header('Content-Type', 'application/octet-stream')
        elif self.path.endswith('.model3.json'):
            self.send_header('Content-Type', 'application/json')
        elif self.path.endswith('.physics3.json'):
            self.send_header('Content-Type', 'application/json')
        elif self.path.endswith('.motion3.json'):
            self.send_header('Content-Type', 'application/json')
        elif self.path.endswith('.js'):
            self.send_header('Content-Type', 'application/javascript')
        
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def main():
    port = 13443
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port number: {sys.argv[1]}")
            sys.exit(1)
    
    print(f"Starting Live2D development server...")
    print(f"Server running at: http://localhost:{port}")
    print(f"Live2D viewer URL: http://localhost:{port}/index.html")
    # Show the actual static directory path
    script_dir = Path(__file__).parent.parent.parent  # Go up to repo root
    static_dir = script_dir / "src/web/static"
    print(f"Serving from: {static_dir}")
    print("Press Ctrl+C to stop the server")
    
    with socketserver.TCPServer(("", port), Live2DHTTPRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == "__main__":
    main()
