#!/usr/bin/env python3
"""
Test the exact flow that should happen when a user sends a chat message
"""
import json
import sys
import os

# Simulate the SSH environment
os.environ["SSH_SESSION_ID"] = "test-session-456"
os.environ["SSH_USERNAME"] = "TestUser2"

def simulate_chat_input():
    """Simulate what happens when a user types and submits a chat message"""
    
    # This simulates the message that would be sent by send_chat_message()
    message = "Hello from test simulation!"
    
    # This is exactly what send_chat_message() should do
    chat_msg = {
        "message": message.strip(),
        "username": "TestUser2"
    }
    chat_json = json.dumps(chat_msg)
    
    print(f"DEBUG: About to send: {chat_json}", file=sys.stderr, flush=True)
    print(f"CHAT:{chat_json}", flush=True)
    print(f"DEBUG: Message sent", file=sys.stderr, flush=True)

if __name__ == "__main__":
    simulate_chat_input()
