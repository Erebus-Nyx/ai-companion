#!/bin/bash
# download_live2d_dependencies.sh
# Download and organize Live2D dependencies for offline installation

set -e

echo "📦 Downloading Live2D Dependencies for Offline Installation"
echo "=========================================================="

DIST_DIR="src/web/static/dist"
mkdir -p "$DIST_DIR"

# Download pixi-live2d-display if not present
PIXI_LIVE2D_FILE="$DIST_DIR/pixi-live2d-display-0.4.0.min.js"
if [ ! -f "$PIXI_LIVE2D_FILE" ]; then
    echo "⬇️  Downloading pixi-live2d-display..."
    curl -o "$PIXI_LIVE2D_FILE" \
         -L "https://cdn.jsdelivr.net/npm/pixi-live2d-display@0.4.0/dist/index.min.js"
    echo "✅ Downloaded pixi-live2d-display"
else
    echo "✅ pixi-live2d-display already exists"
fi

# Verify all critical files exist
echo "🔍 Verifying Live2D dependencies..."

critical_files=(
    "$DIST_DIR/pixi-6.5.10.min.js"
    "$DIST_DIR/live2d_bundle.js" 
    "$DIST_DIR/CubismSdkForWeb-5-r.4/Core/live2dcubismcore.min.js"
    "$PIXI_LIVE2D_FILE"
)

all_present=true
for file in "${critical_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ Found: $(basename "$file")"
    else
        echo "❌ Missing: $file"
        all_present=false
    fi
done

if [ "$all_present" = true ]; then
    echo ""
    echo "🎉 All Live2D dependencies are present!"
    echo "📊 File sizes:"
    ls -lh "$DIST_DIR"/*.js 2>/dev/null || true
    echo ""
    echo "🔧 Package is ready for offline installation"
else
    echo ""
    echo "❌ Some dependencies are missing. Please check the above output."
    exit 1
fi
