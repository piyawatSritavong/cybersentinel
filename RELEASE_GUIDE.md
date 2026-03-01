# CyberSentinel AI v1.0.0 - Release Guide

## Sovereign Security Platform - Deployment & Configuration

---

## Quick Start

```bash
# 1. Clone the repository
git clone <repo-url> && cd cybersentinel

# 2. Run the auto-healing setup
chmod +x setup.sh && ./setup.sh

# 3. Start the platform
npm run dev

# 4. Open the Web UI and complete the onboarding wizard
# No .env file required — configure everything from the browser
```

---

## Architecture Overview

CyberSentinel AI is a dual-layer platform with a plug-and-play modular architecture:

- **Express Gateway** (port 5000): Serves the React Cyber Command Center and proxies API requests
- **FastAPI AI Core** (port 8000): Runs the autonomous SOC engine with Blue/Red/Purple agent squads
- **Dynamic Settings**: PostgreSQL-backed configuration engine (no .env editing required)
- **Provider Pattern**: Modular adapters for AI models, integrations, and social connectors

```
                    Browser
                      |
              Express Gateway (:5000)
             /        |        \
    React UI    REST API    WebSocket
                  |
           FastAPI Core (:8000)
          /    |    |    \       \
     Agents  Queue  Vault  Gateways  DynamicSettings
      |        |      |       |           |
    Groq    Scheduler PBKDF2  Telegram  PostgreSQL
                              Discord   (system_settings)
                              Slack
                              Line*
                              WhatsApp*
```

---

## First-Run Setup (Web UI)

CyberSentinel uses a **Web-first configuration** approach. No `.env` file is required.

1. Start the platform with `npm run dev`
2. Open the dashboard in your browser
3. The **Onboarding Wizard** launches automatically on first run:
   - **Step 1**: Welcome screen
   - **Step 2**: Configure your AI model (enter Groq API key, test connection)
   - **Step 3**: Optional integrations checklist (Splunk, Jira, VirusTotal, etc.)
   - **Step 4**: Complete setup
4. All settings are saved to PostgreSQL and persist across restarts

After onboarding, use the **Settings** page (marketplace-style) to manage:
- AI Model providers (Groq, OpenAI, Anthropic, Ollama)
- Social Gateways (Telegram, Discord, Slack, Line, WhatsApp)
- Security Integrations (Splunk, Jira, VirusTotal, ClickUp, Notion, HybridAnalysis)
- Security settings (API key rotation)

---

## Environment Variables

### Required (auto-configured on Replit)

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (Replit Managed) |
| `SESSION_SECRET` | Express session secret |

### Optional (can be configured via Web UI instead)

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Groq API key for LLM agents |
| `APP_API_KEY` | Internal API authentication key |
| `SECRET_VAULT_KEY` | PII encryption master key |
| `ENABLE_SOCIAL_GATEWAY` | Set to `true` to enable social integrations |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot API token (from @BotFather) |
| `TELEGRAM_CHAT_ID` | Default Telegram chat/group ID for alerts |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL for notifications |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL |
| `INFRA_PROVIDER` | Infrastructure provider (REPLIT/AWS/LOCAL) |

All optional variables can be configured from the **Settings** page in the Web UI. On first startup, `seed_from_env()` migrates any existing `.env` values into the database automatically.

---

## Provider Pattern

### AI Model Providers

CyberSentinel uses a factory pattern for AI model providers:

| Provider | Status | Description |
|---|---|---|
| **Groq** | Fully configured | Primary LLM provider (llama-3.3-70b-versatile) |
| **OpenAI** | Stub | Ready for implementation |
| **Anthropic** | Stub | Ready for implementation |
| **Ollama** | Stub | Local model support |

### Integration Hub

| Integration | Status | Description |
|---|---|---|
| **Splunk** | Adapter | SIEM log forwarding via HEC |
| **Jira** | Adapter | Ticket creation for incidents |
| **VirusTotal** | Adapter | IOC enrichment and reputation |
| **ClickUp** | Stub | Task management |
| **Notion** | Stub | Documentation and wiki |
| **HybridAnalysis** | Stub | Malware sandbox analysis |

