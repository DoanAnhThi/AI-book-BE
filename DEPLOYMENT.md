# 🚀 Deployment Guide - Gen Book API

## 📋 Files Overview

Các file đã được chuẩn bị cho deployment:

### Development Files
- `docker-compose.dev.yml` - Development environment với hot reload
- `env-dev.txt` - Template cho `.env.dev` (copy và điền API keys)
- `env-example.txt` - Template tất cả environment variables

### Production Files
- `docker-compose.prod.yml` - Production environment với nginx
- `Dockerfile.prod` - Multi-stage build cho production
- `env-prod.txt` - Template cho `.env.prod`
- `nginx/nginx.conf` - Nginx reverse proxy config
- `ssl/` - Thư mục cho SSL certificates

### Management
- `Makefile` - Scripts để chạy dev/prod environments
- `.gitignore` - Bảo mật các file nhạy cảm

## 🛠️ Quick Start

### 1. Setup Development Environment

```bash
# Copy environment template
cp env-dev.txt .env.dev

# Edit .env.dev với API keys thật của bạn
nano .env.dev

# Chạy development
make dev

# Hoặc build từ đầu
make dev-build
```

### 2. Setup Production Environment

```bash
# Trên VPS server:

# 1. Clone code
git clone <your-repo> genbook
cd genbook

# 2. Setup environment
cp env-prod.txt .env.prod

# 3. Edit production credentials
nano .env.prod

# 4. Build và deploy
make prod-deploy

# 5. Check logs
make prod-logs
```

## 📝 Environment Variables

### Required for Production:
```bash
# Database
DB_NAME=gen_book_prod
DB_USER=prod_user
DB_PASSWORD=your_strong_password

# AI APIs
OPENAI_API_KEY=sk-prod-...
REPLICATE_API_TOKEN=r8_prod_...

# Payment APIs (Live mode)
PAYPAL_CLIENT_ID=AZ_prod_...
PAYPAL_CLIENT_SECRET=EG_prod_...
# ... other payment credentials

# Email
SENDER_EMAIL=noreply@yourdomain.com
SENDER_PASSWORD=app_password
```

## 🔧 Makefile Commands

```bash
# Development
make dev          # Start dev environment
make dev-build    # Build & start dev
make dev-down     # Stop dev
make dev-logs     # View dev logs

# Production
make prod-build   # Build production image
make prod-deploy  # Build & deploy prod
make prod-down    # Stop prod
make prod-logs    # View prod logs

# Database
make db-dev       # Access dev database
make db-prod      # Access prod database

# Utilities
make clean        # Remove all containers & volumes
make setup-dev    # Setup dev environment files
make setup-prod   # Setup prod environment files
```

## 🌐 Production Deployment Steps

### 1. Server Requirements
- Ubuntu 20.04+ / CentOS 7+
- Docker & Docker Compose
- 2GB RAM minimum, 4GB recommended
- Domain name (cho SSL)

### 2. Security Setup
```bash
# Tạo user cho ứng dụng
sudo useradd -m -s /bin/bash genbook
sudo usermod -aG docker genbook

# Setup firewall
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 22
sudo ufw --force enable
```

### 3. SSL Certificate (Let's Encrypt)
```bash
# Install certbot
sudo apt install certbot

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com

# Copy to ssl folder
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./ssl/
sudo chown -R genbook:genbook ssl/
```

### 4. Environment Variables
```bash
# Set production secrets as environment variables
export DB_PASSWORD="your_db_password"
export OPENAI_API_KEY="sk-prod-..."
export PAYPAL_CLIENT_ID="AZ_prod_..."
# ... etc

# Hoặc dùng .env.prod file (less secure)
```

### 5. Deploy
```bash
# Build production image
make prod-build

# Start services
make prod

# Check health
curl http://localhost/health
```

## 🔍 Monitoring & Troubleshooting

### Check Service Status
```bash
# Container status
docker ps

# Logs
make prod-logs

# Check specific service
docker logs ai-system-prod
docker logs nginx-prod
```

### Common Issues

1. **Port 80/443 occupied**
   ```bash
   sudo netstat -tulpn | grep :80
   sudo systemctl stop apache2  # if running
   ```

2. **Database connection failed**
   ```bash
   make db-prod
   # Check if database exists and credentials correct
   ```

3. **SSL certificate issues**
   ```bash
   # Check certificate validity
   openssl x509 -in ssl/fullchain.pem -text -noout
   ```

## 🔄 Updates & Rollback

### Update Production
```bash
# Pull latest code
git pull origin main

# Rebuild & redeploy
make prod-deploy

# Check if healthy
curl http://localhost/health
```

### Rollback
```bash
# Stop current deployment
make prod-down

# Revert to previous commit
git checkout <previous-commit-hash>

# Redeploy
make prod-deploy
```

## 📞 Support

Nếu gặp vấn đề, kiểm tra:
1. Docker logs: `make prod-logs`
2. Environment variables
3. Network connectivity
4. File permissions
5. SSL certificates validity
