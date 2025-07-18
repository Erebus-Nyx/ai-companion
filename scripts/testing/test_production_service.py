#!/usr/bin/env python3
"""
Test Production Service Configuration

This script tests the AI Companion service without dev flag to ensure all model paths
are correctly configured and the service can start in production mode.
"""

import subprocess
import time
import sys
import requests
from pathlib import Path

def test_service_restart():
    """Test restarting the service without dev flag."""
    print("🔄 Testing service restart without dev flag...")
    
    try:
        # Stop current service
        result = subprocess.run(
            ["./scripts/service-manager.sh", "stop"],
            capture_output=True, text=True, cwd="/home/nyx/ai-companion"
        )
        print(f"Service stop: {result.returncode}")
        
        # Reload daemon
        result = subprocess.run(
            ["systemctl", "--user", "daemon-reload"],
            capture_output=True, text=True
        )
        print(f"Daemon reload: {result.returncode}")
        
        # Start service
        result = subprocess.run(
            ["./scripts/service-manager.sh", "start"],
            capture_output=True, text=True, cwd="/home/nyx/ai-companion"
        )
        print(f"Service start: {result.returncode}")
        print(f"Output: {result.stdout}")
        if result.stderr:
            print(f"Errors: {result.stderr}")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Service restart failed: {e}")
        return False

def check_service_health():
    """Check if the service is running and responding."""
    print("🏥 Checking service health...")
    
    # Wait for service to start
    time.sleep(5)
    
    try:
        # Check systemd status
        result = subprocess.run(
            ["systemctl", "--user", "is-active", "ai-companion.service"],
            capture_output=True, text=True
        )
        print(f"Service status: {result.stdout.strip()}")
        
        if result.stdout.strip() != "active":
            return False
        
        # Check HTTP endpoint
        response = requests.get("http://localhost:19443", timeout=10)
        print(f"HTTP status: {response.status_code}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def check_model_paths():
    """Verify that all model files exist in expected locations."""
    print("📂 Checking model file existence...")
    
    user_data_dir = Path.home() / ".local" / "share" / "ai-companion"
    
    expected_files = [
        "models/tts/kokoro/onnx/model.onnx",
        "models/tts/kokoro/config.json", 
        "models/llm/llama-2-13b-chat.Q4_0.gguf",
        "databases/live2d.db",
        "databases/conversations.db",
        "databases/personality.db"
    ]
    
    missing_files = []
    
    for file_path in expected_files:
        full_path = user_data_dir / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            missing_files.append(file_path)
    
    return len(missing_files) == 0, missing_files

def test_api_endpoints():
    """Test key API endpoints."""
    print("🔌 Testing API endpoints...")
    
    endpoints = [
        "/api/status",
        "/api/live2d/models",
        "/status"
    ]
    
    results = {}
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"http://localhost:19443{endpoint}", timeout=5)
            results[endpoint] = response.status_code
            print(f"  {endpoint}: {response.status_code}")
        except Exception as e:
            results[endpoint] = f"Error: {e}"
            print(f"  {endpoint}: Error - {e}")
    
    return results

def main():
    """Run complete production service test."""
    print("🎯 AI Companion Production Service Test")
    print("=" * 50)
    
    # 1. Check model paths
    models_ok, missing = check_model_paths()
    if not models_ok:
        print(f"\n⚠️ Missing model files: {missing}")
        print("💡 Consider running migration script first")
    
    # 2. Test service restart
    restart_ok = test_service_restart()
    if not restart_ok:
        print("\n❌ Service restart failed")
        return 1
    
    # 3. Check service health
    health_ok = check_service_health()
    if not health_ok:
        print("\n❌ Service health check failed")
        
        # Get logs for debugging
        try:
            result = subprocess.run(
                ["./scripts/service-manager.sh", "logs"],
                capture_output=True, text=True, cwd="/home/nyx/ai-companion"
            )
            print("Recent logs:")
            print(result.stdout[-1000:])  # Last 1000 chars
        except:
            pass
        
        return 1
    
    # 4. Test API endpoints
    api_results = test_api_endpoints()
    
    # Summary
    print("\n📊 Test Summary:")
    print(f"  Model files: {'✅' if models_ok else '❌'}")
    print(f"  Service restart: {'✅' if restart_ok else '❌'}")
    print(f"  Health check: {'✅' if health_ok else '❌'}")
    print(f"  API endpoints: {len([r for r in api_results.values() if r == 200])}/{len(api_results)} working")
    
    if models_ok and restart_ok and health_ok:
        print("\n🎉 Production service test PASSED!")
        return 0
    else:
        print("\n❌ Production service test FAILED!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
