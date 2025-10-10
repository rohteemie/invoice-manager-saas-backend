#!/usr/bin/env bash

# Multi-Tenant SaaS Backend Deployment Script
# This script automates the deployment of the FastAPI application

set -e  # Exit on any error

# Load deployment configuration if available
if [ -f "deploy/deploy.env" ]; then
    source deploy/deploy.env
    echo "📋 Loaded configuration from deploy/deploy.env"
fi

# Configuration - Set these values for your deployment
SERVER_IP="${DEPLOY_SERVER_IP:-your.server.ip.here}"
SERVER_USER="${DEPLOY_SERVER_USER:-ubuntu}"
APP_NAME="multi-tenant-saas"
APP_DIR="/home/ubuntu/$APP_NAME"
VENV_DIR="$APP_DIR/venv"
SERVICE_NAME="$APP_NAME"

# Validate configuration
if [ "$SERVER_IP" = "your.server.ip.here" ]; then
    echo "❌ Please set DEPLOY_SERVER_IP in deploy/deploy.env or as environment variable"
    echo "Copy deploy/deploy.env.template to deploy/deploy.env and configure it"
    exit 1
fi

echo "🚀 Starting deployment of Multi-Tenant SaaS Backend..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Copy application files to server
print_status "Copying application files to server..."
rsync -avz --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='.env' \
    ./ $SERVER_USER@$SERVER_IP:$APP_DIR/

# Step 2: Copy environment file
print_status "Copying environment configuration..."
scp .env $SERVER_USER@$SERVER_IP:$APP_DIR/

# Step 3: Copy deployment scripts
print_status "Copying deployment scripts..."
scp deploy/server_setup.sh $SERVER_USER@$SERVER_IP:~/
scp deploy/$SERVICE_NAME.service $SERVER_USER@$SERVER_IP:~/

# Step 4: Execute server setup
print_status "Setting up server environment..."
ssh $SERVER_USER@$SERVER_IP "chmod +x ~/server_setup.sh && ~/server_setup.sh"

# Step 5: Start the application
print_status "Starting the application..."
ssh $SERVER_USER@$SERVER_IP "sudo systemctl enable $SERVICE_NAME && sudo systemctl start $SERVICE_NAME"

# Step 6: Check status
print_status "Checking application status..."
ssh $SERVER_USER@$SERVER_IP "sudo systemctl status $SERVICE_NAME --no-pager"

print_status "🎉 Deployment completed successfully!"
print_status "Your API is now running at: http://$SERVER_IP:8000"
print_status "API Documentation: http://$SERVER_IP:8000/docs"

echo ""
echo "To check logs, run:"
echo "ssh $SERVER_USER@$SERVER_IP 'sudo journalctl -u $SERVICE_NAME -f'"