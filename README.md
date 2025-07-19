# SSH Blackjack with Chat

A terminal-based blackjack game with real-time chat functionality, accessible via SSH.

## Features

- **Blackjack Game**: Play blackjack with standard rules
- **Real-time Chat**: Chat with other connected players
- **SSH Access**: Connect from anywhere using SSH
- **Multi-user**: Multiple players can connect simultaneously
- **No Authentication**: Anonymous access (users identified by IP)

## Requirements

- Go 1.24.5+
- Python 3.8+
- Virtual environment with Textual installed

## Setup

1. **Install Dependencies**:
   ```bash
   # Go dependencies
   go mod tidy
   
   # Python dependencies (automated in start.sh)
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install textual
   ```

2. **Quick Start**:
   ```bash
   # Make scripts executable
   chmod +x start.sh connect.sh wsl-helper.sh
   
   # Start the server (handles all setup automatically)
   ./start.sh
   ```

3. **Manual Build** (optional):
   ```bash
   go build -o ssh-server main.go
   ./ssh-server
   ```

## Usage

### WSL (Windows Subsystem for Linux) Users

The scripts are fully compatible with WSL. Use the provided helper scripts:

```bash
# Start the server
./start.sh

# Get connection information (in another terminal)
./wsl-helper.sh

# Interactive connection helper
./connect.sh
```

**WSL Connection Options:**
- **From within WSL**: `ssh localhost -p 2223`
- **From Windows**: `ssh {WSL_IP} -p 2223` (get IP with `./wsl-helper.sh`)
- **Custom username**: `ssh {username}@localhost -p 2223`

### Connecting

**Simple Connection:**
```bash
ssh localhost -p 2223
```

**With Username:**
```bash
ssh {username}@localhost -p 2223
```

**Using Helper Scripts:**
```bash
# Interactive connection menu
./connect.sh

# WSL connection info
./wsl-helper.sh
```

No password is required - users are automatically identified by their SSH username or IP address.

### Playing Blackjack

- Click "Deal" to start a new hand
- Use "Hit" to draw another card
- Use "Stand" to end your turn
- The dealer follows standard blackjack rules (hits on 16, stands on 17)

### Chat Features

- **Chat Panel**: Located on the right side of the screen
- **Sending Messages**: Type in the chat input box and press Enter
- **Real-time Updates**: See messages from all connected players instantly
- **User Identification**: Each user is identified by their IP address

### Controls

- **Tab**: Navigate between game buttons and chat input
- **Enter**: Send chat message (when chat input is focused)
- **Ctrl+C**: Quit the application

## Architecture

The system consists of two main components:

1. **Go SSH Server** (`main.go`):
   - Handles multiple SSH connections
   - Manages chat message broadcasting
   - Spawns Python blackjack instances for each connection

2. **Python Blackjack App** (`main.py`):
   - Textual-based UI for the game and chat
   - Handles game logic and user interactions
   - Communicates with SSH server for chat messages

### Communication Protocol

- Chat messages are sent from Python to Go via stdout with `CHAT:` prefix
- Go server broadcasts messages to all sessions via stdin with `CHATMSG:` prefix
- JSON format is used for message serialization

## Development

### Testing Locally

You can run the Python app directly for local testing:
```bash
source .venv/bin/activate
python main.py
```

### Multiple Connections

To test with multiple users, open multiple terminal windows and connect via SSH:
```bash
# Terminal 1
ssh localhost -p 2223

# Terminal 2  
ssh localhost -p 2223

# etc.
```

## Troubleshooting

### General Issues
- **Port in use**: Change the port in `main.go` if 2223 is already in use
- **Python not found**: Ensure the virtual environment path is correct in `main.go`
- **Chat not working**: Check that file permissions allow writing to `/tmp/ssh-chat.log`

### WSL-Specific Issues
- **Connection refused from Windows**: 
  - Check Windows Firewall settings for port 2223
  - Ensure WSL networking is properly configured
  - Get WSL IP with `./wsl-helper.sh` and use that instead of localhost
- **Python virtual environment issues**: 
  - WSL should use Linux-style paths (already handled in scripts)
  - If issues persist, manually create venv: `python3 -m venv .venv`
- **Permission issues**: 
  - Make scripts executable: `chmod +x *.sh`
  - Ensure `/tmp` directory is writable

### Testing Multiple Connections
```bash
# Terminal 1: Start server
./start.sh

# Terminal 2: First user
ssh user1@localhost -p 2223

# Terminal 3: Second user  
ssh user2@localhost -p 2223

# Or use the helper
./connect.sh
```

## Security Note

This implementation is for demonstration purposes. In production:
- Add proper authentication
- Implement user management
- Add rate limiting
- Secure the SSH configuration
- Add input validation and sanitization