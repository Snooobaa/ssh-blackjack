#!/usr/bin/env python3
"""
Test script to simulate chat message sending
"""
import json
import sys
import os

# Simulate environment variables that would be set by the Go server
os.environ["SSH_SESSION_ID"] = "test-session"
os.environ["SSH_USERNAME"] = "TestUser"

def test_chat_message():
    message = "Hello, this is a test message!"
    chat_msg = {
        "message": message,
        "username": "TestUser"
    }
    chat_json = json.dumps(chat_msg)
    print(f"CHAT:{chat_json}", flush=True)
    print(f"DEBUG: Sent chat message via stdout", file=sys.stderr, flush=True)

if __name__ == "__main__":
    test_chat_message()
