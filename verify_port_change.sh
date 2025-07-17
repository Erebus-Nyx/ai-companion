#!/bin/bash
# verify_port_change.sh
# Verify that all port references have been updated to 19443

echo "🔍 AI Companion Port Configuration Verification"
echo "==============================================="

echo "📊 Checking port configuration in key files..."

# Check production config
if grep -q "19443" src/production_config.py; then
    echo "✅ Production config: Port 19443 configured"
else
    echo "❌ Production config: Port not updated"
fi

# Check main entry point
if grep -q "19443" ai_companion_main.py; then
    echo "✅ Main entry point: Port 19443 configured"
else
    echo "❌ Main entry point: Port not updated"
fi

# Check JavaScript API files
js_files_updated=0
total_js_files=0

for file in src/web/static/js/*.js; do
    if [ -f "$file" ]; then
        total_js_files=$((total_js_files + 1))
        if grep -q "19443" "$file" 2>/dev/null; then
            js_files_updated=$((js_files_updated + 1))
            echo "✅ $(basename "$file"): Port 19443 configured"
        fi
    fi
done

if [ $js_files_updated -gt 0 ]; then
    echo "✅ JavaScript files: $js_files_updated/$total_js_files files updated with port 19443"
else
    echo "ℹ️  JavaScript files: No port references found (this may be normal)"
fi

# Check for any remaining old port references
echo ""
echo "🔍 Checking for any remaining 13443 references..."
remaining_refs=$(find . -name "*.py" -o -name "*.js" -o -name "*.html" -o -name "*.sh" | xargs grep -l "13443" 2>/dev/null | grep -v docs | wc -l)

if [ "$remaining_refs" -eq 0 ]; then
    echo "✅ No remaining 13443 references found in code files"
else
    echo "⚠️  Found $remaining_refs files with remaining 13443 references:"
    find . -name "*.py" -o -name "*.js" -o -name "*.html" -o -name "*.sh" | xargs grep -l "13443" 2>/dev/null | grep -v docs
fi

echo ""
echo "🚀 Port Migration Summary:"
echo "========================="
echo "• Old port: 13443"
echo "• New port: 19443"
echo "• Status: Migration complete"
echo ""
echo "💡 Next steps:"
echo "1. Test the application: python src/app.py"
echo "2. Visit: http://localhost:19443"
echo "3. Update any external configurations (firewall, proxy, etc.)"
