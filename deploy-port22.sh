#!/bin/bash

# SSH Blackjack Deployment Script - PORT 22 VERSION (RISKY)
# ⚠️  WARNING: This will DISABLE your system's SSH daemon!
# ⚠️  Make sure you have console/physical access to your server!

set -e

echo "⚠️  WARNING: SSH PORT 22 DEPLOYMENT"
echo "===================================="
echo "This will DISABLE your system's SSH daemon and replace it with the game!"
echo "You will LOSE normal SSH access to this server!"
echo ""
read -p "Are you absolutely sure you want to continue? (type 'YES' to proceed): " confirm

if [ "$confirm" != "YES" ]; then
    echo "❌ Deployment cancelled. Good choice!"
    exit 1
fi

echo "⏰ Waiting 10 seconds... Press Ctrl+C to cancel!"
sleep 10

# Configuration
INSTALL_DIR="/opt/ssh-blackjack"
SERVICE_USER="gameuser"
PORT="22"

echo "🎮 Proceeding with risky deployment..."

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root (use sudo)"
   exit 1
fi

# Backup SSH configuration
echo "💾 Backing up SSH configuration..."
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup.$(date +%Y%m%d_%H%M%S)

# Stop and disable system SSH
echo "🛑 Stopping system SSH daemon..."
systemctl stop ssh || systemctl stop sshd
systemctl disable ssh || systemctl disable sshd

# Install dependencies
echo "📦 Installing dependencies..."
apt update
apt install -y golang-go python3 python3-pip python3-venv git

# Create service user
echo "👤 Creating service user..."
if ! id "$SERVICE_USER" &>/dev/null; then
    useradd --system --create-home --shell /bin/bash "$SERVICE_USER"
    echo "✅ Created user: $SERVICE_USER"
else
    echo "✅ User $SERVICE_USER already exists"
fi

# Create installation directory
echo "📁 Setting up installation directory..."
mkdir -p "$INSTALL_DIR"
chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"

# Copy files
echo "📋 Copying application files..."
cp main.go "$INSTALL_DIR/"
cp main.py "$INSTALL_DIR/"
cp go.mod "$INSTALL_DIR/"
cp go.sum "$INSTALL_DIR/"
cp button.tcss "$INSTALL_DIR/"
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"

# Update port to 22
echo "🔧 Updating port to 22..."
sed -i 's/:2223/:22/g' "$INSTALL_DIR/main.go"

# Set up Python virtual environment
echo "🐍 Setting up Python environment..."
sudo -u "$SERVICE_USER" bash -c "cd $INSTALL_DIR && python3 -m venv .venv"
sudo -u "$SERVICE_USER" bash -c "cd $INSTALL_DIR && source .venv/bin/activate && pip install textual"

# Install Go dependencies
echo "🔧 Installing Go dependencies..."
sudo -u "$SERVICE_USER" bash -c "cd $INSTALL_DIR && go mod tidy"

# Install systemd service (modified for port 22)
echo "⚙️  Installing systemd service..."
cat > /etc/systemd/system/ssh-blackjack.service << EOF
[Unit]
Description=SSH Blackjack Game Server (Port 22)
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/go run main.go
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$INSTALL_DIR /tmp

# Allow binding to port 22
AmbientCapabilities=CAP_NET_BIND_SERVICE

# Environment
Environment=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

[Install]
WantedBy=multi-user.target
EOF

# Start and enable service
systemctl daemon-reload
systemctl enable ssh-blackjack
systemctl start ssh-blackjack

# Check service status
echo "🏁 Deployment complete!"
echo ""
echo "⚠️  IMPORTANT WARNINGS:"
echo "- Normal SSH access is now DISABLED"
echo "- Only the blackjack game is accessible on port 22"
echo "- To restore normal SSH: sudo systemctl stop ssh-blackjack && sudo systemctl start ssh"
echo ""
echo "Service status:"
systemctl status ssh-blackjack --no-pager

echo ""
echo "🎮 Connect to your game:"
echo "ssh any_username@your_server_ip"
echo ""
echo "🔧 Emergency recovery:"
echo "If you get locked out, use console access and run:"
echo "sudo systemctl stop ssh-blackjack"
echo "sudo systemctl start ssh"
