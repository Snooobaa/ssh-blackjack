#!/usr/bin/env python3
"""
Test script to verify the chat system is working correctly.
This script simulates user messages and verifies they are properly handled.
"""

import json
import time
import os

def test_chat_system():
    """Test the complete chat message flow"""
    
    print("Testing file-based chat system...")
    
    # Simulate a user sending a message (what Python app does)
    test_message = {
        "message": "Hello from test script!",
        "username": "test_user",
        "session_id": "test-session-123",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    # Write to the messages file (simulating Python app)
    with open('/tmp/ssh-chat-messages.log', 'a') as f:
        f.write(json.dumps(test_message) + '\n')
    
    print(f"✓ Sent message: {test_message['message']}")
    
    # Wait for Go server to process and write to chat log
    time.sleep(2)
    
    # Check if message appears in chat log (what Python apps read)
    if os.path.exists('/tmp/ssh-chat.log'):
        with open('/tmp/ssh-chat.log', 'r') as f:
            lines = f.readlines()
        
        found_message = False
        for line in lines:
            try:
                msg = json.loads(line.strip())
                if msg['username'] == 'test_user' and 'Hello from test script!' in msg['message']:
                    found_message = True
                    print(f"✓ Message received in chat log: {msg['message']}")
                    break
            except:
                continue
        
        if not found_message:
            print("✗ Message not found in chat log")
            print("Chat log contents:")
            print('\n'.join(lines))
        else:
            print("✓ Chat system working correctly!")
    else:
        print("✗ Chat log file not found")

if __name__ == "__main__":
    test_chat_system()
