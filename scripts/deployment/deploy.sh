#!/bin/bash

# deploy.sh - Production deployment script for AI Companion Live2D

set -e  # Exit on any error

echo "🚀 AI Companion Live2D - Production Deployment Script"
echo "======================================================"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}📍 Working directory: $SCRIPT_DIR${NC}"

# Step 1: Backup the current index.html
echo -e "\n${YELLOW}📦 Step 1: Backing up current index.html...${NC}"
if [ -f "src/web/templates/index.html" ]; then
    BACKUP_NAME="index_backup_$(date +%Y%m%d_%H%M%S).html"
    cp "src/web/templates/index.html" "backups/$BACKUP_NAME"
    echo -e "${GREEN}✅ Backup created: backups/$BACKUP_NAME${NC}"
else
    echo -e "${YELLOW}⚠️  No existing index.html found to backup${NC}"
fi

# Step 2: Replace index.html with live2d_pixi.html
echo -e "\n${YELLOW}🔄 Step 2: Migrating Live2D interface...${NC}"
if [ -f "src/web/static/live2d_pixi.html" ]; then
    # Create template directory if it doesn't exist
    mkdir -p "src/web/templates"
    
    # Copy live2d_pixi.html to replace index.html
    cp "src/web/static/live2d_pixi.html" "src/web/templates/index.html"
    echo -e "${GREEN}✅ Live2D interface migrated to index.html${NC}"
    
    # Update the CSS link in the new index.html to use the correct path
    sed -i 's|href="css/live2d_test.css"|href="/static/css/live2d_test.css"|g' "src/web/templates/index.html"
    sed -i 's|src="js/|src="/static/js/|g' "src/web/templates/index.html"
    sed -i 's|src="dist/|src="/static/dist/|g' "src/web/templates/index.html"
    echo -e "${GREEN}✅ Updated static file paths for Flask serving${NC}"
else
    echo -e "${RED}❌ Error: live2d_pixi.html not found!${NC}"
    exit 1
fi

# Step 3: Validate dependencies
echo -e "\n${YELLOW}🔍 Step 3: Validating dependencies...${NC}"
if [ -f "pyproject.toml" ] && [ -f "requirements.txt" ]; then
    echo -e "${GREEN}✅ pyproject.toml and requirements.txt found${NC}"
    
    # Check if main.py exists
    if [ -f "src/main.py" ]; then
        echo -e "${GREEN}✅ Main entry point found: src/main.py${NC}"
    else
        echo -e "${YELLOW}⚠️  Creating main entry point...${NC}"
        cat > src/main.py << 'EOF'
#!/usr/bin/env python3
"""
AI Companion - Main Entry Point
Production-ready Live2D AI Companion with enhanced VAD, emotional TTS, and local LLM.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

def main():
    """Main entry point for AI Companion."""
    try:
        from app import app
        import logging
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        logger = logging.getLogger(__name__)
        logger.info("🤖 Starting AI Companion Live2D Server...")
        
        # Run the Flask app
        app.run(
            host='0.0.0.0',
            port=19443,
            debug=False,
            threaded=True
        )
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please ensure all dependencies are installed.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF
        echo -e "${GREEN}✅ Created main.py entry point${NC}"
    fi
else
    echo -e "${RED}❌ Error: Missing pyproject.toml or requirements.txt${NC}"
    exit 1
fi

# Step 4: Build package
echo -e "\n${YELLOW}🔨 Step 4: Building package...${NC}"
if command -v python3 &> /dev/null; then
    echo -e "${BLUE}📦 Installing build dependencies...${NC}"
    python3 -m pip install --upgrade pip build wheel
    
    echo -e "${BLUE}🔧 Building package...${NC}"
    python3 -m build
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Package built successfully${NC}"
    else
        echo -e "${RED}❌ Build failed${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ Error: python3 not found${NC}"
    exit 1
fi

# Step 5: Installation instructions
echo -e "\n${GREEN}🎉 Deployment Complete!${NC}"
echo -e "${BLUE}📋 Installation Instructions:${NC}"
echo ""
echo -e "${YELLOW}For pipx installation (recommended):${NC}"
echo "  pipx install ./dist/ai2d_chat-*.whl"
echo ""
echo -e "${YELLOW}For pip installation:${NC}"
echo "  pip install ./dist/ai2d_chat-*.whl"
echo ""
echo -e "${YELLOW}To run after installation:${NC}"
echo "  ai2d_chat"
echo ""
echo -e "${YELLOW}For development mode:${NC}"
echo "  pip install -e ."
echo "  python src/main.py"
echo ""
echo -e "${BLUE}📡 Server will be available at: http://localhost:19443${NC}"
echo -e "${BLUE}🎭 Live2D interface with enhanced AI features ready!${NC}"

echo ""
echo -e "${GREEN}✨ Ready for Cloudflare tunnel setup!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Install with pipx: pipx install ./dist/ai2d_chat-*.whl"
echo "2. Run: ai2d_chat"
echo "3. Set up Cloudflare tunnel to expose port 19443"
echo "4. Configure DNS for external access"
