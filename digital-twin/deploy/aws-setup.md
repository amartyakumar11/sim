# AWS Deployment Guide - Digital Twin

## Prerequisites
- AWS Account with EC2 access
- AWS CLI configured locally (optional but helpful)
- Your project pushed to a Git repository (GitHub/GitLab)

---

## Step 1: Launch EC2 Instance

1. Go to **AWS Console → EC2 → Launch Instance**

2. Configure:
   - **Name**: `digital-twin-server`
   - **AMI**: Amazon Linux 2023 (or Ubuntu 22.04)
   - **Instance Type**: `t3.medium` (2 vCPU, 4GB RAM) - minimum for this stack
   - **Key Pair**: Create new or use existing (download .pem file!)
   - **Security Group**: Create new with these rules:
     - SSH (22) - Your IP
     - HTTP (80) - Anywhere (0.0.0.0/0)
     - HTTPS (443) - Anywhere (0.0.0.0/0)
     - Custom TCP (3000) - Anywhere (for frontend dev)
     - Custom TCP (8000) - Anywhere (for API)
   - **Storage**: 30 GB gp3

3. Click **Launch Instance**

4. Note the **Public IPv4 address** (e.g., `54.123.45.67`)

---

## Step 2: Connect to EC2

```bash
# Make key readable (Windows PowerShell)
icacls your-key.pem /inheritance:r /grant:r "$($env:USERNAME):(R)"

# Connect via SSH
ssh -i your-key.pem ec2-user@YOUR_PUBLIC_IP

# Or for Ubuntu AMI:
ssh -i your-key.pem ubuntu@YOUR_PUBLIC_IP
```

---

## Step 3: Install Docker on EC2

For **Amazon Linux 2023**:
```bash
# Update system
sudo dnf update -y

# Install Docker
sudo dnf install docker -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Git
sudo dnf install git -y

# IMPORTANT: Log out and back in for group changes
exit
```

For **Ubuntu 22.04**:
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin -y

# Install Git
sudo apt install git -y

# Log out and back in
exit
```

---

## Step 4: Clone and Deploy

```bash
# Reconnect
ssh -i your-key.pem ec2-user@YOUR_PUBLIC_IP

# Clone your repository
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO/digital-twin

# Create production environment file
cp .env.example .env.production
# Edit with your production values if needed

# Build and start all services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

---

## Step 5: Access Your Application

Your app will be available at:
- **Frontend**: `http://YOUR_PUBLIC_IP:3000`
- **API**: `http://YOUR_PUBLIC_IP:8000`
- **API Docs**: `http://YOUR_PUBLIC_IP:8000/docs`

---

## Step 6: (Optional) Set Up Domain with HTTPS

### Option A: Use AWS Elastic IP (stable IP)
1. Go to EC2 → Elastic IPs → Allocate
2. Associate with your instance
3. Use this IP instead of public IP

### Option B: Use a Free Domain + Cloudflare
1. Get free subdomain from freenom.com or use your own domain
2. Point A record to your EC2 IP
3. Use Cloudflare for free SSL

### Option C: Use Nginx + Let's Encrypt (recommended)
See `nginx-setup.sh` in this folder.

---

## Troubleshooting

### Check if services are running:
```bash
docker-compose ps
docker-compose logs api
docker-compose logs frontend
```

### Restart services:
```bash
docker-compose restart
```

### Rebuild after code changes:
```bash
git pull
docker-compose up -d --build
```

### Check disk space:
```bash
df -h
docker system prune -a  # Clean unused images
```

---

## Cost Estimate (t3.medium)
- ~$30/month for EC2
- Free tier: 750 hours/month for t2.micro (but may be slow)

## Quick Teardown
```bash
docker-compose down -v  # Stop and remove volumes
# Then terminate EC2 instance in AWS Console
```
