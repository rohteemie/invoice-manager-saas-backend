#!/usr/bin/env bash

# Server Setup Script for Multi-Tenant SaaS Backend
# This script prepares the Ubuntu server for the FastAPI application

set -e

APP_NAME="multi-tenant-saas"
APP_DIR="/home/ubuntu/$APP_NAME"
VENV_DIR="$APP_DIR/venv"
SERVICE_NAME="$APP_NAME"

# Avoid interactive prompts during package installation
export DEBIAN_FRONTEND=noninteractive

# Wait for apt/dpkg locks to be released
wait_for_apt() {
    echo "Checking for apt/dpkg locks..."
    # Try to gently stop background apt units that may hold locks
    sudo systemctl stop apt-daily.service apt-daily-upgrade.service apt-daily.timer apt-daily-upgrade.timer 2>/dev/null || true

    # Wait until locks are free
    while sudo fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1 \
       || sudo fuser /var/lib/apt/lists/lock >/dev/null 2>&1 \
       || sudo fuser /var/lib/dpkg/lock >/dev/null 2>&1; do
        echo "apt is busy (locks present). Waiting 5s..."
        sleep 5
    done
}

echo "🔧 Setting up server for Multi-Tenant SaaS Backend..."

# Update system packages
echo "Updating system packages..."
wait_for_apt
sudo apt-get update -y
wait_for_apt
sudo apt-get upgrade -y -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold

# Install Python 3.11 and pip (with fallback to system python3 if 3.11 unavailable)
echo "Installing Python 3.11..."
wait_for_apt
if ! command -v python3.11 >/dev/null 2>&1; then
    if ! sudo apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip; then
        echo "Python 3.11 not available in repositories. Falling back to system python3."
        wait_for_apt
        sudo apt-get install -y python3 python3-venv python3-dev python3-pip
        PYTHON_BIN=python3
    else
        PYTHON_BIN=python3.11
    fi
else
    PYTHON_BIN=python3.11
fi

# Install system dependencies (include rsync for faster subsequent deploys)
echo "Installing system dependencies..."
wait_for_apt
sudo apt-get install -y build-essential libpq-dev pkg-config nginx supervisor git curl rsync

# Create application directory
echo "Creating application directory..."
mkdir -p $APP_DIR
cd $APP_DIR

# Create Python virtual environment
echo "Creating Python virtual environment..."
"$PYTHON_BIN" -m venv "$VENV_DIR"
source $VENV_DIR/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Create systemd service
echo "Creating systemd service..."
sudo mv ~/multi-tenant-saas.service /etc/systemd/system/
sudo systemctl daemon-reload

# Setup Nginx (optional - for reverse proxy)
echo "Setting up Nginx configuration..."
sudo tee /etc/nginx/sites-available/$APP_NAME > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx

# Set proper permissions
echo "Setting file permissions..."
sudo chown -R ubuntu:ubuntu $APP_DIR
chmod +x $APP_DIR/venv/bin/activate

# Create log directory
sudo mkdir -p /var/log/$APP_NAME
sudo chown ubuntu:ubuntu /var/log/$APP_NAME

echo "✅ Server setup completed successfully!"
echo "Application directory: $APP_DIR"
echo "Virtual environment: $VENV_DIR"
echo "Service name: $SERVICE_NAME"