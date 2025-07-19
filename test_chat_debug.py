#!/usr/bin/env python3
import json
import time
import os

def send_test_message():
    """Send a test message to the chat system"""
    chat_msg = {
        "message": "Hello from debug test!",
        "username": "debug_user",
        "session_id": "debug-session-123",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    chat_json = json.dumps(chat_msg)
    
    print(f"Sending message: {chat_json}")
    
    # Write to the file that Go server monitors
    try:
        with open('/tmp/ssh-chat-messages.log', 'a') as f:
            f.write(f"{chat_json}\n")
            f.flush()
        print("Message written to /tmp/ssh-chat-messages.log")
    except Exception as e:
        print(f"Error writing to messages file: {e}")
    
    # Check if Go server wrote to the broadcast file
    time.sleep(2)
    try:
        if os.path.exists('/tmp/ssh-chat.log'):
            with open('/tmp/ssh-chat.log', 'r') as f:
                content = f.read()
                print(f"Broadcast file content: {content}")
        else:
            print("Broadcast file doesn't exist yet")
    except Exception as e:
        print(f"Error reading broadcast file: {e}")

if __name__ == "__main__":
    send_test_message()
