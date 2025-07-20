#!/bin/bash
# build_pipx.sh - Build and prepare AI Companion for pipx installation

set -e

echo "🔧 Building AI Companion v0.4.0 for pipx installation"
echo "=================================================="

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info/
find . -name "*.pyc" -delete
find . -name "__pycache__" -delete

# Verify version consistency
echo "📋 Verifying version consistency..."
echo "   - pyproject.toml: $(grep 'version =' pyproject.toml | cut -d'"' -f2)"
if [ -f "setup.py" ]; then
    echo "   - setup.py: $(grep "version=" setup.py | cut -d"'" -f2)"
else
    echo "   - setup.py: not found (using pyproject.toml only)"
fi
echo "   - package.json: $(grep '"version"' package.json | cut -d'"' -f4)"

# Build the package
echo "📦 Building package..."
python3 -m build

# Verify the package
echo "✅ Verifying package contents..."
echo "Package files created:"
ls -la dist/

echo ""
echo "📁 Package contents:"
if command -v tar &> /dev/null; then
    echo "Source distribution contents:"
    tar -tzf dist/*.tar.gz | head -20
    echo "... (showing first 20 files)"
fi

# Test installation in virtual environment
echo ""
echo "🧪 Testing package installation..."

# Create temporary test environment
TEST_DIR=$(mktemp -d)
cd $TEST_DIR

echo "📍 Testing in: $TEST_DIR"

# Create virtual environment
python3 -m venv test_env
source test_env/bin/activate

# Install the package
echo "💾 Installing package for testing..."
cd - > /dev/null
pip install dist/*.whl

# Test CLI functionality
echo "🔍 Testing CLI functionality..."
echo "Testing version command:"
ai2d_chat --version

echo ""
echo "Testing API documentation:"
ai2d_chat api --format json | head -10

echo ""
echo "Testing help command:"
ai2d_chat --help

# Cleanup
deactivate
cd - > /dev/null
rm -rf $TEST_DIR

echo ""
echo "🎉 Build completed successfully!"
echo "=================================================="
echo ""
echo "📋 Installation Instructions:"
echo "   Local install:  pipx install ."
echo "   From wheel:     pipx install dist/*.whl"
echo ""
echo "🚀 Quick Start Commands:"
echo "   ai2d_chat server          # Start the server"
echo "   ai2d_chat api             # View API docs"
echo "   ai2d_chat status          # Check status"
echo "   ai2d_chat --help          # Show help"
echo ""
echo "🌐 After installation, visit: http://localhost:19080/live2d (production)"
echo "   or in dev mode: http://localhost:19081/live2d"
