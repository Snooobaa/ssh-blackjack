#!/bin/bash

# WSL-specific helper script for SSH Blackjack

echo "SSH Blackjack WSL Helper"
echo "======================="

# Get WSL IP address
WSL_IP=$(hostname -I | awk '{print $1}')
echo "WSL IP Address: $WSL_IP"

# Check if server is running
if ! pgrep -f ssh-server > /dev/null; then
    echo ""
    echo "Server is not running. Start it with: ./start.sh"
    exit 1
fi

echo ""
echo "Server is running! Connect using:"
echo ""
echo "From within WSL:"
echo "  ssh localhost -p 2223"
echo "  ssh {username}@localhost -p 2223"
echo ""
echo "From Windows or external machines:"
echo "  ssh $WSL_IP -p 2223"
echo "  ssh {username}@$WSL_IP -p 2223"
echo ""
echo "Note: You may need to configure Windows Firewall"
echo "      to allow connections to port 2223"
echo ""
echo "Active connections:"
ps aux | grep -v grep | grep ssh-server | wc -l | xargs echo "  SSH server processes:"
lsof -i :2223 2>/dev/null | grep LISTEN | wc -l | xargs echo "  Listening on port 2223:"
