#!/usr/bin/env bash

# Server Setup Script for Multi-Tenant SaaS Backend
# This script prepares the Ubuntu server for the FastAPI application

set -e

APP_NAME="multi-tenant-saas"
APP_DIR="/home/ubuntu/$APP_NAME"
VENV_DIR="$APP_DIR/venv"
SERVICE_NAME="$APP_NAME"

echo "🔧 Setting up server for Multi-Tenant SaaS Backend..."

# Update system packages
echo "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Python 3.11 and pip
echo "Installing Python 3.11..."
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get install -y build-essential libpq-dev pkg-config nginx supervisor git curl

# Create application directory
echo "Creating application directory..."
mkdir -p $APP_DIR
cd $APP_DIR

# Create Python virtual environment
echo "Creating Python virtual environment..."
python3.11 -m venv $VENV_DIR
source $VENV_DIR/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "Running database migrations..."
source $VENV_DIR/bin/activate
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