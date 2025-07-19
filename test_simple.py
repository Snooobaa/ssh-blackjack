#!/usr/bin/env python3
"""
Simple test app that just sends a chat message and exits
"""
import json
import sys
import time

def main():
    # Send a test chat message
    chat_msg = {
        "message": "Test message from Python",
        "username": "TestUser"
    }
    chat_json = json.dumps(chat_msg)
    
    print("Starting test...")
    print(f"CHAT:{chat_json}")
    print("Test completed.")
    
    # Keep running for a bit to allow Go server to process
    time.sleep(2)

if __name__ == "__main__":
    main()
