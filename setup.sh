#!/usr/bin/env bash
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
FRONTEND_PORT=5000
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

check_command() {
  command -v "$1" &> /dev/null
}

detect_os() {
  case "$(uname -s)" in
    Darwin*) echo "macos" ;;
    Linux*)  echo "linux" ;;
    MINGW*|MSYS*|CYGWIN*) echo "windows" ;;
    *)       echo "unknown" ;;
  esac
}

detect_pkg_manager() {
  local os="$1"
  if [ "$os" = "macos" ]; then
    check_command brew && echo "brew" || echo "none"
  elif check_command apt-get; then
    echo "apt"
  elif check_command dnf; then
    echo "dnf"
  elif check_command yum; then
    echo "yum"
  elif check_command pacman; then
    echo "pacman"
  elif check_command nix-env; then
    echo "nix"
  else
    echo "none"
  fi
}

wait_for_port() {
  local port="$1"
  local timeout="${2:-30}"
  local elapsed=0
  while [ "$elapsed" -lt "$timeout" ]; do
    if check_command nc; then
      nc -z 127.0.0.1 "$port" 2>/dev/null && return 0
    elif check_command python3; then
      python3 -c "import socket; s=socket.socket(); s.settimeout(1); s.connect(('127.0.0.1',$port)); s.close()" 2>/dev/null && return 0
    elif (echo >/dev/tcp/127.0.0.1/"$port") 2>/dev/null; then
      return 0
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done
  return 1
}

print_banner

OS=$(detect_os)
PKG=$(detect_pkg_manager "$OS")

step 1 "Environment Audit"
echo -e "  ${DIM}Platform:${NC}  ${BOLD}$(uname -s) $(uname -m)${NC}"
echo -e "  ${DIM}OS Type:${NC}   ${BOLD}${OS}${NC}"
echo -e "  ${DIM}Pkg Mgr:${NC}   ${BOLD}${PKG}${NC}"
echo ""

HAVE_PYTHON=false
HAVE_NODE=false
HAVE_NPM=false

if check_command python3; then
  PY_VER=$(python3 --version 2>&1)
  ok "Python: $PY_VER"
  HAVE_PYTHON=true
else
  fail "Python3 not found"
fi

if check_command node; then
  NODE_VER=$(node --version 2>&1)
  ok "Node.js: $NODE_VER"
  HAVE_NODE=true
else
  fail "Node.js not found"
fi

if check_command npm; then
  NPM_VER=$(npm --version 2>&1)
  ok "npm: v$NPM_VER"
  HAVE_NPM=true
else
  fail "npm not found"
fi

if [ -n "${DATABASE_URL:-}" ]; then
  ok "DATABASE_URL: configured (PostgreSQL)"
else
  warn "DATABASE_URL not set (will use SQLite fallback)"
fi

step 2 "Auto-Healing Missing Dependencies"

install_python() {
  info "Attempting to install Python3..."
  case "$PKG" in
    brew)   brew install python3 2>/dev/null && HAVE_PYTHON=true ;;
    apt)    sudo apt-get update -qq && sudo apt-get install -y -qq python3 python3-pip python3-venv 2>/dev/null && HAVE_PYTHON=true ;;
    dnf)    sudo dnf install -y python3 python3-pip 2>/dev/null && HAVE_PYTHON=true ;;
    yum)    sudo yum install -y python3 python3-pip 2>/dev/null && HAVE_PYTHON=true ;;
    pacman) sudo pacman -S --noconfirm python python-pip 2>/dev/null && HAVE_PYTHON=true ;;
    *)      fail "Cannot auto-install Python3. Install manually: https://python.org/downloads" ;;
  esac
  $HAVE_PYTHON && ok "Python3 installed successfully"
}

install_node() {
  info "Attempting to install Node.js..."
  case "$PKG" in
    brew)   brew install node 2>/dev/null && HAVE_NODE=true && HAVE_NPM=true ;;
    apt)    curl -fsSL https://deb.nodesource.com/setup_20.x 2>/dev/null | sudo -E bash - 2>/dev/null && sudo apt-get install -y -qq nodejs 2>/dev/null && HAVE_NODE=true && HAVE_NPM=true ;;
    dnf)    sudo dnf install -y nodejs npm 2>/dev/null && HAVE_NODE=true && HAVE_NPM=true ;;
    *)
      if check_command curl; then
        info "Installing via nvm..."
        export NVM_DIR="${HOME}/.nvm"
        curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh 2>/dev/null | bash 2>/dev/null
        [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
        nvm install 20 2>/dev/null && HAVE_NODE=true && HAVE_NPM=true
      else
        fail "Cannot auto-install Node.js. Install manually: https://nodejs.org"
      fi
      ;;
  esac
  $HAVE_NODE && ok "Node.js installed successfully"
}

