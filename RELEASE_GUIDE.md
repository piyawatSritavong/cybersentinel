# CyberSentinel AI v1.0.0 - Release Guide

## Sovereign Security Platform - Deployment & Configuration

---

## Quick Start

```bash
# 1. Clone the repository
git clone <repo-url> && cd cybersentinel

# 2. Install dependencies
pip install -r requirements.txt
npm install

# 3. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 4. Start the platform
npm run dev
```

---

## Architecture Overview

CyberSentinel AI is a dual-layer platform:

- **Express Gateway** (port 5000): Serves the React Cyber Command Center and proxies API requests
- **FastAPI AI Core** (port 8000): Runs the autonomous SOC engine with Blue/Red/Purple agent squads

```
                    Browser
                      |
              Express Gateway (:5000)
             /        |        \
    React UI    REST API    WebSocket
                  |
           FastAPI Core (:8000)
          /    |    |    \
     Agents  Queue  Vault  Gateways
      |        |      |       |
    Groq    Scheduler PBKDF2  Telegram/Discord/Slack
```

---

## Environment Variables

### Required

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Groq API key for LLM agents |
| `APP_API_KEY` | Internal API authentication key |
| `SECRET_VAULT_KEY` | PII encryption master key |
| `SESSION_SECRET` | Express session secret |

### Optional - Social Gateways

| Variable | Description |
|---|---|
| `ENABLE_SOCIAL_GATEWAY` | Set to `true` to enable social integrations |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot API token (from @BotFather) |
| `TELEGRAM_CHAT_ID` | Default Telegram chat/group ID for alerts |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL for notifications |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL |

### Optional - Database

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (Replit Managed or self-hosted) |
| `ENABLE_LEARNING` | Set to `true` to enable vector memory learning |

---

## Social Gateway Configuration

### Telegram Bot Setup

1. Message @BotFather on Telegram and create a new bot with `/newbot`
2. Copy the bot token and set `TELEGRAM_BOT_TOKEN`
3. Add the bot to your security group/channel
4. Get the chat ID and set `TELEGRAM_CHAT_ID`
5. Set `ENABLE_SOCIAL_GATEWAY=true`

The bot supports:
- `/status` - System health overview
- `/analyze <target>` - Quick threat analysis via Blue Team
- `/squad_stats` - Agent squad statistics
- `/help` - Available commands

Reply to any alert message to send feedback to the Purple Team HITL loop.

### Discord Setup (Extensibility Stub)

1. Create a webhook in your Discord server settings
2. Set `DISCORD_WEBHOOK_URL` to the webhook URL
3. Implement the full gateway logic in `cybersentinel/app/gateways/discord.py`

### Slack Setup (Extensibility Stub)

1. Create an incoming webhook in your Slack workspace
2. Set `SLACK_WEBHOOK_URL` to the webhook URL
3. Implement the full gateway logic in `cybersentinel/app/gateways/slack.py`

### Adding a Custom Gateway

Create a new file in `cybersentinel/app/gateways/` implementing `BaseGateway`:

```python
from app.gateways.base import BaseGateway

class WhatsAppGateway(BaseGateway):
    name = "whatsapp"
    gateway_type = "messaging"

    async def send_alert(self, alert):
        # Implementation here
        pass

    async def send_message(self, message, target=None):
        # Implementation here
        pass

    async def handle_command(self, command, args, context):
        # Implementation here
        pass

    async def start(self):
        self._connected = True
        return True

    async def stop(self):
        self._connected = False
        return True
```

Register it in `main.py` startup event.

---

## Production Deployment

### Docker Compose

```yaml
version: '3.8'
services:
  cybersentinel:
    build: .
    ports:
      - "5000:5000"
      - "8000:8000"
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
      - APP_API_KEY=${APP_API_KEY}
      - SECRET_VAULT_KEY=${SECRET_VAULT_KEY}
      - DATABASE_URL=${DATABASE_URL}
      - ENABLE_SOCIAL_GATEWAY=${ENABLE_SOCIAL_GATEWAY}
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2.0'
```

### Scaling Guide

**Single Instance (up to 100K alerts/day):**
- Default configuration with 5 queue workers
- In-memory task queue
- SQLite-backed ChromaDB

**Multi-Instance (100K-1M alerts/day):**
- Replace TaskQueue with Redis/Celery backend
- Use PostgreSQL for all persistent data
- Deploy behind a load balancer
- Scale FastAPI workers: `uvicorn app.main:app --workers 4`

**Enterprise (1M+ alerts/day):**
- Kubernetes deployment with horizontal pod autoscaler
- Dedicated Redis cluster for task queue
- Separate ChromaDB service with managed vector store
- API gateway (Kong/Traefik) for rate limiting
- Observability stack (Prometheus + Grafana)

---

## API Reference

### Health Endpoints

| Endpoint | Auth | Description |
|---|---|---|
| `GET /health` | No | Basic health check |
| `GET /v1/health/pro` | API Key | Production health (memory, queue, agents, gateways) |

### Alert Management

| Endpoint | Auth | Description |
|---|---|---|
| `POST /v1/ingest` | API Key | Async alert ingestion (returns task_id) |
| `GET /v1/task/{id}` | API Key | Poll task status |
| `POST /analyze` | API Key | Synchronous full analysis |
| `POST /confirm-verdict` | API Key | RLHF feedback loop |

### Agent Squads

| Endpoint | Auth | Description |
|---|---|---|
| `POST /v1/agents/run` | API Key | Run Blue/Red/Purple team |

### Skills & Cron

| Endpoint | Auth | Description |
|---|---|---|
| `GET /v1/skills` | API Key | List loaded skills |
| `POST /v1/skills/generate` | API Key | AI-generate new skill |
| `GET /v1/cron` | API Key | List scheduled jobs |
| `POST /v1/cron` | API Key | Create cron job |
| `PATCH /v1/cron/{id}/toggle` | API Key | Toggle job on/off |
| `DELETE /v1/cron/{id}` | API Key | Delete job |

### Social Gateways

| Endpoint | Auth | Description |
|---|---|---|
| `GET /v1/gateways/status` | No | Gateway connection status |
| `POST /v1/gateways/test` | API Key | Test gateway connectivity |

---

## Security Considerations

- All PII is encrypted with PBKDF2+HMAC-SHA256 before agents process it
- Agents only see Forensic Tokens (FTKN-xxxx), never raw data
- Vault audit logs are immutable (append-only tuple storage)
- API key validation uses timing-safe comparison (prevents timing attacks)
- Rate limiting enforced on API key validation (120 req/min per key)
- Circuit breaker pattern protects against external API cascading failures

---

## Running the Test Suite

```bash
cd cybersentinel
python test_suite.py
```

The test suite validates 6 phases:
1. Infrastructure & Multi-Tenancy (Vault, Queue, PII Masking)
2. Triple-Threat Squad Simulation (Blue/Red/Purple agents)
3. AI Self-Evolution (Dynamic skills, Cron scheduler)
4. UI/UX Gateway Connectivity (Express proxy, terminal)
5. Social Gateway Framework (Telegram, multi-channel)
6. Production Hardening (Immutable audit, metrics, circuit breakers)

---

## Changelog - v1.0.0

- Universal Social Gateway with Telegram integration and multi-channel extensibility
- Production-grade queue with surge protection, metrics, and task TTL
- Immutable vault audit logs with timestamps
- Circuit breaker and retry-with-backoff resilience patterns
- Production health endpoint with memory, queue, and agent monitoring
- Gateway management page in Cyber Command Center
- Strict API key validation with timing-safe comparison
- 80+ automated tests across 6 phases
