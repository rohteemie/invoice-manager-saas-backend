# Deployment Guide for Multi-Tenant SaaS Backend

## Prerequisites

Before deploying, ensure you have:

1. **Server Requirements:**
   - Ubuntu 20.04+ server with sudo access
   - At least 2GB RAM and 20GB storage
   - SSH access configured
   - Server IP: Set DEPLOY_SERVER_IP environment variable or update in deploy.sh

2. **External Services:**
   - PostgreSQL database (already configured)
   - Redis server (already configured)

3. **Local Setup:**
   - SSH key configured for passwordless access to server
   - rsync installed locally

## Quick Deployment

1. **Configure deployment settings:**

   ```bash
   cp deploy/deploy.env.template deploy/deploy.env
   # Edit deploy/deploy.env with your server details
   ```

2. **Make deployment script executable:**

   ```bash
   chmod +x deploy/deploy.sh
   ```

3. **Run deployment:**

   ```bash
   ./deploy/deploy.sh
   ```

## Manual Deployment Steps

If you prefer to deploy manually:

### 1. Server Preparation

```bash
# Connect to server
ssh ubuntu@YOUR_SERVER_IP

# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip build-essential libpq-dev nginx \
    libpango-1.0-0 libpangocairo-1.0-0 libcairo2 libgdk-pixbuf-2.0-0 libffi8 shared-mime-info
```

### 2. Application Setup

```bash
# Create app directory
mkdir -p /home/ubuntu/multi-tenant-saas
cd /home/ubuntu/multi-tenant-saas

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Copy your application files (from local machine)
rsync -avz --exclude='.git' --exclude='__pycache__' ./ ubuntu@YOUR_SERVER_IP:/home/ubuntu/multi-tenant-saas/

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head
```

### 3. Service Configuration

```bash
# Copy and enable systemd service
sudo cp deploy/multi-tenant-saas.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable multi-tenant-saas
sudo systemctl start multi-tenant-saas
```

### 4. Nginx Setup (Optional)

```bash
# Configure Nginx as reverse proxy
sudo cp deploy/nginx.conf /etc/nginx/sites-available/multi-tenant-saas
sudo ln -s /etc/nginx/sites-available/multi-tenant-saas /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo systemctl restart nginx
```

## Environment Configuration

Update your `.env` file with production values:

```env
PROJECT_NAME=Multi-Tenant SaaS Backend API
SECRET_KEY=your-production-secret-key
ACCESS_TOKEN_EXPIRATION=30
DATABASE_URL=postgresql+psycopg2://user:pass@your-db-server:5432/dbname
REDIS_URL=redis://user:pass@your-redis-server:6379
```

## Post-Deployment

### Check Application Status

```bash
# Check service status
sudo systemctl status multi-tenant-saas

# View logs
sudo journalctl -u multi-tenant-saas -f

# Check if app is responding
curl http://localhost:8000/
```

### Access Your API

- API Base URL: `http://YOUR_SERVER_IP:8000`
- API Documentation: `http://YOUR_SERVER_IP:8000/docs`
- Health Check: `http://YOUR_SERVER_IP:8000/`

## Maintenance Commands

### Update Application

```bash
# Pull latest changes
git pull origin main

# Restart service
sudo systemctl restart multi-tenant-saas

# Run new migrations if any
source venv/bin/activate
alembic upgrade head
```

### Monitor Logs

```bash
# Real-time logs
sudo journalctl -u multi-tenant-saas -f

# Application logs
tail -f /var/log/multi-tenant-saas/access.log
tail -f /var/log/multi-tenant-saas/error.log
```

### Restart Services

```bash
# Restart application
sudo systemctl restart multi-tenant-saas

# Restart Nginx
sudo systemctl restart nginx
```

## Troubleshooting

### Common Issues

1. **Port 8000 already in use:**

   ```bash
   sudo lsof -i :8000
   sudo kill -9 <PID>
   ```

2. **Database connection issues:**
   - Verify DATABASE_URL in .env
   - Check network connectivity to PostgreSQL server
   - Ensure database credentials are correct

3. **Redis connection issues:**
   - Verify REDIS_URL in .env
   - Check network connectivity to Redis server

4. **Permission issues:**

   ```bash
   sudo chown -R ubuntu:ubuntu /home/ubuntu/multi-tenant-saas
   ```

### Security Considerations

1. **Firewall Setup:**

   ```bash
   sudo ufw allow ssh
   sudo ufw allow 80
   sudo ufw allow 443
   sudo ufw enable
   ```

2. **SSL Certificate (Production):**

   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```

## Scaling Considerations

- Use multiple workers in the systemd service
- Set up load balancer for multiple instances
- Monitor resource usage and scale accordingly
- Consider using Docker for containerization
