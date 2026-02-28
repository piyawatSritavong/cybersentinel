#!/bin/bash

echo "==========================================="
echo "  CyberSentinel AI - One-Line Install"
echo "  AI-Native Autonomous SOC System v3.0"
echo "==========================================="
echo ""

# 1. Check for Docker
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker is not installed. Please install Docker first."
    echo "  -> https://docs.docker.com/get-docker/"
    exit 1
fi
echo "[OK] Docker found."

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "[ERROR] docker-compose is not installed."
    exit 1
fi
echo "[OK] Docker Compose found."

# 2. Setup environment variables
if [ ! -f .env ]; then
    echo "[SETUP] Creating .env from .env.example..."
    cp .env.example .env
    echo "[ACTION REQUIRED] Please update the .env file with your actual keys:"
    echo "  - GROQ_API_KEY"
    echo "  - APP_API_KEY"
    echo "  - DATABASE_URL"
    echo "  - SECRET_VAULT_KEY"
else
    echo "[OK] .env file already exists."
fi

# 3. Create necessary directories for volume mounts
echo "[SETUP] Creating data directories..."
mkdir -p data/vector_db
mkdir -p data/exports
mkdir -p data/playbooks

# 4. Build and start containers
echo ""
echo "[DEPLOY] Building and starting CyberSentinel..."
if command -v docker-compose &> /dev/null; then
    docker-compose up -d --build
else
    docker compose up -d --build
fi

echo ""
echo "==========================================="
echo "  CyberSentinel AI is now running!"
echo "  API:    http://localhost:8000"
echo "  Docs:   http://localhost:8000/docs"
echo "  Health: http://localhost:8000/health"
echo "==========================================="
echo ""
echo "Quick test:"
echo '  curl -X POST http://localhost:8000/v1/ingest \'
echo '    -H "X-API-KEY: YOUR_API_KEY" \'
echo '    -H "Content-Type: application/json" \'
echo '    -d '"'"'{"alert_id":"TEST-001","description":"Test","raw_data":"Failed login from 10.0.0.1","source":"splunk"}'"'"''
