#!/bin/bash

# Quick start script for SSH Blackjack server

echo "Starting SSH Blackjack Server with Chat..."
echo "Platform: $(uname -s) on $(uname -m)"

# Check if required tools are available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed or not in PATH"
    exit 1
fi

if ! command -v go &> /dev/null; then
    echo "Error: go is not installed or not in PATH" 
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment"
        exit 1
    fi
    echo "Installing dependencies..."
    .venv/bin/pip install textual
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install Python dependencies"
        exit 1
    fi
fi

# Build the server
echo "Building Go SSH server..."
go build -o ssh-server main.go
if [ $? -ne 0 ]; then
    echo "Error: Failed to build Go server"
    exit 1
fi

# Clean up any existing chat files
rm -f /tmp/ssh-chat.log

# Check if port is already in use
if command -v netstat &> /dev/null; then
    if netstat -ln | grep -q ":2223 "; then
        echo "Warning: Port 2223 appears to be in use"
        echo "You may need to kill existing processes or use a different port"
    fi
elif command -v ss &> /dev/null; then
    if ss -ln | grep -q ":2223 "; then
        echo "Warning: Port 2223 appears to be in use"
        echo "You may need to kill existing processes or use a different port"
    fi
fi

# Start the server
echo "Starting server on port 2223..."
echo "Connect with: ssh localhost -p 2223"
echo "         or: ssh {username}@localhost -p 2223"
echo "Press Ctrl+C to stop the server"
echo ""
echo "For WSL users: You can connect from Windows using:"
echo "  ssh localhost -p 2223"
echo "  or from outside WSL using your WSL IP address"
echo ""

./ssh-server
