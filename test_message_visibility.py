#!/usr/bin/env python3
"""
Debug script to test if the issue is that users don't see their own messages
"""
import json
import time

def test_message_visibility():
    """Test what messages a user should see"""
    
    # Simulate the current user
    current_username = "testuser"
    
    # Read the current broadcast file
    try:
        with open('/tmp/ssh-chat.log', 'r') as f:
            lines = f.readlines()
        
        print(f"Messages that '{current_username}' should see:")
        print("=" * 50)
        
        messages_shown = 0
        messages_filtered = 0
        
        for line in lines:
            line = line.strip()
            if line:
                try:
                    msg = json.loads(line)
                    username = msg.get('username', 'Unknown')
                    message = msg.get('message', '')
                    timestamp = msg.get('timestamp', '')
                    
                    # This is the logic from the Python app
                    if username != current_username:
                        print(f"✅ SHOW: [{timestamp}] {username}: {message}")
                        messages_shown += 1
                    else:
                        print(f"❌ HIDE: [{timestamp}] {username}: {message} (own message)")
                        messages_filtered += 1
                        
                except json.JSONDecodeError:
                    print(f"⚠️  Invalid JSON: {line}")
        
        print("=" * 50)
        print(f"Messages shown: {messages_shown}")
        print(f"Messages filtered (own): {messages_filtered}")
        
        if messages_filtered > 0:
            print(f"\n🔍 DIAGNOSIS: User '{current_username}' won't see their own {messages_filtered} message(s)")
            print("This is why it might appear that 'no message appears' when they type!")
            
    except FileNotFoundError:
        print("❌ No chat log file found")
    except Exception as e:
        print(f"❌ Error reading chat log: {e}")

if __name__ == "__main__":
    test_message_visibility()
