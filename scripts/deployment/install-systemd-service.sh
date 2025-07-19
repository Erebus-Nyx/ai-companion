#!/bin/bash

# AI Companion Systemd Service Installation Script
# This script sets up AI Companion to run as a systemd service

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="ai2d_chat"
SERVICE_FILE="ai2d_chat.service"
INSTALL_DIR="/home/nyx/ai2d_chat"
VENV_PATH="/home/nyx/ai2d_chat/.venv"
USER="nyx"
GROUP="nyx"

echo -e "${BLUE}🤖 AI Companion Systemd Service Installer${NC}"
echo "============================================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}❌ This script should not be run as root${NC}"
   echo "Please run as the user who will run the service (nyx)"
   exit 1
fi

# Check if we're in the right directory
if [[ ! -f "systemd/${SERVICE_FILE}" ]]; then
    echo -e "${RED}❌ Service file not found. Please run this script from the AI Companion root directory.${NC}"
    exit 1
fi

# Check if virtual environment exists
if [[ ! -d "${VENV_PATH}" ]]; then
    echo -e "${RED}❌ Virtual environment not found at ${VENV_PATH}${NC}"
    echo "Please ensure the virtual environment is set up first."
    exit 1
fi

# Check if ai2d_chat is installed
if [[ ! -f "${VENV_PATH}/bin/ai2d_chat" ]]; then
    echo -e "${RED}❌ ai2d_chat executable not found in virtual environment${NC}"
    echo "Please install the package first: pip install -e ."
    exit 1
fi

echo -e "${YELLOW}📋 Pre-installation checks...${NC}"

# Create systemd user directory if it doesn't exist
USER_SYSTEMD_DIR="$HOME/.config/systemd/user"
mkdir -p "$USER_SYSTEMD_DIR"

echo -e "${GREEN}✅ Systemd user directory ready${NC}"

# Copy service file to user systemd directory
echo -e "${YELLOW}📝 Installing service file...${NC}"
cp "systemd/${SERVICE_FILE}" "$USER_SYSTEMD_DIR/"

# Update service file with actual paths
sed -i "s|/home/nyx/ai2d_chat|${INSTALL_DIR}|g" "$USER_SYSTEMD_DIR/${SERVICE_FILE}"
sed -i "s|User=nyx|User=${USER}|g" "$USER_SYSTEMD_DIR/${SERVICE_FILE}"
sed -i "s|Group=nyx|Group=${GROUP}|g" "$USER_SYSTEMD_DIR/${SERVICE_FILE}"

echo -e "${GREEN}✅ Service file installed${NC}"

# Reload systemd daemon
echo -e "${YELLOW}🔄 Reloading systemd daemon...${NC}"
systemctl --user daemon-reload

# Enable the service
echo -e "${YELLOW}🔧 Enabling service...${NC}"
systemctl --user enable "${SERVICE_NAME}"

# Enable lingering to allow user services to run without login
echo -e "${YELLOW}🔐 Enabling user lingering...${NC}"
sudo loginctl enable-linger "${USER}"

echo -e "${GREEN}✅ Service installed and enabled successfully!${NC}"
echo ""
echo -e "${BLUE}📖 Usage Commands:${NC}"
echo "  Start service:    systemctl --user start ${SERVICE_NAME}"
echo "  Stop service:     systemctl --user stop ${SERVICE_NAME}"
echo "  Restart service:  systemctl --user restart ${SERVICE_NAME}"
echo "  Check status:     systemctl --user status ${SERVICE_NAME}"
echo "  View logs:        journalctl --user -u ${SERVICE_NAME} -f"
echo "  Disable service:  systemctl --user disable ${SERVICE_NAME}"
echo ""
echo -e "${BLUE}🌐 Service Configuration:${NC}"
echo "  Service will run on: http://localhost:19443"
echo "  Live2D interface:   http://localhost:19443/live2d"
echo "  User:              ${USER}"
echo "  Working Directory: ${INSTALL_DIR}"
echo ""
echo -e "${YELLOW}⚠️  Note: The service will start automatically on boot${NC}"
echo -e "${YELLOW}   To start it now, run: systemctl --user start ${SERVICE_NAME}${NC}"
