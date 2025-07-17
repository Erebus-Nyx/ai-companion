#!/bin/bash

# cloudflare-setup.sh - Helper script for setting up Cloudflare tunnel

echo "🌐 AI Companion - Cloudflare Tunnel Setup Helper"
echo "================================================="

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}This script will help you set up a Cloudflare tunnel for AI Companion${NC}"
echo ""

# Check if cloudflared is installed
if command -v cloudflared &> /dev/null; then
    echo -e "${GREEN}✅ cloudflared is installed${NC}"
else
    echo -e "${YELLOW}📦 Installing cloudflared...${NC}"
    
    # Detect OS and install accordingly
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
        sudo dpkg -i cloudflared.deb
        rm cloudflared.deb
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install cloudflared
    else
        echo -e "${YELLOW}⚠️  Please install cloudflared manually for your OS${NC}"
        echo "Visit: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"
        exit 1
    fi
fi

echo ""
echo -e "${YELLOW}🔧 Setup Instructions:${NC}"
echo ""
echo "1. First, authenticate with Cloudflare:"
echo "   cloudflared tunnel login"
echo ""
echo "2. Create a tunnel:"
echo "   cloudflared tunnel create ai-companion"
echo ""
echo "3. Configure the tunnel (replace YOUR_TUNNEL_ID):"
echo "   Create ~/.cloudflared/config.yml with:"
echo ""
cat << 'EOF'
tunnel: YOUR_TUNNEL_ID
credentials-file: /home/user/.cloudflared/YOUR_TUNNEL_ID.json

ingress:
  - hostname: ai-companion.yourdomain.com
    service: http://localhost:19443
  - service: http_status:404
EOF
echo ""
echo "4. Route traffic through the tunnel:"
echo "   cloudflared tunnel route dns ai-companion ai-companion.yourdomain.com"
echo ""
echo "5. Run the tunnel:"
echo "   cloudflared tunnel run ai-companion"
echo ""
echo -e "${GREEN}🎉 Your AI Companion will be available at: https://ai-companion.yourdomain.com${NC}"
echo ""
echo -e "${BLUE}💡 Pro tip: Set up a systemd service for automatic startup${NC}"
