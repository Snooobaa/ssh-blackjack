#!/usr/bin/env python3
"""
Manual test to send a chat message directly to stdout with proper environment
"""
import json
import sys
import os

# Set environment variables to simulate SSH session
os.environ["SSH_SESSION_ID"] = "test-session-123"
os.environ["SSH_USERNAME"] = "TestUser"

def send_test_message():
    message = "Hello from manual test!"
    chat_msg = {
        "message": message,
        "username": "TestUser"
    }
    chat_json = json.dumps(chat_msg)
    
    print(f"CHAT:{chat_json}", flush=True)
    print("DEBUG: Test message sent", file=sys.stderr, flush=True)

if __name__ == "__main__":
    send_test_message()
