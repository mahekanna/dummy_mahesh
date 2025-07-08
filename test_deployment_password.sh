#!/bin/bash

# Test script to troubleshoot password capture issue

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=== Password Capture Test ==="
echo

# Test 1: Direct password capture
echo "Test 1: Direct password capture"
echo -n "Enter password: "
read -s PASSWORD1
echo
echo "You entered: ${#PASSWORD1} characters"
echo "Password value: '$PASSWORD1'"
echo

# Test 2: With function
prompt_password() {
    local prompt="$1"
    local password
    
    read -s -p "$(echo -e "${BLUE}[INPUT]${NC} $prompt: ")" password
    echo >&2  # Newline to stderr
    
    if [[ -n "$password" ]]; then
        echo -e "${GREEN}[✓]${NC} Password entered: $(printf '*%.0s' $(seq 1 ${#password}))" >&2
    else
        echo -e "${RED}[✗]${NC} No password entered" >&2
    fi
    
    echo "$password"
}

echo "Test 2: Function with stderr output"
PASSWORD2=$(prompt_password "Enter password")
echo "Captured password: ${#PASSWORD2} characters"
echo "Password value: '$PASSWORD2'"
echo

# Test 3: Check chpasswd
echo "Test 3: Testing chpasswd format"
if [[ -n "$PASSWORD2" ]]; then
    echo "Would run: echo 'patchadmin:$PASSWORD2' | chpasswd"
    echo "Password looks valid for chpasswd"
else
    echo "Password is empty - chpasswd would fail"
fi