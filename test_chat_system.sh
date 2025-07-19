#!/bin/bash

echo "Testing SSH Blackjack Chat Functionality"
echo "========================================"

# Start monitoring the chat file
echo "Starting chat file monitor..."
(
    while true; do
        if [ -f /tmp/ssh-chat.log ]; then
            echo "--- Chat Log Contents ---"
            cat /tmp/ssh-chat.log
            echo "--- End of Chat Log ---"
            break
        fi
        sleep 1
    done
) &
MONITOR_PID=$!

echo "Chat monitoring started with PID: $MONITOR_PID"

# Wait a bit for setup
sleep 2

echo "Test completed. Chat file monitoring continues in background."
echo "You can now test the chat functionality by connecting to: ssh localhost -p 2223"
echo "To stop monitoring, run: kill $MONITOR_PID"
