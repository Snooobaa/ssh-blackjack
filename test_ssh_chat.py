#!/usr/bin/env python3
"""
Test script that connects to SSH and attempts to send a chat message
"""
import subprocess
import time
import os

def test_ssh_chat():
    print("Testing SSH chat functionality...")
    
    # Create a test script that will be run via SSH
    test_script = '''
import sys
import json
import time

# Send a test chat message
message = "Test message from SSH client"
chat_msg = {
    "message": message,
    "username": "TestUser"
}
chat_json = json.dumps(chat_msg)
print(f"CHAT:{chat_json}", flush=True)

# Wait a bit for the message to be processed
time.sleep(2)
'''
    
    # Write the test script to a temporary file
    with open('/tmp/test_ssh_chat.py', 'w') as f:
        f.write(test_script)
    
    # Connect via SSH and run the test script
    try:
        result = subprocess.run([
            'ssh', '-o', 'StrictHostKeyChecking=no', 
            'localhost', '-p', '2223',
            'python3', '/tmp/test_ssh_chat.py'
        ], capture_output=True, text=True, timeout=10)
        
        print(f"SSH command output: {result.stdout}")
        print(f"SSH command errors: {result.stderr}")
        print(f"SSH command return code: {result.returncode}")
        
    except subprocess.TimeoutExpired:
        print("SSH connection timed out")
    except Exception as e:
        print(f"Error: {e}")
    
    # Check if chat file was created
    if os.path.exists('/tmp/ssh-chat.log'):
        print("\nChat log file contents:")
        with open('/tmp/ssh-chat.log', 'r') as f:
            print(f.read())
    else:
        print("Chat log file was not created")

if __name__ == "__main__":
    test_ssh_chat()
