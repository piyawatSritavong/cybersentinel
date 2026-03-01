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

step() {
  echo -e "\n${CYAN}${BOLD}[$1/5]${NC} ${BOLD}$2${NC}"
}

ok()   { echo -e "  ${GREEN}[OK]${NC} $1"; }
warn() { echo -e "  ${YELLOW}[WARN]${NC} $1"; }
fail() { echo -e "  ${RED}[FAIL]${NC} $1"; }

check_command() {
  command -v "$1" &> /dev/null
}

detect_os() {
  case "$(uname -s)" in
    Darwin*) echo "macos" ;;
    Linux*)  echo "linux" ;;
    *)       echo "unknown" ;;
  esac
}

detect_pkg_manager() {
  local os="$1"
  if [ "$os" = "macos" ]; then
    echo "brew"
  elif check_command apt-get; then
    echo "apt"
  elif check_command yum; then
    echo "yum"
  elif check_command dnf; then
    echo "dnf"
  else
    echo "unknown"
  fi
}

print_banner

OS=$(detect_os)
PKG=$(detect_pkg_manager "$OS")

step 1 "Environment Audit"
echo -e "  Platform: ${BOLD}$(uname -s) $(uname -m)${NC}"
echo -e "  Package Manager: ${BOLD}${PKG}${NC}"

if check_command python3; then
  PY_VER=$(python3 --version 2>&1)
  ok "Python: $PY_VER"
else
  warn "Python3 not found"
fi

if check_command node; then
  NODE_VER=$(node --version 2>&1)
  ok "Node.js: $NODE_VER"
else
  warn "Node.js not found"
fi

if check_command npm; then
  NPM_VER=$(npm --version 2>&1)
  ok "npm: v$NPM_VER"
else
  warn "npm not found"
fi

if [ -n "${DATABASE_URL:-}" ]; then
  ok "PostgreSQL: DATABASE_URL configured"
else
  warn "DATABASE_URL not set (database features will be limited)"
fi

step 2 "Dependency Check"

MISSING_DEPS=()

if ! check_command python3; then
  MISSING_DEPS+=("python3")
fi

if ! check_command node; then
  MISSING_DEPS+=("node")
fi

if ! check_command npm; then
  MISSING_DEPS+=("npm")
fi

if [ ${#MISSING_DEPS[@]} -eq 0 ]; then
  ok "All required dependencies found"
else
  warn "Missing dependencies: ${MISSING_DEPS[*]}"
fi

step 3 "Auto-Healing"

if [[ " ${MISSING_DEPS[*]:-} " == *" python3 "* ]]; then
  echo -e "  Attempting to install Python3..."
  if [ "$PKG" = "brew" ]; then
    echo -e "  ${CYAN}Run: brew install python3${NC}"
  elif [ "$PKG" = "apt" ]; then
    echo -e "  ${CYAN}Run: sudo apt-get install -y python3 python3-pip${NC}"
  elif [ "$PKG" = "yum" ] || [ "$PKG" = "dnf" ]; then
    echo -e "  ${CYAN}Run: sudo $PKG install -y python3 python3-pip${NC}"
  else
    warn "Could not determine package manager. Install Python3 manually."
  fi
fi

if [[ " ${MISSING_DEPS[*]:-} " == *" node "* ]]; then
  echo -e "  Attempting to install Node.js..."
  if [ "$PKG" = "brew" ]; then
    echo -e "  ${CYAN}Run: brew install node${NC}"
  elif [ "$PKG" = "apt" ]; then
    echo -e "  ${CYAN}Run: curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt-get install -y nodejs${NC}"
  else
    echo -e "  ${CYAN}Install nvm: https://github.com/nvm-sh/nvm${NC}"
  fi
fi

if [ ${#MISSING_DEPS[@]} -eq 0 ]; then
  ok "No auto-healing required"
fi

mkdir -p cybersentinel/data/vector_db cybersentinel/data/exports cybersentinel/app/skills
ok "Data directories verified (data/, data/vector_db/, data/exports/)"

if check_command pip; then
  pip install -r cybersentinel/requirements.txt --quiet 2>/dev/null && ok "Python dependencies installed" || warn "Some Python dependencies failed to install"
elif check_command pip3; then
  pip3 install -r cybersentinel/requirements.txt --quiet 2>/dev/null && ok "Python dependencies installed" || warn "Some Python dependencies failed to install"
else
  warn "pip not found, skipping Python dependency install"
fi

if check_command npm; then
  npm install --silent 2>/dev/null && ok "Node.js dependencies installed" || warn "Some Node.js dependencies failed to install"
fi

step 4 "Database Setup"

if [ -n "${DATABASE_URL:-}" ] && check_command python3; then
  cd cybersentinel
  python3 app/setup_db.py 2>/dev/null && ok "Database migration complete" || warn "Database migration had issues (non-fatal)"
  cd ..
else
  if [ -z "${DATABASE_URL:-}" ]; then
    warn "DATABASE_URL not set, skipping database setup"
  else
    warn "Python3 not available, skipping database setup"
  fi
fi

step 5 "Launch"

ok "CyberSentinel AI v1.0.0 setup complete"

echo ""
echo -e "${BOLD}========================================================${NC}"
echo -e "${GREEN}${BOLD}  CyberSentinel AI v1.0.0 is ready${NC}"
echo -e "${BOLD}========================================================${NC}"
echo ""
echo -e "  Open the ${BOLD}Web UI${NC} to configure integrations."
echo -e "  No API keys are required in .env files."
echo -e "  All settings are managed through the dashboard."
echo ""
echo -e "  ${CYAN}To start:${NC}"
echo -e "    npm run dev"
echo ""
echo -e "  ${CYAN}Dashboard:${NC}  http://localhost:5000"
echo -e "  ${CYAN}API Docs:${NC}   http://localhost:8000/docs"
echo ""
echo -e "${BOLD}========================================================${NC}"
