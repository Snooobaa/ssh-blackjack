#!/bin/bash

# SSH Blackjack Deployment Script for Debian
set -e

# Configuration
INSTALL_DIR="/opt/ssh-blackjack"
SERVICE_USER="gameuser"
PORT="2223"  # Change this if you want a different port

echo "🎮 SSH Blackjack Deployment Script"
echo "===================================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root (use sudo)"
   exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
apt update
apt install -y golang-go python3 python3-pip python3-venv git ufw

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

# Copy files (assuming script is run from the project directory)
echo "📋 Copying application files..."
cp main.go "$INSTALL_DIR/"
cp main.py "$INSTALL_DIR/"
cp go.mod "$INSTALL_DIR/"
cp go.sum "$INSTALL_DIR/"
cp button.tcss "$INSTALL_DIR/"
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"

# Set up Python virtual environment
echo "🐍 Setting up Python environment..."
sudo -u "$SERVICE_USER" bash -c "cd $INSTALL_DIR && python3 -m venv .venv"
sudo -u "$SERVICE_USER" bash -c "cd $INSTALL_DIR && source .venv/bin/activate && pip install textual"

# Update port in Go code if different from default
if [ "$PORT" != "2223" ]; then
    echo "🔧 Updating port to $PORT..."
    sed -i "s/:2223/:$PORT/g" "$INSTALL_DIR/main.go"
fi

# Install Go dependencies
echo "🔧 Installing Go dependencies..."
sudo -u "$SERVICE_USER" bash -c "cd $INSTALL_DIR && go mod tidy"

# Configure firewall
echo "🔥 Configuring firewall..."
ufw allow "$PORT/tcp"
echo "✅ Opened port $PORT/tcp"

# Install systemd service
echo "⚙️  Installing systemd service..."
cp ssh-blackjack.service /etc/systemd/system/
sed -i "s|WorkingDirectory=.*|WorkingDirectory=$INSTALL_DIR|g" /etc/systemd/system/ssh-blackjack.service
sed -i "s|User=.*|User=$SERVICE_USER|g" /etc/systemd/system/ssh-blackjack.service
sed -i "s|Group=.*|Group=$SERVICE_USER|g" /etc/systemd/system/ssh-blackjack.service

# Start and enable service
systemctl daemon-reload
systemctl enable ssh-blackjack
systemctl start ssh-blackjack

# Check service status
echo "🏁 Deployment complete!"
echo ""
echo "Service status:"
systemctl status ssh-blackjack --no-pager

echo ""
echo "📋 Summary:"
echo "- Game server installed in: $INSTALL_DIR"
echo "- Running as user: $SERVICE_USER"
echo "- Listening on port: $PORT"
echo "- Service name: ssh-blackjack"
echo ""
echo "🔧 Management commands:"
echo "- Check status: sudo systemctl status ssh-blackjack"
echo "- View logs: sudo journalctl -u ssh-blackjack -f"
echo "- Restart: sudo systemctl restart ssh-blackjack"
echo "- Stop: sudo systemctl stop ssh-blackjack"
echo ""
echo "🎮 Connect to your game:"
echo "ssh any_username@your_server_ip -p $PORT"
