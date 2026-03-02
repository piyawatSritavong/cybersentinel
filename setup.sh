#!/usr/bin/env bash
# CyberSentinel AI - Turbo Setup Script (Optimized for Speed)
set -euo pipefail

trap 'cleanup' EXIT INT TERM

BACKEND_PID=""

cleanup() {
  if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo -e "\n${YELLOW}Shutting down backend (PID $BACKEND_PID)...${NC}"
    kill "$BACKEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" 2>/dev/null || true
  fi
}

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

REPO_URL="${CYBERSENTINEL_REPO:-https://github.com/piyawatSritavong/cybersentinel.git}"
PROJECT_DIR="cybersentinel"
VENV_DIR=".venv"
BACKEND_PORT=8000
FRONTEND_PORT=5001
BACKEND_LOG="backend.log"

print_banner() {
cat << 'EOF'
   ██████╗██╗   ██╗██████╗ ███████╗██████╗ ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗
  ██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║
  ██║      ╚████╔╝ ██████╔╝█████╗  ██████╔╝███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║
  ██║       ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██╗╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║
  ╚██████╗   ██║   ██████╔╝███████╗██║  ██║███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗
   ╚═════╝   ╚═╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝
EOF
echo -e "  ${MAGENTA}${BOLD}AI-Native Autonomous SOC Platform v1.0.0${NC}"
echo -e "  ${DIM}Single-Command Setup & Launch${NC}"
echo ""
}

step() {
  echo -e "\n${CYAN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${CYAN}${BOLD}  [$1/6] $2${NC}"
  echo -e "${CYAN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

ok()   { echo -e "  ${GREEN}✓${NC} $1"; }
warn() { echo -e "  ${YELLOW}⚠${NC} $1"; }
fail() { echo -e "  ${RED}✗${NC} $1"; }
info() { echo -e "  ${CYAN}→${NC} $1"; }

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
  if [ "$os" = "macos" ]; then check_command brew && echo "brew" || echo "none"
  elif check_command apt-get; then echo "apt"
  else echo "none"; fi
}

wait_for_port() {
  local port="$1"
  local timeout="${2:-30}"
  local elapsed=0
  while [ "$elapsed" -lt "$timeout" ]; do
    (echo >/dev/tcp/127.0.0.1/"$port") 2>/dev/null && return 0
    sleep 1
    elapsed=$((elapsed + 1))
  done
  return 1
}

print_banner
OS=$(detect_os)
PKG=$(detect_pkg_manager "$OS")

step 1 "Environment Audit"
check_command python3 && ok "Python: $(python3 --version)" || fail "Python3 missing"
check_command node && ok "Node.js: $(node --version)" || fail "Node.js missing"
check_command npm && ok "npm: v$(npm --version)" || fail "npm missing"

step 2 "Project Structure Setup"
CWD="$(pwd)"
if [ ! -d "$PROJECT_DIR" ] && [ ! -f "package.json" ]; then
    info "Cloning with --depth 1 for speed..."
    git clone --depth 1 "$REPO_URL" "$PROJECT_DIR"
    cd "$PROJECT_DIR"
elif [ -d "$PROJECT_DIR" ]; then
    cd "$PROJECT_DIR"
fi
PROJECT_ROOT="$(pwd)"
CYBERSENTINEL_DIR="$PROJECT_ROOT/cybersentinel"
NPM_DIR="$PROJECT_ROOT"
[ -f "$PROJECT_ROOT/client/package.json" ] && NPM_DIR="$PROJECT_ROOT/client"

mkdir -p "$CYBERSENTINEL_DIR/data/vector_db" "$CYBERSENTINEL_DIR/data/exports" "$CYBERSENTINEL_DIR/app/skills"
ok "Structure verified at $PROJECT_ROOT"

step 3 "Parallel Dependency Installation (Turbo Mode)"
VENV_PATH="$PROJECT_ROOT/$VENV_DIR"
PYTHON_STATUS="/tmp/py_install_$$.status"
NODE_STATUS="/tmp/node_install_$$.status"

info "Installing Python and Node.js dependencies concurrently..."

# --- Background Task: Python ---
(
  if [ ! -d "$VENV_PATH" ]; then
    python3 -m venv "$VENV_PATH"
  fi
  source "$VENV_PATH/bin/activate"
  pip install --upgrade pip --quiet --disable-pip-version-check
  if [ -f "$CYBERSENTINEL_DIR/requirements.txt" ]; then
    # Optimization: Use quiet mode and skip version check
    pip install -r "$CYBERSENTINEL_DIR/requirements.txt" --quiet --no-cache-dir 2>/dev/null
  fi
  touch "$PYTHON_STATUS"
) &
PY_PID=$!

# --- Background Task: Node.js ---
(
  cd "$NPM_DIR"
  # Optimization: --prefer-offline and skip audits/funding notices
  npm install --silent --no-audit --no-fund --prefer-offline 2>/dev/null
  touch "$NODE_STATUS"
) &
NODE_PID=$!

# Wait for both with a simple progress indicator
while kill -0 $PY_PID 2>/dev/null || kill -0 $NODE_PID 2>/dev/null; do
    echo -ne "  ${CYAN}Processing dependencies...${NC}\r"
    sleep 1
done

[ -f "$PYTHON_STATUS" ] && ok "Python dependencies ready" || warn "Python installation had issues"
[ -f "$NODE_STATUS" ] && ok "Node.js dependencies ready" || warn "Node.js installation had issues"
rm -f "$PYTHON_STATUS" "$NODE_STATUS"

step 4 "Database Fast-Setup"
export DATABASE_URL=${DATABASE_URL:-"sqlite:///./cybersentinel.db"}
if [ -z "${DATABASE_URL##*sqlite*}" ]; then
    info "Using optimized SQLite fallback"
else
    ok "Using custom DATABASE_URL"
fi

step 5 "Launch Strategy"
source "$VENV_PATH/bin/activate"
PYTHON_BIN="$VENV_PATH/bin/python"

info "Starting Backend (Background)..."

# [FIX 1] ตรวจสอบตำแหน่งโฟลเดอร์ให้ชัวร์ก่อนรัน
if [ -d "$CYBERSENTINEL_DIR/app" ]; then
    cd "$CYBERSENTINEL_DIR"
elif [ -d "$PROJECT_ROOT/app" ]; then
    cd "$PROJECT_ROOT"
fi

# [FIX 2] เพิ่ม Time-out เป็น 60 วินาทีสำหรับเครื่องที่โหลดช้า
# และเก็บ Error ไว้ดูใน backend.log
nohup "$PYTHON_BIN" -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "$BACKEND_PORT" \
    --log-level info \
    > "$PROJECT_ROOT/$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!

cd "$PROJECT_ROOT"
info "Waiting for Backend to initialize (Max 60s)..."

# [FIX 3] ปรับ wait_for_port ให้รอนานขึ้น
if wait_for_port "$BACKEND_PORT" 60; then
    ok "Backend Live on port $BACKEND_PORT (PID: $BACKEND_PID)"
else
    warn "Backend is taking a while to respond."
    info "Check error details in: cat $BACKEND_LOG"
fi

step 6 "Frontend Launch"
echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}${BOLD}  CyberSentinel AI v1.0.0 — READY${NC}"
echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
info "Dashboard: http://localhost:$FRONTEND_PORT"
info "Starting Frontend (Foreground)...\n"

cd "$NPM_DIR"
npm run dev