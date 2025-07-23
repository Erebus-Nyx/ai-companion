#!/usr/bin/env python3
"""
Development Flask Server Restart Script
Kills existing Flask app.py processes and starts a new one in the background.
"""

import os
import subprocess
import sys
import time
import signal

def find_flask_processes():
    """Find all running python3 app.py processes"""
    try:
        # Use ps to find python3 app.py processes
        result = subprocess.run(
            ["ps", "aux"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        processes = []
        for line in result.stdout.split('\n'):
            if 'python3 app.py' in line and 'grep' not in line:
                # Extract PID (second column)
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        pid = int(parts[1])
                        processes.append(pid)
                        print(f"Found Flask process: PID {pid}")
                    except ValueError:
                        continue
        
        return processes
    except subprocess.CalledProcessError as e:
        print(f"Error finding processes: {e}")
        return []

def kill_flask_processes():
    """Kill all existing Flask app.py processes"""
    processes = find_flask_processes()
    
    if not processes:
        print("No existing Flask processes found.")
        return True
    
    print(f"Killing {len(processes)} Flask process(es)...")
    
    for pid in processes:
        try:
            print(f"Terminating PID {pid}...")
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            print(f"Process {pid} already terminated")
        except PermissionError:
            print(f"Permission denied killing process {pid}")
            return False
        except Exception as e:
            print(f"Error killing process {pid}: {e}")
            return False
    
    # Wait a bit for graceful shutdown
    print("Waiting for processes to terminate...")
    time.sleep(2)
    
    # Check if any processes are still running
    remaining = find_flask_processes()
    if remaining:
        print(f"Force killing {len(remaining)} remaining process(es)...")
        for pid in remaining:
            try:
                os.kill(pid, signal.SIGKILL)
                print(f"Force killed PID {pid}")
            except ProcessLookupError:
                print(f"Process {pid} already terminated")
            except Exception as e:
                print(f"Error force killing process {pid}: {e}")
        
        time.sleep(1)
    
    return True

def start_flask_server():
    """Start Flask server in background with nohup"""
    print("Starting Flask server in background...")
    
    try:
        # Change to the script directory to ensure correct working directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
        
        # Start the Flask server with nohup
        subprocess.Popen(
            ["nohup", "python3", "app.py"],
            stdout=open("nohup.out", "w"),
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid  # Start in new session to detach from terminal
        )
        
        print("Flask server started successfully!")
        print("Output will be logged to nohup.out")
        print("Use 'tail -f nohup.out' to monitor the log")
        
        # Wait a moment and check if it started
        time.sleep(2)
        new_processes = find_flask_processes()
        if new_processes:
            print(f"Confirmed: Flask server running with PID(s): {new_processes}")
            return True
        else:
            print("Warning: No Flask processes found after startup")
            return False
            
    except Exception as e:
        print(f"Error starting Flask server: {e}")
        return False

def main():
    """Main function to restart Flask development server"""
    print("=" * 50)
    print("Flask Development Server Restart Script")
    print("=" * 50)
    
    # Kill existing processes
    if not kill_flask_processes():
        print("Failed to kill existing processes. Exiting.")
        sys.exit(1)
    
    # Start new server
    if not start_flask_server():
        print("Failed to start Flask server. Check nohup.out for details.")
        sys.exit(1)
    
    print("=" * 50)
    print("Flask server restart completed successfully!")
    print("Monitor with: tail -f nohup.out")
    print("Stop with: kill $(ps aux | grep 'python3 app.py' | grep -v grep | awk '{print $2}')")
    print("=" * 50)

if __name__ == "__main__":
    main()
