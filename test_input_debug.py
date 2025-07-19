#!/usr/bin/env python3
"""
Test script to debug chat input issues
"""
import json
import time
import sys

def simulate_user_input():
    """Simulate what happens when a user types and presses enter"""
    
    # Test message
    message = "Manual test from debug script"
    username = "debug_input_test"
    session_id = "debug-input-123"
    
    print(f"Simulating user input: '{message}'")
    
    # This is what the Python app should do when user presses enter
    if message.strip():
        chat_msg = {
            "message": message.strip(),
            "username": username,
            "session_id": session_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        chat_json = json.dumps(chat_msg)
        
        print(f"Formatted message: {chat_json}")
        
        # Write to the messages file (what the Python app does)
        try:
            with open('/tmp/ssh-chat-messages.log', 'a') as f:
                f.write(f"{chat_json}\n")
                f.flush()
            print("✅ Message written to /tmp/ssh-chat-messages.log")
            
            # Also write to debug file
            with open('/tmp/python-chat-debug.log', 'a') as f:
                f.write(f"[{session_id}] Sent to file: {chat_json}\n")
                f.flush()
            print("✅ Debug log updated")
            
        except Exception as e:
            print(f"❌ Error writing message: {e}")
            return False
        
        # Wait a bit and check if Go server processed it
        time.sleep(2)
        
        try:
            with open('/tmp/ssh-chat.log', 'r') as f:
                lines = f.readlines()
                
            # Look for our message in the broadcast file
            our_message_found = False
            for line in lines:
                if line.strip():
                    try:
                        msg = json.loads(line.strip())
                        if msg.get('username') == username and message in msg.get('message', ''):
                            print(f"✅ Message found in broadcast file: {line.strip()}")
                            our_message_found = True
                            break
                    except json.JSONDecodeError:
                        continue
            
            if not our_message_found:
                print("❌ Message not found in broadcast file")
                print("Last few lines of broadcast file:")
                for line in lines[-3:]:
                    print(f"  {line.strip()}")
                    
        except Exception as e:
            print(f"❌ Error checking broadcast file: {e}")
            
    else:
        print("❌ Empty message, would not be sent")

if __name__ == "__main__":
    simulate_user_input()
