# Deployment Guide for SSH Blackjack Game

## Option 1: Deploy on Custom Port (RECOMMENDED)

### Prerequisites
- Debian server with Go and Python3 installed
- Firewall configured to allow your chosen port

### Steps:

1. **Install Dependencies**
```bash
# On your Debian server
sudo apt update
sudo apt install golang-go python3 python3-pip python3-venv git

# Install required Go modules
go mod tidy
```

2. **Set up Python environment**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install textual
```

3. **Configure firewall**
```bash
# For port 2223 (or your chosen port)
sudo ufw allow 2223/tcp
sudo ufw status
```

4. **Create systemd service**
```bash
sudo nano /etc/systemd/system/ssh-blackjack.service
```

5. **Start and enable service**
```bash
sudo systemctl daemon-reload
sudo systemctl enable ssh-blackjack
sudo systemctl start ssh-blackjack
sudo systemctl status ssh-blackjack
```

## Option 2: Replace System SSH (ADVANCED - RISKY)

⚠️ **WARNING: This will disable normal SSH access to your server!**

Only do this if:
- You have console/physical access to the server
- You have a backup access method
- You understand the risks

### Steps:

1. **Disable system SSH daemon**
```bash
sudo systemctl stop ssh
sudo systemctl disable ssh
```

2. **Modify your Go code to use port 22**

3. **Set up as system service with proper permissions**

## Security Improvements Needed

Before deploying to production, consider adding:

1. **Authentication**: Currently anyone can connect
2. **Rate limiting**: Prevent abuse
3. **Logging**: Monitor connections and activities
4. **TLS/Security**: Add proper encryption
5. **User management**: Control who can access

## Monitoring and Maintenance

- Set up log rotation for chat logs
- Monitor system resources
- Regular backups of any persistent data
- Health checks and alerting

Would you like me to help you set up any of these options?
