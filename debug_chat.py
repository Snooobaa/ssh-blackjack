#!/usr/bin/env python3
"""
Debug version of the chat functionality
"""
import json
import sys
import os
import time

def test_chat_functionality():
    print("=== CHAT DEBUG TEST ===", flush=True)
    
    # Check environment variables
    session_id = os.getenv("SSH_SESSION_ID", "local")
    username = os.getenv("SSH_USERNAME", "Player")
    
    print(f"Session ID: {session_id}", flush=True)
    print(f"Username: {username}", flush=True)
    
    # Test sending a chat message
    message = "Hello from debug test!"
    if session_id != "local":
        chat_msg = {
            "message": message,
            "username": username
        }
        chat_json = json.dumps(chat_msg)
        print(f"CHAT:{chat_json}", flush=True)
        print("Chat message sent via CHAT: protocol", flush=True)
    else:
        print("Running in local mode - no chat message sent", flush=True)
    
    print("=== END DEBUG TEST ===", flush=True)
    
    # Keep running to allow interaction
    try:
        while True:
            user_input = input("Type 'chat:message' to send a chat message, or 'quit' to exit: ")
            if user_input.lower() == 'quit':
                break
            elif user_input.startswith('chat:'):
                message = user_input[5:].strip()
                if message and session_id != "local":
                    chat_msg = {
                        "message": message,
                        "username": username
                    }
                    chat_json = json.dumps(chat_msg)
                    print(f"CHAT:{chat_json}", flush=True)
                    print(f"Sent: {message}", flush=True)
    except KeyboardInterrupt:
        pass
    except EOFError:
        pass

if __name__ == "__main__":
    test_chat_functionality()
