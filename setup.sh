#!/usr/bin/env bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

print_banner() {
cat << 'EOF'

   ██████╗██╗   ██╗██████╗ ███████╗██████╗ ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗
  ██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║
  ██║      ╚████╔╝ ██████╔╝█████╗  ██████╔╝███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║
  ██║       ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██╗╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║
  ╚██████╗   ██║   ██████╔╝███████╗██║  ██║███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗
   ╚═════╝   ╚═╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝
                              AI-Native Autonomous SOC Platform v1.0.0

EOF
}
step() { echo -e "\n${CYAN}${BOLD}[$1/5]${NC} ${BOLD}$2${NC}"; }
ok()   { echo -e "  ${GREEN}[OK]${NC} $1"; }
warn() { echo -e "  ${YELLOW}[WARN]${NC} $1"; }

check_command() { command -v "$1" &> /dev/null; }

detect_os() {
  case "$(uname -s)" in
    Darwin*) echo "macos" ;;
    Linux*)  echo "linux" ;;
    *)       echo "unknown" ;;
  esac
}

detect_pkg_manager() {
  local os="$1"
  if [ "$os" = "macos" ]; then echo "brew";
  elif check_command apt-get; then echo "apt";
  else echo "unknown"; fi
}

print_banner
OS=$(detect_os)
PKG=$(detect_pkg_manager "$OS")
REPO_NAME="cybersentinel"

# [CRITICAL] 1. จัดการเรื่อง Folder อัตโนมัติ
if [ ! -d "$REPO_NAME" ] && [[ "$PWD" != *"$REPO_NAME"* ]]; then
    step 1 "Cloning Repository"
    git clone https://github.com/piyawatSritavong/cybersentinel.git "$REPO_NAME"
    cd "$REPO_NAME"
elif [ -d "$REPO_NAME" ]; then
    cd "$REPO_NAME"
fi

step 2 "Environment Audit"
check_command python3 && ok "Python found" || warn "Python3 missing"
check_command node && ok "Node.js found" || warn "Node.js missing"

step 3 "Installation"
mkdir -p data/vector_db data/exports app/skills

# ติดตั้ง Python Dependencies
if check_command pip3; then
    pip3 install -r requirements.txt --quiet && ok "Backend libraries installed"
elif check_command pip; then
    pip install -r requirements.txt --quiet && ok "Backend libraries installed"
fi

# ติดตั้ง Node.js (Frontend)
if [ -f "package.json" ]; then
    npm install --silent && ok "Frontend libraries installed"
elif [ -d "client" ] && [ -f "client/package.json" ]; then
    cd client && npm install --silent && cd .. && ok "Frontend libraries installed (in client/)"
fi

step 4 "Database Setup"
export DATABASE_URL=${DATABASE_URL:-"sqlite:///./cybersentinel.db"}
if check_command python3 && [ -f "app/setup_db.py" ]; then
    python3 app/setup_db.py 2>/dev/null && ok "Database ready"
fi

step 5 "Launching CyberSentinel AI"
echo -e "${GREEN}${BOLD}========================================================${NC}"
echo -e "${GREEN}${BOLD}  Everything is ready! Starting Backend and Frontend...${NC}"
echo -e "${GREEN}${BOLD}========================================================${NC}"

# [MAGIC BITS] รันทุกอย่างให้เองในคำสั่งเดียว
# 1. รัน Backend ใน background
(python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &)
ok "Backend started at http://localhost:8000"

# 2. รัน Frontend ในตำแหน่งที่ถูกต้อง
if [ -f "package.json" ]; then
    npm run dev
elif [ -d "client" ]; then
    cd client && npm run dev
fi