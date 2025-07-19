#!/bin/bash

# Connection script for SSH Blackjack server

echo "SSH Blackjack Connection Helper"
echo "==============================="

# Check if server is running
if ! pgrep -f ssh-server > /dev/null; then
    echo "Error: Server is not running!"
    echo "Start the server first with: ./start.sh"
    exit 1
fi

echo "Server is running!"
echo ""

# Show connection options
echo "Choose connection method:"
echo "1) Connect as current user ($(whoami))"
echo "2) Connect with custom username"
echo "3) Show WSL connection info"
echo "4) Exit"
echo ""

read -p "Enter choice (1-4): " choice

case $choice in
    1)
        echo "Connecting as $(whoami)..."
        ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null localhost -p 2223
        ;;
    2)
        read -p "Enter username: " username
        echo "Connecting as $username..."
        ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $username@localhost -p 2223
        ;;
    3)
        ./wsl-helper.sh
        ;;
    4)
        echo "Goodbye!"
        exit 0
        ;;
    *)
        echo "Invalid choice. Connecting with default settings..."
        ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null localhost -p 2223
        ;;
esac