### Social Connectors

| Connector | Status | Description |
|---|---|---|
| **Telegram** | Full | Alerts, commands, HITL feedback |
| **Discord** | Stub | Webhook-based notifications |
| **Slack** | Stub | Webhook-based notifications |
| **Line** | Stub | Messaging integration |
| **WhatsApp** | Stub | Messaging integration |

---

## Social Gateway Configuration

### Telegram Bot Setup

1. Message @BotFather on Telegram and create a new bot with `/newbot`
2. Go to **Settings > Social Gateways** in the Web UI
3. Enter the bot token and chat ID
4. Toggle the Telegram integration to enabled
5. Use the "Test Connection" button to verify

The bot supports:
- `/status` - System health overview
- `/analyze <target>` - Quick threat analysis via Blue Team
- `/squad_stats` - Agent squad statistics
- `/help` - Available commands

Reply to any alert message to send feedback to the Purple Team HITL loop.

### Adding a Custom Gateway

Create a new file in `cybersentinel/app/gateways/` implementing `BaseGateway`:

```python
from app.gateways.base import BaseGateway

class WhatsAppGateway(BaseGateway):
    name = "whatsapp"
    gateway_type = "messaging"

    async def send_alert(self, alert):
        pass

    async def send_message(self, message, target=None):
        pass

    async def handle_command(self, command, args, context):
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
      - DATABASE_URL=${DATABASE_URL}
      - SESSION_SECRET=${SESSION_SECRET}
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

### Settings & Configuration

| Endpoint | Auth | Description |
|---|---|---|
| `GET /api/settings` | No | All settings grouped by category |
| `POST /api/settings` | API Key | Update a setting |
| `GET /api/settings/onboarding` | No | Onboarding state |
| `POST /api/settings/onboarding/complete` | No | Mark onboarding complete |
| `GET /api/providers/models` | No | List AI model providers |
| `GET /api/providers/integrations` | No | List integrations |
| `GET /api/providers/social` | No | List social connectors |
| `POST /api/providers/integrations/test` | API Key | Test integration |
| `POST /api/settings/api-key/rotate` | API Key | Rotate API key |

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
- Sensitive settings (API keys, tokens) encrypted at rest in PostgreSQL
- API key rotation available via Settings page or API

---

## Running the Test Suite

```bash
cd cybersentinel
python test_suite.py
```

The test suite validates 7 phases (130 tests):
1. Infrastructure & Multi-Tenancy (Vault, Queue, PII Masking) — 19 tests
2. Triple-Threat Squad Simulation (Blue/Red/Purple agents) — 13 tests
3. AI Self-Evolution (Dynamic skills, Cron scheduler) — 14 tests
4. UI/UX Gateway Connectivity (Express proxy, terminal) — 17 tests
5. Social Gateway Framework (Telegram, multi-channel) — 21 tests
6. Production Hardening (Immutable audit, metrics, circuit breakers) — 18 tests
7. Dynamic Platform & Modular Architecture (DynamicSettings, Providers, Hub, API) — 28 tests

---

## Changelog - v1.0.0

- Dynamic Settings Engine: PostgreSQL-backed configuration replaces static .env
- Plug-and-Play Provider Pattern: ModelProvider factory, IntegrationHub, SocialConnector stubs
- Onboarding Wizard: 4-step first-run setup in the Web UI
- Integrations Marketplace: Settings page with tabs for AI/Social/Integrations/Security
- Auto-healing setup.sh with ASCII art banner and no API key prompts
- Plugin system stubs (Excel parser, Web scraper)
- Universal Social Gateway with Telegram integration and multi-channel extensibility
- Production-grade queue with surge protection, metrics, and task TTL
- Immutable vault audit logs with timestamps
- Circuit breaker and retry-with-backoff resilience patterns
- Production health endpoint with memory, queue, and agent monitoring
- Strict API key validation with timing-safe comparison
- 130 automated tests across 7 phases
