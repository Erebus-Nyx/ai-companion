#!/bin/bash

# AI Companion Service Management Script
# Provides easy commands to manage the AI Companion systemd service

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SERVICE_NAME="ai-companion"

# Function to show usage
show_usage() {
    echo -e "${BLUE}🤖 AI Companion Service Manager${NC}"
    echo "================================="
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     - Start the AI Companion service"
    echo "  stop      - Stop the AI Companion service"
    echo "  restart   - Restart the AI Companion service"
    echo "  status    - Show service status"
    echo "  logs      - Show service logs (follow mode)"
    echo "  enable    - Enable service to start on boot"
    echo "  disable   - Disable service from starting on boot"
    echo "  install   - Install/reinstall the systemd service"
    echo "  uninstall - Remove the systemd service"
    echo ""
    echo "Examples:"
    echo "  $0 start     # Start the service"
    echo "  $0 logs      # View live logs"
    echo "  $0 status    # Check if service is running"
}

# Function to check if service exists
service_exists() {
    systemctl --user list-unit-files | grep -q "^${SERVICE_NAME}.service"
}

# Function to get service status
get_status() {
    if service_exists; then
        systemctl --user is-active "${SERVICE_NAME}" 2>/dev/null || echo "inactive"
    else
        echo "not-installed"
    fi
}

# Main command handling
case "${1:-}" in
    "start")
        echo -e "${YELLOW}🚀 Starting AI Companion service...${NC}"
        if ! service_exists; then
            echo -e "${RED}❌ Service not installed. Run '$0 install' first.${NC}"
            exit 1
        fi
        systemctl --user start "${SERVICE_NAME}"
        sleep 2
        if [[ "$(get_status)" == "active" ]]; then
            echo -e "${GREEN}✅ AI Companion service started successfully${NC}"
            echo -e "${BLUE}🌐 Access at: http://localhost:19443${NC}"
            echo -e "${BLUE}🎭 Live2D interface: http://localhost:19443/live2d${NC}"
        else
            echo -e "${RED}❌ Failed to start service${NC}"
            echo "Check status with: $0 status"
            exit 1
        fi
        ;;
    
    "stop")
        echo -e "${YELLOW}🛑 Stopping AI Companion service...${NC}"
        if ! service_exists; then
            echo -e "${RED}❌ Service not installed.${NC}"
            exit 1
        fi
        systemctl --user stop "${SERVICE_NAME}"
        echo -e "${GREEN}✅ AI Companion service stopped${NC}"
        ;;
    
    "restart")
        echo -e "${YELLOW}🔄 Restarting AI Companion service...${NC}"
        if ! service_exists; then
            echo -e "${RED}❌ Service not installed. Run '$0 install' first.${NC}"
            exit 1
        fi
        systemctl --user restart "${SERVICE_NAME}"
        sleep 2
        if [[ "$(get_status)" == "active" ]]; then
            echo -e "${GREEN}✅ AI Companion service restarted successfully${NC}"
            echo -e "${BLUE}🌐 Access at: http://localhost:19443${NC}"
        else
            echo -e "${RED}❌ Failed to restart service${NC}"
            exit 1
        fi
        ;;
    
    "status")
        echo -e "${BLUE}📊 AI Companion Service Status${NC}"
        echo "==============================="
        
        if ! service_exists; then
            echo -e "${RED}❌ Service not installed${NC}"
            echo "Run '$0 install' to install the service."
            exit 1
        fi
        
        # Show detailed status
        systemctl --user status "${SERVICE_NAME}" --no-pager -l
        
        # Show if enabled
        if systemctl --user is-enabled "${SERVICE_NAME}" >/dev/null 2>&1; then
            echo -e "\n${GREEN}✅ Service is enabled (will start on boot)${NC}"
        else
            echo -e "\n${YELLOW}⚠️  Service is not enabled (won't start on boot)${NC}"
        fi
        ;;
    
    "logs")
        echo -e "${BLUE}📋 AI Companion Service Logs (Press Ctrl+C to exit)${NC}"
        echo "=================================================="
        if ! service_exists; then
            echo -e "${RED}❌ Service not installed.${NC}"
            exit 1
        fi
        journalctl --user -u "${SERVICE_NAME}" -f --no-pager
        ;;
    
    "enable")
        echo -e "${YELLOW}🔧 Enabling AI Companion service...${NC}"
        if ! service_exists; then
            echo -e "${RED}❌ Service not installed. Run '$0 install' first.${NC}"
            exit 1
        fi
        systemctl --user enable "${SERVICE_NAME}"
        echo -e "${GREEN}✅ Service enabled - will start automatically on boot${NC}"
        ;;
    
    "disable")
        echo -e "${YELLOW}🔧 Disabling AI Companion service...${NC}"
        if ! service_exists; then
            echo -e "${RED}❌ Service not installed.${NC}"
            exit 1
        fi
        systemctl --user disable "${SERVICE_NAME}"
        echo -e "${GREEN}✅ Service disabled - won't start automatically on boot${NC}"
        ;;
    
    "install")
        echo -e "${YELLOW}📦 Installing AI Companion systemd service...${NC}"
        if [[ -f "scripts/install-systemd-service.sh" ]]; then
            bash scripts/install-systemd-service.sh
        else
            echo -e "${RED}❌ Installation script not found${NC}"
            echo "Please run this from the AI Companion root directory."
            exit 1
        fi
        ;;
    
    "uninstall")
        echo -e "${YELLOW}🗑️  Uninstalling AI Companion service...${NC}"
        if service_exists; then
            # Stop service if running
            if [[ "$(get_status)" == "active" ]]; then
                systemctl --user stop "${SERVICE_NAME}"
                echo -e "${GREEN}✅ Service stopped${NC}"
            fi
            
            # Disable service
            systemctl --user disable "${SERVICE_NAME}" 2>/dev/null || true
            echo -e "${GREEN}✅ Service disabled${NC}"
            
            # Remove service file
            rm -f "$HOME/.config/systemd/user/${SERVICE_NAME}.service"
            systemctl --user daemon-reload
            echo -e "${GREEN}✅ Service file removed${NC}"
            
            echo -e "${GREEN}✅ AI Companion service uninstalled${NC}"
        else
            echo -e "${YELLOW}⚠️  Service not installed${NC}"
        fi
        ;;
    
    "help"|"-h"|"--help"|"")
        show_usage
        ;;
    
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        echo ""
        show_usage
        exit 1
        ;;
esac
