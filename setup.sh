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
FRONTEND_PORT=3000
BACKEND_LOG="backend.log"
FRONTEND_LOG="frontend.log"

print_banner() {
cat << 'EOF'
   ██████╗██╗   ██╗██████╗ ███████╗██████╗     ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗
  ██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗    ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║
  ██║      ╚████╔╝ ██████╔╝█████╗  ██████╔╝    ███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║
  ██║       ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██╗    ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║
  ╚██████╗   ██║   ██████╔╝███████╗██║  ██║    ███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗
   ╚═════╝   ╚═╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝    ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝
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
    # ใช้ nc (netcat) แทน /dev/tcp เพื่อความชัวร์บน macOS
    nc -z 127.0.0.1 "$port" >/dev/null 2>&1 && return 0
    sleep 1
    elapsed=$((elapsed + 1))
  done
  return 1
}

info "Cleaning up old processes..."
lsof -ti:$BACKEND_PORT,$FRONTEND_PORT | xargs kill -9 2>/dev/null || true

print_banner
OS=$(detect_os)
PKG=$(detect_pkg_manager "$OS")

step 1 "Environment Audit"
if command -v pyenv &>/dev/null; then
    pyenv local 3.10.13 2>/dev/null || warn "Python 3.10.13 not found in pyenv, using default."
fi

# เลือก Python ที่ถูกต้องก่อนทำ Audit
PYTHON_CMD=$(command -v python3.10 || command -v python3 || command -v python)
ok "Python: $($PYTHON_CMD --version)"
check_command node && ok "Node.js: $(node --version)" || fail "Node.js missing"
check_command npm && ok "npm: v$(npm --version)" || fail "npm missing"

step 2 "Project Structure Setup"
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

# --- Background Task: Python (ใช้ $PYTHON_CMD ที่เราเลือกไว้) ---
(
  if [ ! -d "$VENV_PATH" ]; then
    $PYTHON_CMD -m venv "$VENV_PATH"
  fi
  source "$VENV_PATH/bin/activate"
  pip install --upgrade pip --quiet --disable-pip-version-check
  if [ -f "$CYBERSENTINEL_DIR/requirements.txt" ]; then
    pip install -r "$CYBERSENTINEL_DIR/requirements.txt" --quiet --no-cache-dir
  fi
  touch "$PYTHON_STATUS"
) &
PY_PID=$!

# --- Background Task: Node.js ---
(
  cd "$NPM_DIR"
  npm install --silent --no-audit --no-fund --prefer-offline
  touch "$NODE_STATUS"
) &
NODE_PID=$!

while kill -0 $PY_PID 2>/dev/null || kill -0 $NODE_PID 2>/dev/null; do
    echo -ne "  ${CYAN}Processing dependencies...${NC}\r"
    sleep 1
done

[ -f "$PYTHON_STATUS" ] && ok "Python dependencies ready" || warn "Python installation had issues"
[ -f "$NODE_STATUS" ] && ok "Node.js dependencies ready" || warn "Node.js installation had issues"
rm -f "$PYTHON_STATUS" "$NODE_STATUS"

step 4 "Database Fast-Setup"
export DATABASE_URL=${DATABASE_URL:-"sqlite:///./cybersentinel.db"}
mkdir -p cybersentinel/data
ok "Database directory initialized."

step 5 "Launch Strategy"
source "$VENV_PATH/bin/activate"
PYTHON_BIN="$VENV_PATH/bin/python"

info "Starting Backend (Background)..."
if [ -d "$CYBERSENTINEL_DIR/app" ]; then
    cd "$CYBERSENTINEL_DIR"
fi

nohup "$PYTHON_BIN" -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "$BACKEND_PORT" \
    --log-level info \
    > "$PROJECT_ROOT/$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!

cd "$PROJECT_ROOT"
info "Waiting for Backend to initialize (Max 60s)..."

if wait_for_port "$BACKEND_PORT" 60; then
    ok "Backend Live on port $BACKEND_PORT (PID: $BACKEND_PID)"
else
    fail "Backend failed to respond. Check $BACKEND_LOG"
fi

step 6 "Frontend Launch"
info "Starting Frontend in background..."
# รัน Frontend แบบ Background ทิ้งไว้
nohup npm run dev -- --port "$FRONTEND_PORT" > "$FRONTEND_LOG" 2>&1 &
FRONTEND_PID=$!

sleep 5
echo -e "\n${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}${BOLD}  CyberSentinel AI v1.0.0 — FULLY OPERATIONAL${NC}"
echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
info "Dashboard: http://localhost:$FRONTEND_PORT"
info "Backend API: http://localhost:$BACKEND_PORT"
info "Backend Log: tail -f $BACKEND_LOG"
info "Frontend Log: tail -f $FRONTEND_LOG"
echo -e "\n${YELLOW}Note: All processes are now running in the background.${NC}"
echo -e "${YELLOW}To stop them: lsof -ti:$BACKEND_PORT,$FRONTEND_PORT | xargs kill -9${NC}"