#!/bin/bash
# Quick deploy script for AWS EC2
# Run this on your EC2 instance after cloning the repo

set -e

echo "🚀 Digital Twin AWS Deployment Script"
echo "======================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Installing..."
    
    if command -v dnf &> /dev/null; then
        # Amazon Linux
        sudo dnf update -y
        sudo dnf install docker git -y
        sudo systemctl start docker
        sudo systemctl enable docker
        sudo usermod -aG docker $USER
    else
        # Ubuntu
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
    fi
    
    echo "✅ Docker installed. Please log out and back in, then run this script again."
    exit 0
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "📦 Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Navigate to project directory
cd "$(dirname "$0")/.."

echo "📁 Working directory: $(pwd)"

# Create data directories
mkdir -p data/results

# Create empty SSL directory (for nginx)
mkdir -p deploy/ssl

# Check if .env exists, create if not
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
POSTGRES_DB=twin
POSTGRES_USER=twin_user
POSTGRES_PASSWORD=twin_pass_$(openssl rand -hex 8)
REDIS_HOST=redis
REDIS_PORT=6379
MAPBOX_TOKEN=
OPENAI_API_KEY=
GEMINI_API_KEY=
EOF
    echo "✅ Created .env file with secure password"
fi

# Get public IP
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || curl -s ifconfig.me)
echo "🌐 Public IP: $PUBLIC_IP"

# Update frontend API URL for production
export VITE_API_URL="http://${PUBLIC_IP}"

# Build and start services
echo "🔨 Building and starting services..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml build
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo ""
echo "📊 Service Status:"
docker compose ps

# Health check
echo ""
echo "🏥 Health Check:"
if curl -s "http://localhost:8000/health" | grep -q "healthy"; then
    echo "✅ API is healthy"
else
    echo "⚠️  API health check failed - check logs with: docker compose logs api"
fi

echo ""
echo "======================================"
echo "🎉 Deployment Complete!"
echo "======================================"
echo ""
echo "Access your application at:"
echo "  📱 Frontend: http://$PUBLIC_IP"
echo "  🔌 API:      http://$PUBLIC_IP/api/"
echo "  📚 API Docs: http://$PUBLIC_IP/docs"
echo ""
echo "Useful commands:"
echo "  View logs:     docker compose logs -f"
echo "  Restart:       docker compose restart"
echo "  Stop:          docker compose down"
echo "  Update:        git pull && docker compose up -d --build"
echo ""
