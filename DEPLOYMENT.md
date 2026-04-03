# 🚀 Deployment Guide

Complete deployment instructions for the Agentic Arbitrage Factory.

## Table of Contents

1. [Deployment Overview](#deployment-overview)
2. [Local Deployment](#local-deployment)
3. [Cloud Deployment](#cloud-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Production Setup](#production-setup)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)

---

## Deployment Overview

The factory can be deployed in multiple configurations:

| Environment | Use Case | Database | Deployment |
|-------------|----------|----------|------------|
| Local | Development | SQLite | Local Python |
| VPS | Small scale | SQLite/PostgreSQL | systemd |
| Docker | Containerized | PostgreSQL | Docker Compose |
| Kubernetes | Large scale | PostgreSQL | K8s cluster |

### Architecture Decisions

- **SQLite** for local/small scale (zero config)
- **PostgreSQL** for production (concurrency, reliability)
- **Cloudflare Pages** for site hosting (edge network, cheap)
- **Cloudflare D1** for site databases (serverless, scalable)

---

## Local Deployment

### Prerequisites

- Python 3.8+
- pip
- Git

### Installation

```bash
# Clone repository
git clone <repository-url>
cd agentic_arbitrage_factory

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Create data directory
mkdir -p data

# Run factory
python factory.py run
```

### Directory Structure

```
agentic_arbitrage_factory/
├── venv/                    # Virtual environment
├── data/                    # Database and logs
│   ├── factory.db          # SQLite database
│   └── factory.log         # Log files
├── sites/                   # Generated sites
└── ...
```

### Running Modes

**One-time run:**
```bash
python factory.py run
```

**Continuous mode:**
```bash
python factory.py continuous
```

**With nohup (background):**
```bash
nohup python factory.py continuous > factory.log 2>&1 &
```

---

## Cloud Deployment

### VPS (DigitalOcean, Linode, AWS EC2)

#### 1. Provision Server

**Recommended specs:**
- 2 vCPU
- 4GB RAM
- 50GB SSD
- Ubuntu 22.04 LTS

#### 2. Server Setup

```bash
# SSH into server
ssh user@your-server-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python
sudo apt install python3 python3-pip python3-venv git -y

# Create app directory
sudo mkdir -p /opt/agentic_factory
sudo chown $USER:$USER /opt/agentic_factory

# Clone repository
cd /opt/agentic_factory
git clone <repository-url> .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create data directory
mkdir -p data
```

#### 3. Environment Configuration

```bash
# Create .env file
cat > .env << EOF
# Optional API keys
REDDIT_CLIENT_ID=your_id
REDDIT_CLIENT_SECRET=your_secret
OPENAI_API_KEY=your_key
CLOUDFLARE_API_TOKEN=your_token
GITHUB_TOKEN=your_token

# Database (optional - defaults to SQLite)
DATABASE_URL=sqlite:///data/factory.db

# Logging
LOG_LEVEL=INFO
EOF
```

#### 4. Systemd Service

Create service file:

```bash
sudo cat > /etc/systemd/system/agentic-factory.service << EOF
[Unit]
Description=Agentic Arbitrage Factory
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/agentic_factory
Environment=PATH=/opt/agentic_factory/venv/bin
ExecStart=/opt/agentic_factory/venv/bin/python factory.py continuous
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

Start service:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable agentic-factory

# Start service
sudo systemctl start agentic-factory

# Check status
sudo systemctl status agentic-factory

# View logs
sudo journalctl -u agentic-factory -f
```

#### 5. Nginx Reverse Proxy (Optional)

```bash
# Install nginx
sudo apt install nginx -y

# Create config
sudo cat > /etc/nginx/sites-available/agentic-factory << EOF
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/agentic-factory /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Docker Deployment

### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directory
RUN mkdir -p data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

# Run factory
CMD ["python", "factory.py", "continuous"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  factory:
    build: .
    container_name: agentic-factory
    restart: unless-stopped
    volumes:
      - ./data:/app/data
      - ./sites:/app/sites
    environment:
      - LOG_LEVEL=INFO
      - DATABASE_URL=sqlite:///data/factory.db
      # Add other env vars
    networks:
      - factory-network

  # Optional: PostgreSQL
  postgres:
    image: postgres:15
    container_name: factory-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: factory
      POSTGRES_PASSWORD: your_password
      POSTGRES_DB: factory
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - factory-network

volumes:
  postgres-data:

networks:
  factory-network:
    driver: bridge
```

### Docker Commands

```bash
# Build image
docker build -t agentic-factory .

# Run container
docker run -d \
  --name agentic-factory \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/sites:/app/sites \
  agentic-factory

# View logs
docker logs -f agentic-factory

# Stop container
docker stop agentic-factory

# Remove container
docker rm agentic-factory

# Using Docker Compose
docker-compose up -d
docker-compose logs -f
docker-compose down
```

---

## Production Setup

### PostgreSQL Database

#### 1. Install PostgreSQL

```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib -y

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### 2. Create Database

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database
CREATE DATABASE factory;
CREATE USER factory WITH ENCRYPTED PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE factory TO factory;

# Exit
\q
```

#### 3. Update Configuration

```bash
# .env file
DATABASE_URL=postgresql://factory:your_password@localhost/factory
```

### Cloudflare Setup

#### 1. Create Account

1. Sign up at [cloudflare.com](https://cloudflare.com)
2. Add your domain
3. Update nameservers

#### 2. Get API Token

1. Go to [dash.cloudflare.com/profile/api-tokens](https://dash.cloudflare.com/profile/api-tokens)
2. Create token with permissions:
   - Zone:Read
   - Page Rules:Edit
   - Workers Scripts:Edit
   - Account:Read
   - D1:Edit

#### 3. Configure Factory

```bash
# .env file
CLOUDFLARE_API_TOKEN=your_token
CLOUDFLARE_ACCOUNT_ID=your_account_id
```

### GitHub Setup

#### 1. Create Token

1. Go to [github.com/settings/tokens](https://github.com/settings/tokens)
2. Generate new token with scopes:
   - repo (full control)
   - workflow

#### 2. Configure Factory

```bash
# .env file
GITHUB_TOKEN=ghp_your_token
```

---

## Monitoring & Maintenance

### Health Checks

```bash
# Check factory status
python factory.py status

# Check database
sqlite3 data/factory.db "SELECT COUNT(*) FROM opportunities;"

# Check logs
tail -f data/factory.log
```

### Backup Strategy

#### SQLite Backup

```bash
# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups/factory"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
sqlite3 /opt/agentic_factory/data/factory.db ".backup '$BACKUP_DIR/factory_$DATE.db'"

# Compress backup
gzip $BACKUP_DIR/factory_$DATE.db

# Keep only last 30 days
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
```

#### PostgreSQL Backup

```bash
# pg_dump backup
pg_dump -U factory -d factory > factory_$(date +%Y%m%d).sql

# Automated with cron
0 2 * * * pg_dump -U factory -d factory | gzip > /backups/factory_$(date +\%Y\%m\%d).sql.gz
```

### Log Rotation

```bash
# Install logrotate
sudo apt install logrotate -y

# Create config
sudo cat > /etc/logrotate.d/agentic-factory << EOF
/opt/agentic_factory/data/factory.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 $USER $USER
}
EOF
```

### Performance Monitoring

```bash
# Monitor resource usage
htop

# Monitor disk usage
df -h

# Monitor database size
ls -lh data/factory.db

# Monitor process
ps aux | grep factory
```

---

## Troubleshooting

### Problem: Service won't start

**Check:**
```bash
# Check service status
sudo systemctl status agentic-factory

# Check logs
sudo journalctl -u agentic-factory -n 100

# Check Python syntax
python -m py_compile factory.py

# Check permissions
ls -la /opt/agentic_factory
```

**Fix:**
```bash
# Fix permissions
sudo chown -R $USER:$USER /opt/agentic_factory

# Restart service
sudo systemctl restart agentic-factory
```

### Problem: Database locked

**Cause:** SQLite doesn't support concurrent writes

**Fix:**
```bash
# Switch to PostgreSQL
# OR
# Reduce concurrency in config
max_concurrent_sites = 5
```

### Problem: Out of memory

**Check:**
```bash
# Check memory usage
free -h

# Check OOM kills
dmesg | grep -i "out of memory"
```

**Fix:**
```bash
# Add swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Reduce concurrency
max_concurrent_sites = 10
```

### Problem: Rate limited by Reddit

**Check:**
```bash
# Check logs for 429 errors
grep "429" data/factory.log
```

**Fix:**
```bash
# Reduce rate in config
reddit_rate_limit = 0.5  # 1 request per 2 seconds

# Or use mock data temporarily
# (Factory auto-falls back to mock data)
```

### Problem: Sites not deploying

**Check:**
```bash
# Check Cloudflare token
curl -X GET "https://api.cloudflare.com/client/v4/user/tokens/verify" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN"

# Check GitHub token
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user
```

**Fix:**
```bash
# Update tokens in .env
# Restart service
sudo systemctl restart agentic-factory
```

---

## Security Checklist

- [ ] Use strong database passwords
- [ ] Rotate API keys regularly
- [ ] Enable firewall (ufw)
- [ ] Keep system updated
- [ ] Use HTTPS for all APIs
- [ ] Store secrets in environment variables
- [ ] Limit file permissions (600 for .env)
- [ ] Enable automatic security updates
- [ ] Use fail2ban for SSH protection
- [ ] Disable password authentication (use keys)

---

## Scaling Guide

### Vertical Scaling

Increase server resources:
- 4 vCPU → 8 vCPU
- 4GB RAM → 16GB RAM
- 50GB SSD → 200GB SSD

### Horizontal Scaling

Deploy multiple factory instances:

```yaml
# docker-compose.yml
version: '3.8'

services:
  factory-1:
    build: .
    environment:
      - INSTANCE_ID=1
    
  factory-2:
    build: .
    environment:
      - INSTANCE_ID=2
    
  factory-3:
    build: .
    environment:
      - INSTANCE_ID=3
```

### Database Scaling

**Read Replicas:**
```python
# config/settings.py
class DatabaseConfig:
    primary_url = "postgresql://primary..."
    replica_urls = [
        "postgresql://replica1...",
        "postgresql://replica2...",
    ]
```

---

For more information, see:
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [CONFIGURATION.md](CONFIGURATION.md) - Configuration guide
- [AGENTS.md](AGENTS.md) - Agent documentation
