#!/usr/bin/env bash
set -euo pipefail

# ==================================================
#  CyberSentinel AI v1.0.0 — Sovereign Master Setup
#  The AI-Native Autonomous SOC System
# ==================================================

echo "=================================================="
echo " 🛡️  CyberSentinel AI - Sovereign SOC v1.0.0"
echo "=================================================="

# Function to check commands
check_command() {
  if ! command -v "$1" &> /dev/null; then
    return 1
  fi
  return 0
}

# --- [STEP 1] Environment Setup ---
echo "[1/4] Preparing Environment..."
if [ ! -f "cybersentinel/.env" ]; then
    echo "  Creating .env from example..."
    cp cybersentinel/.env.example cybersentinel/.env
    echo "  [ACTION] Created cybersentinel/.env - Please add your API keys there."
else
    echo "  [OK] .env file already exists."
fi

# Create Data Directories
mkdir -p cybersentinel/data/vector_db cybersentinel/data/exports cybersentinel/app/skills
echo "  [OK] Data directories ready."

# --- [STEP 2] Choose Deployment Method ---
echo ""
echo "How would you like to deploy CyberSentinel?"
echo "1) Docker (Recommended - Quickest & Cleanest)"
echo "2) Local Manual (For Developers - Requires Python & Node.js)"
read -p "Select option [1-2]: " DEPLOY_CHOICE

if [ "$DEPLOY_CHOICE" == "1" ]; then
    # --- DOCKER DEPLOYMENT ---
    echo "[2/4] Checking Docker..."
    if ! check_command docker; then
        echo "[ERROR] Docker is not installed. Visit https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    echo "[3/4] Building and starting with Docker Compose..."
    docker-compose up -d --build || docker compose up -d --build
    
    echo ""
    echo "=================================================="
    echo " ✅ CyberSentinel is ONLINE (Docker)"
    echo " Dashboard: http://localhost:3000"
    echo " API & Docs: http://localhost:8000/docs"
    echo "=================================================="

else
    # --- MANUAL DEPLOYMENT ---
    echo "[2/4] Checking Dependencies (Python/Node)..."
    check_command python3 || { echo "Python3 missing"; exit 1; }
    check_command npm || { echo "NPM missing"; exit 1; }

    echo "[3/4] Installing dependencies..."
    # Python
    pip install -r cybersentinel/requirements.txt --quiet && echo "  Python: OK"
    # Node.js
    npm install --silent && echo "  Node.js: OK"

    echo "[4/4] Running core validation..."
    cd cybersentinel
    python3 test_suite.py | tail -n 5 || echo "  [WARN] Some tests failed."
    cd ..

    echo ""
    echo "=================================================="
    echo " ✅ Setup Complete (Manual Mode)"
    echo " To run the system:"
    echo " Terminal 1 (Backend): cd cybersentinel && python3 -m uvicorn app.main:app"
    echo " Terminal 2 (Frontend): npm run dev"
    echo "=================================================="
fi