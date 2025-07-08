#!/bin/bash

# Test script for password input issues

echo "=== Password Input Test Script ==="
echo

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Test 1: Basic hidden input
echo "Test 1: Basic hidden input"
echo -n "Type something (hidden): "
if read -s test1; then
    echo
    echo -e "${GREEN}✓ Hidden input works${NC}"
    echo "You typed: ${#test1} characters"
else
    echo
    echo -e "${RED}✗ Hidden input failed${NC}"
fi
echo

# Test 2: Hidden input with prompt
echo "Test 2: Hidden input with -p flag"
if read -s -p "Type something (hidden with prompt): " test2; then
    echo
    echo -e "${GREEN}✓ Hidden input with prompt works${NC}"
    echo "You typed: ${#test2} characters"
else
    echo
    echo -e "${RED}✗ Hidden input with prompt failed${NC}"
fi
echo

# Test 3: Visible input
echo "Test 3: Visible input"
read -p "Type something (visible): " test3
echo -e "${GREEN}✓ Visible input works${NC}"
echo "You typed: $test3"
echo

# Test 4: Terminal type
echo "Test 4: Environment information"
echo "TERM=$TERM"
echo "Shell=$SHELL"
echo "TTY=$(tty)"
echo

# Test 5: stty method
echo "Test 5: Alternative hidden input using stty"
echo -n "Type something (stty method): "
stty -echo
read test5
stty echo
echo
echo -e "${GREEN}✓ stty method complete${NC}"
echo "You typed: ${#test5} characters"
echo

# Recommendation
echo "=== RECOMMENDATION ==="
if [[ -n "$test1" ]] || [[ -n "$test2" ]]; then
    echo -e "${GREEN}Hidden password input should work fine.${NC}"
    echo "If you're still having issues during deployment, try:"
    echo "1. Run the deployment script directly in terminal (not through screen/tmux)"
    echo "2. Make sure you're using a standard terminal emulator"
else
    echo -e "${YELLOW}Hidden password input may not work properly.${NC}"
    echo "During deployment, choose 'visible password input' when prompted."
fi