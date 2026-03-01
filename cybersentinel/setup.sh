#!/usr/bin/env bash
set -euo pipefail

# 1. แสดง ASCII Art (Branding)
echo "=================================================="
echo " 🛡️  CyberSentinel AI v1.0.0 - Auto-Installer"
echo "=================================================="

# 2. ตรวจสอบและ Clone (ถ้ายังไม่มี)
REPO_DIR="cybersentinel"
if [ ! -d "$REPO_DIR" ]; then
    echo "[1/5] Cloning repository..."
    git clone https://github.com/piyawatSritavong/cybersentinel.git "$REPO_DIR" --quiet
fi
cd "$REPO_DIR"

# 3. ตรวจสอบ Dependencies (Node & Python)
echo "[2/5] Checking System Dependencies..."
check_cmd() { command -v "$1" >/dev/null 2>&1; }

if ! check_cmd node || ! check_cmd python3; then
    echo "  [ERROR] Node.js and Python3 are required."
    exit 1
fi

# 4. ติดตั้ง Backend (Python)
echo "[3/5] Setting up AI Backend..."
python3 -m venv venv --quiet
source venv/bin/activate
pip install -r requirements.txt --quiet
# สร้างฐานข้อมูล SQLite เริ่มต้น (กรณีไม่มี DATABASE_URL เพื่อให้รันได้ทันที)
if [ -z "${DATABASE_URL:-}" ]; then
    export DATABASE_URL="sqlite:///./cybersentinel.db"
    echo "  [INFO] Using local SQLite database for quick start."
fi

# 5. ติดตั้ง Frontend (Node.js) - แก้ไขปัญหาหาไฟล์ package.json ไม่เจอ
echo "[4/5] Setting up Dashboard UI..."
# สแกนหาตำแหน่ง package.json อัตโนมัติ (เผื่ออยู่ในโฟลเดอร์ client/)
PKG_PATH=$(find . -name "package.json" -not -path "*/node_modules/*" | head -n 1)
PKG_DIR=$(dirname "$PKG_PATH")

cd "$PKG_DIR"
npm install --silent
# Build โปรเจค (ถ้าเป็นโปรเจค Production) หรือเตรียมรัน Dev
npm run build --if-present
cd - > /dev/null

# 6. Launching - รัน Backend และ Frontend พร้อมกัน
echo "[5/5] Launching CyberSentinel..."
echo "=================================================="
echo " ✅ Setup Complete! System is starting..."
echo " Dashboard: http://localhost:5173 (or 3000)"
echo " API Docs:  http://localhost:8000/docs"
echo "=================================================="

# ใช้ 'concurrently' หรือรัน Background process เพื่อให้จบในคำสั่งเดียว
(source venv/bin/activate && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &)
cd "$PKG_DIR" && npm run dev