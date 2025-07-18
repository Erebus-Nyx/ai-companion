#!/bin/bash
# deploy_live2d_integration.sh
# Deployment script for migrating to Live2D PIXI integrated interface

set -e  # Exit on any error

echo "🚀 AI Companion Live2D Integration Deployment"
echo "=============================================="

# Variables
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)_live2d_migration"
INDEX_TEMPLATE="src/web/templates/index.html"
LIVE2D_STATIC="src/web/static/live2d_pixi.html"
NEW_INDEX_TEMPLATE="src/web/templates/live2d_index.html"

# Create backup directory
echo "📦 Creating backup directory: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# Backup current index.html
if [ -f "$INDEX_TEMPLATE" ]; then
    echo "📄 Backing up current index.html..."
    cp "$INDEX_TEMPLATE" "$BACKUP_DIR/index.html.backup"
    echo "✅ Backup created: $BACKUP_DIR/index.html.backup"
else
    echo "⚠️  Warning: $INDEX_TEMPLATE not found"
fi

# Copy live2d_pixi.html to templates directory as new index
echo "🔄 Migrating Live2D PIXI interface to main template..."
if [ -f "$LIVE2D_STATIC" ]; then
    # First copy to a new name to avoid conflicts
    cp "$LIVE2D_STATIC" "$NEW_INDEX_TEMPLATE"
    echo "✅ Created new template: $NEW_INDEX_TEMPLATE"
    
    # Now replace the original
    cp "$LIVE2D_STATIC" "$INDEX_TEMPLATE"
    echo "✅ Replaced main index template with Live2D PIXI interface"
else
    echo "❌ Error: $LIVE2D_STATIC not found!"
    exit 1
fi

# Update template paths in the new index.html (if needed)
echo "🔧 Updating asset paths for template directory..."
if command -v sed >/dev/null 2>&1; then
    # Update CSS and JS paths to work from templates directory
    sed -i 's|href="css/|href="/static/css/|g' "$INDEX_TEMPLATE"
    sed -i 's|src="js/|src="/static/js/|g' "$INDEX_TEMPLATE"
    sed -i 's|src="dist/|src="/static/dist/|g' "$INDEX_TEMPLATE"
    echo "✅ Updated asset paths for Flask templates"
else
    echo "⚠️  Warning: sed not available, manual path updates may be needed"
fi

# Verify critical files exist
echo "🔍 Verifying critical files..."
critical_files=(
    "src/web/static/js/voice-recording.js"
    "src/web/static/js/tts-audio.js"
    "src/web/static/js/chat.js"
    "src/web/static/js/db.js"
    "src/web/static/css/live2d_test.css"
)

for file in "${critical_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ Found: $file"
    else
        echo "❌ Missing: $file"
    fi
done

# Check if Flask app exists
if [ -f "src/app.py" ]; then
    echo "✅ Flask app found: src/app.py"
elif [ -f "src/main.py" ]; then
    echo "✅ Main app found: src/main.py"
else
    echo "⚠️  Warning: Flask app not found in expected locations"
fi

# Display next steps
echo ""
echo "🎯 Migration Complete! Next Steps:"
echo "================================="
echo ""
echo "1. 🧪 Test the integrated interface:"
echo "   cd /path/to/ai-companion"
echo "   python src/app.py"
echo "   # Visit http://localhost:19443 to test"
echo ""
echo "2. 📦 Install with pipx for production:"
echo "   pipx install ."
echo "   # or for development:"
echo "   pipx install -e ."
echo ""
echo "3. 🌐 Set up for Cloudflare access:"
echo "   # Configure your Flask app to bind to 0.0.0.0:PORT"
echo "   # Set up Cloudflare tunnel or DNS pointing to your server"
echo ""
echo "4. 🔧 Configure production settings:"
echo "   # Update config.yaml for production environment"
echo "   # Set appropriate host and port bindings"
echo ""
echo "📂 Backup location: $BACKUP_DIR"
echo "🔄 Original index.html backed up"
echo "✨ Live2D PIXI interface is now the main interface"
echo ""
echo "🚀 Ready for production deployment!"
