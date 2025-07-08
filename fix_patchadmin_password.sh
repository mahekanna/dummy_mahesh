#!/bin/bash

# Quick fix script to set patchadmin password manually

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo -e "${RED}[ERROR]${NC} This script must be run as root (sudo)"
    exit 1
fi

echo "=== Fix patchadmin Password ==="
echo
echo "This script will set/reset the password for the patchadmin user."
echo

# Check if patchadmin user exists
if ! id -u patchadmin &>/dev/null; then
    echo -e "${RED}[ERROR]${NC} User 'patchadmin' does not exist"
    echo "Please run the deployment script first to create the user"
    exit 1
fi

# Prompt for password
echo -e "${YELLOW}[INFO]${NC} Enter new password for patchadmin user"
echo "Note: Password must be at least 8 characters long"
echo

# Method 1: Using passwd command (interactive)
echo -e "${GREEN}Method 1:${NC} Using passwd command (recommended)"
echo "You will be prompted twice for the password:"
passwd patchadmin

if [[ $? -eq 0 ]]; then
    echo
    echo -e "${GREEN}[SUCCESS]${NC} Password set successfully!"
    echo
    echo "You can now:"
    echo "1. SSH as patchadmin user"
    echo "2. Continue with deployment if it was interrupted"
    echo "3. Test with: su - patchadmin"
else
    echo
    echo -e "${RED}[ERROR]${NC} Failed to set password"
    echo
    echo -e "${YELLOW}Alternative method:${NC}"
    echo "Run this command manually:"
    echo "  echo 'patchadmin:YourNewPassword' | chpasswd"
fi