if ! $HAVE_PYTHON; then install_python; fi
if ! $HAVE_NODE; then install_node; fi

if ! $HAVE_PYTHON; then
  fail "Python3 is required but could not be installed. Aborting."
  exit 1
fi

if ! $HAVE_NODE || ! $HAVE_NPM; then
  fail "Node.js + npm are required but could not be installed. Aborting."
  exit 1
fi

ok "All core dependencies satisfied"

step 3 "Project Structure & Directory Setup"

CWD="$(pwd)"
PROJECT_ROOT=""

find_project() {
  if [ -f "$CWD/package.json" ] && [ -d "$CWD/cybersentinel/app" ]; then
    PROJECT_ROOT="$CWD"
    ok "Project found in current directory: $PROJECT_ROOT"
    return 0
  fi

  if [ -f "$CWD/package.json" ] && [ -f "$CWD/app/main.py" ]; then
    PROJECT_ROOT="$CWD"
    ok "Project found in current directory: $PROJECT_ROOT"
    return 0
  fi

  if [ -f "$CWD/app/main.py" ] && [ -f "$CWD/../package.json" ]; then
    PROJECT_ROOT="$(cd "$CWD/.." && pwd)"
    ok "Running from inside cybersentinel/, project root: $PROJECT_ROOT"
    return 0
  fi

  if [ -n "${BASH_SOURCE[0]:-}" ] && [ "${BASH_SOURCE[0]}" != "$0" ] 2>/dev/null; then
    local SCRIPT_DIR
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    if [ -f "$SCRIPT_DIR/package.json" ] && [ -d "$SCRIPT_DIR/cybersentinel/app" ]; then
      PROJECT_ROOT="$SCRIPT_DIR"
      ok "Project found via script location: $PROJECT_ROOT"
      return 0
    fi
  fi

  if [ -d "$CWD/$PROJECT_DIR" ] && [ -f "$CWD/$PROJECT_DIR/package.json" ]; then
    PROJECT_ROOT="$CWD/$PROJECT_DIR"
    ok "Project found in ./$PROJECT_DIR subfolder"
    return 0
  fi

  return 1
}

if ! find_project; then
  info "Project not found locally. Cloning from GitHub..."
  if ! check_command git; then
    fail "git not found and project directory missing. Cannot continue."
    exit 1
  fi
  git clone --depth 1 "$REPO_URL" "$PROJECT_DIR"
  if [ $? -ne 0 ]; then
    fail "git clone failed. Check your internet connection and repo URL."
    fail "Repo: $REPO_URL"
    exit 1
  fi
  PROJECT_ROOT="$CWD/$PROJECT_DIR"
  ok "Repository cloned to $PROJECT_ROOT"
fi

cd "$PROJECT_ROOT"

CYBERSENTINEL_DIR="$PROJECT_ROOT/cybersentinel"

if [ -f "$PROJECT_ROOT/package.json" ]; then
  NPM_DIR="$PROJECT_ROOT"
  ok "Frontend: root-level package.json"
elif [ -f "$PROJECT_ROOT/client/package.json" ]; then
  NPM_DIR="$PROJECT_ROOT/client"
  ok "Frontend: client/package.json"
else
  fail "No package.json found at root or client/. Frontend cannot be installed."
  exit 1
fi

mkdir -p "$CYBERSENTINEL_DIR/data/vector_db" \
         "$CYBERSENTINEL_DIR/data/exports" \
         "$CYBERSENTINEL_DIR/app/skills"
ok "Data directories verified (data/, data/vector_db/, data/exports/)"

step 4 "Dependency Installation (Isolated)"

info "Setting up Python virtual environment (PEP 668 safe)..."
VENV_PATH="$PROJECT_ROOT/$VENV_DIR"

if [ ! -d "$VENV_PATH" ]; then
  python3 -m venv "$VENV_PATH" 2>/dev/null || {
    warn "venv module not available, attempting to install..."
    case "$PKG" in
      apt) sudo apt-get install -y -qq python3-venv 2>/dev/null ;;
      dnf) sudo dnf install -y python3-venv 2>/dev/null ;;
      *) ;;
    esac
    python3 -m venv "$VENV_PATH"
  }
  ok "Virtual environment created at $VENV_DIR/"
