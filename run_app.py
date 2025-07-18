#!/usr/bin/env python3
"""
Simple launcher script that sets up the Python path correctly
and runs the AI Companion application.
"""
import sys
import os

# Add the src directory to Python path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

# Now import and run the app
if __name__ == "__main__":
    from app import app, socketio
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Companion Server')
    parser.add_argument('--port', type=int, default=19443, help='Port to run the server on')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--test-db-paths', action='store_true', help='Test database paths and exit')
    
    args = parser.parse_args()
    
    if args.test_db_paths:
        print("Testing database paths...")
        # Import database components to test paths
        try:
            from databases.db_manager import DBManager
            print("✓ Database manager imported successfully")
            
            # Test user data directory structure
            import os
            from pathlib import Path
            
            user_data_dir = Path.home() / '.local/share/ai-companion'
            db_dir = user_data_dir / 'databases'
            
            print(f"✓ User data directory: {user_data_dir}")
            print(f"✓ Database directory: {db_dir}")
            print(f"✓ Directory exists: {db_dir.exists()}")
            
            if db_dir.exists():
                db_files = list(db_dir.glob('*.db'))
                print(f"✓ Found {len(db_files)} database files:")
                for db_file in db_files:
                    print(f"  - {db_file.name}")
            
            print("✓ Database path test completed successfully")
            
        except Exception as e:
            print(f"✗ Database path test failed: {e}")
            sys.exit(1)
        
        sys.exit(0)
    
    # Run the app
    print(f"Starting AI Companion on {args.host}:{args.port}")
    socketio.run(app, host=args.host, port=args.port, debug=args.debug)
