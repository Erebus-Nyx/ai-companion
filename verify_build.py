#!/usr/bin/env python3
"""
Pre-build verification script for AI Companion v0.4.0
Ensures all components are ready for pipx packaging.
"""

import os
import sys
import json
import re
from pathlib import Path

def check_version_consistency():
    """Check that all version numbers are consistent across files."""
    print("🔍 Checking version consistency...")
    
    expected_version = "0.4.0"
    files_to_check = {
        "pyproject.toml": r'version = "([^"]+)"',
        "setup.py": r"version='([^']+)'",
        "package.json": r'"version": "([^"]+)"',
        "src/__version__.py": r'__version__ = "([^"]+)"',
        "src/web/static/js/live2d_config.js": r"'l2dVersion': '([^']+)'",
        "src/audio/__init__.py": r"__version__ = '([^']+)'"
    }
    
    all_good = True
    
    for file_path, pattern in files_to_check.items():
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
                match = re.search(pattern, content)
                if match:
                    version = match.group(1)
                    if version == expected_version:
                        print(f"   ✅ {file_path}: {version}")
                    else:
                        print(f"   ❌ {file_path}: {version} (expected {expected_version})")
                        all_good = False
                else:
                    print(f"   ⚠️  {file_path}: version pattern not found")
                    all_good = False
        else:
            print(f"   ❌ {file_path}: file not found")
            all_good = False
    
    return all_good

def check_cli_module():
    """Verify CLI module is properly configured."""
    print("\n🖥️  Checking CLI module...")
    
    try:
        # Check if CLI module exists and is importable
        cli_path = "src/cli.py"
        if os.path.exists(cli_path):
            print(f"   ✅ CLI module exists: {cli_path}")
            
            # Check main function exists
            with open(cli_path, 'r') as f:
                content = f.read()
                if "def main():" in content:
                    print("   ✅ main() function found")
                else:
                    print("   ❌ main() function not found")
                    return False
                
                if "AICompanionCLI" in content:
                    print("   ✅ AICompanionCLI class found")
                else:
                    print("   ❌ AICompanionCLI class not found")
                    return False
        else:
            print(f"   ❌ CLI module not found: {cli_path}")
            return False
        
        return True
    except Exception as e:
        print(f"   ❌ Error checking CLI module: {e}")
        return False

def check_entry_points():
    """Verify entry points in pyproject.toml."""
    print("\n🚪 Checking entry points...")
    
    try:
        with open("pyproject.toml", 'r') as f:
            content = f.read()
            
        if 'ai-companion = "cli:main"' in content:
            print("   ✅ Main CLI entry point configured")
        else:
            print("   ❌ Main CLI entry point not found")
            return False
            
        if 'ai-companion-server = "main:main"' in content:
            print("   ✅ Server entry point configured")
        else:
            print("   ❌ Server entry point not found")
            return False
        
        return True
    except Exception as e:
        print(f"   ❌ Error checking entry points: {e}")
        return False

def check_live2d_dependencies():
    """Check that Live2D dependencies are present."""
    print("\n🎭 Checking Live2D dependencies...")
    
    required_paths = [
        "src/web/static/dist/pixi-6.5.10.min.js",
        "src/web/static/dist/pixi-live2d-display-0.4.0.min.js",
        "src/web/static/dist/live2d_bundle.js",
        "src/web/static/dist/CubismSdkForWeb-5-r.4/Core/live2dcubismcore.min.js",
        "src/web/static/dist/CubismSdkForWeb-5-r.4/Framework/dist/live2dcubismframework.js",
        "src/web/static/live2d_pixi.html"
    ]
    
    all_present = True
    
    for path in required_paths:
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"   ✅ {path} ({size:,} bytes)")
        else:
            print(f"   ❌ {path} (missing)")
            all_present = False
    
    return all_present

def check_api_documentation():
    """Check API documentation is present and up to date."""
    print("\n📚 Checking API documentation...")
    
    api_doc_path = "docs/API_REFERENCE_v0.4.0.md"
    
    if os.path.exists(api_doc_path):
        print(f"   ✅ API documentation exists: {api_doc_path}")
        
        with open(api_doc_path, 'r') as f:
            content = f.read()
            
        if "v0.4.0" in content:
            print("   ✅ Documentation version is current")
        else:
            print("   ⚠️  Documentation may not be current version")
            
        if "http://localhost:19443" in content:
            print("   ✅ Correct port (19443) in documentation")
        else:
            print("   ❌ Incorrect port in documentation")
            return False
            
        return True
    else:
        print(f"   ❌ API documentation not found: {api_doc_path}")
        return False

def check_manifest():
    """Check MANIFEST.in includes all necessary files."""
    print("\n📦 Checking MANIFEST.in...")
    
    if os.path.exists("MANIFEST.in"):
        with open("MANIFEST.in", 'r') as f:
            content = f.read()
        
        required_includes = [
            "src/__version__.py",
            "src/cli.py",
            "recursive-include src/web/static",
            "recursive-include docs"
        ]
        
        all_present = True
        for include in required_includes:
            if include in content:
                print(f"   ✅ {include}")
            else:
                print(f"   ❌ Missing: {include}")
                all_present = False
        
        return all_present
    else:
        print("   ❌ MANIFEST.in not found")
        return False

def check_requirements():
    """Check that requirements.txt has all necessary dependencies."""
    print("\n📋 Checking requirements.txt...")
    
    if os.path.exists("requirements.txt"):
        with open("requirements.txt", 'r') as f:
            requirements = f.read()
        
        critical_deps = [
            "flask",
            "flask-socketio",
            "torch",
            "transformers",
            "pyyaml"
        ]
        
        all_present = True
        for dep in critical_deps:
            if dep in requirements.lower():
                print(f"   ✅ {dep}")
            else:
                print(f"   ❌ Missing: {dep}")
                all_present = False
        
        return all_present
    else:
        print("   ❌ requirements.txt not found")
        return False

def main():
    """Run all pre-build checks."""
    print("🔧 AI Companion Pre-build Verification v0.4.0")
    print("=" * 50)
    
    checks = [
        ("Version Consistency", check_version_consistency),
        ("CLI Module", check_cli_module),
        ("Entry Points", check_entry_points),
        ("Live2D Dependencies", check_live2d_dependencies),
        ("API Documentation", check_api_documentation),
        ("MANIFEST.in", check_manifest),
        ("Requirements", check_requirements)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        try:
            if not check_func():
                all_passed = False
        except Exception as e:
            print(f"\n❌ Error in {check_name}: {e}")
            all_passed = False
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("🎉 All checks passed! Ready for pipx build.")
        print("\n📋 Next steps:")
        print("   ./build_pipx.sh                    # Build package")
        print("   pipx install .                     # Install locally")
        print("   ai-companion server                # Test installation")
        print("\n🌐 After installation:")
        print("   http://localhost:19443/live2d      # Live2D interface")
        print("   ai-companion api                   # View API docs")
        return 0
    else:
        print("❌ Some checks failed. Please fix issues before building.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