else
  ok "Virtual environment already exists at $VENV_DIR/"
fi

source "$VENV_PATH/bin/activate"
ok "Virtual environment activated"

PYTHON_BIN="$VENV_PATH/bin/python"
PIP_BIN="$VENV_PATH/bin/pip"

info "Installing Python dependencies..."
"$PIP_BIN" install --upgrade pip --quiet 2>/dev/null
if [ -f "$CYBERSENTINEL_DIR/requirements.txt" ]; then
  "$PIP_BIN" install -r "$CYBERSENTINEL_DIR/requirements.txt" --quiet 2>/dev/null \
    && ok "Python dependencies installed ($(wc -l < "$CYBERSENTINEL_DIR/requirements.txt") packages)" \
    || warn "Some Python dependencies had issues (non-fatal)"
else
  warn "No requirements.txt found at $CYBERSENTINEL_DIR/requirements.txt"
fi

info "Installing Node.js dependencies..."
cd "$NPM_DIR"
npm install --silent 2>/dev/null \
  && ok "Node.js dependencies installed" \
  || warn "Some Node.js dependencies had issues (non-fatal)"
cd "$PROJECT_ROOT"

step 5 "Database Setup"

if [ -z "${DATABASE_URL:-}" ]; then
  export DATABASE_URL="sqlite:///./cybersentinel.db"
  warn "No DATABASE_URL found. Using SQLite fallback: $DATABASE_URL"
  info "For production, set DATABASE_URL to a PostgreSQL connection string"
else
  ok "Using PostgreSQL: DATABASE_URL is set"
fi

if [ -f "$CYBERSENTINEL_DIR/app/setup_db.py" ]; then
  cd "$CYBERSENTINEL_DIR"
  "$PYTHON_BIN" app/setup_db.py 2>/dev/null \
    && ok "Database migration complete" \
    || warn "Database migration had issues (non-fatal, app will auto-create tables)"
  cd "$PROJECT_ROOT"
else
  info "No setup_db.py found, skipping migration (tables created on first run)"
fi

step 6 "Launch"

echo ""
ok "Setup complete. Starting CyberSentinel AI..."
echo ""

info "Starting FastAPI backend on port $BACKEND_PORT..."

cd "$CYBERSENTINEL_DIR"
UVICORN_BIN="$VENV_PATH/bin/uvicorn"
if [ -f "$UVICORN_BIN" ]; then
  nohup "$UVICORN_BIN" app.main:app \
    --host 0.0.0.0 \
    --port "$BACKEND_PORT" \
    --log-level info \
    > "$PROJECT_ROOT/$BACKEND_LOG" 2>&1 &
else
  info "uvicorn binary not found, using python -m uvicorn"
  nohup "$PYTHON_BIN" -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "$BACKEND_PORT" \
    --log-level info \
    > "$PROJECT_ROOT/$BACKEND_LOG" 2>&1 &
fi
BACKEND_PID=$!

cd "$PROJECT_ROOT"

info "Waiting for backend to initialize..."
if wait_for_port "$BACKEND_PORT" 30; then
  ok "Backend is live on port $BACKEND_PORT (PID: $BACKEND_PID)"
else
  warn "Backend did not respond on port $BACKEND_PORT within 30s"
  info "It may still be loading. Check $BACKEND_LOG for details"
  info "The frontend will work with fallback data in the meantime"
fi

echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}${BOLD}  CyberSentinel AI v1.0.0 — OPERATIONAL${NC}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  ${CYAN}${BOLD}Dashboard:${NC}     http://localhost:$FRONTEND_PORT"
echo -e "  ${CYAN}${BOLD}API Docs:${NC}      http://localhost:$BACKEND_PORT/docs"
echo -e "  ${CYAN}${BOLD}Backend Log:${NC}   $PROJECT_ROOT/$BACKEND_LOG"
echo ""
echo -e "  ${DIM}No .env file required — configure everything from the Web UI.${NC}"
echo -e "  ${DIM}First launch will open the Onboarding Wizard automatically.${NC}"
echo -e "  ${DIM}Press Ctrl+C to stop both backend and frontend.${NC}"
echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

info "Starting frontend (foreground)..."
echo ""

cd "$NPM_DIR"
npm run dev
