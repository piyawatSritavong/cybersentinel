# CyberSentinel AI v1.0.0 - Sovereign Security Platform

## Overview
CyberSentinel AI is an AI-Native Autonomous Security Operations Center (SOC) platform with a full-stack Sovereign Gateway dashboard. It implements Blue/Red/Purple team agent squads, self-evolving dynamic skills, async task queues, multi-tenant scoping, social gateway integrations, and production hardening with circuit breakers.

## Architecture
- **Frontend**: React 18 + Vite + Tailwind CSS + Shadcn UI (dark cyber theme)
- **Backend Proxy**: Express.js proxying to FastAPI AI core
- **AI Core**: FastAPI (Python) with multi-agent ReAct loop
- **Database**: PostgreSQL (Replit Managed) + ChromaDB (vector memory)
- **Social Gateways**: Telegram (full), Discord (stub), Slack (stub)
- **Routing**: wouter (frontend), Express routes (backend)
- **State**: @tanstack/react-query for data fetching

## Frontend Structure
```
client/src/
├── App.tsx                  # Router with Layout wrapper
├── index.css                # Dark cyber theme (HSL variables)
├── components/
│   ├── layout.tsx           # Sidebar navigation (8 items) + main content
│   └── ui/                  # Shadcn UI components
├── pages/
│   ├── dashboard.tsx        # Sovereign Gateway overview + gateway status
│   ├── alerts.tsx           # Alert feed + ingest form
│   ├── agents.tsx           # Blue/Red/Purple squad management
│   ├── skills.tsx           # Dynamic skill generation + listing
│   ├── cron-jobs.tsx        # Security scheduler CRUD
│   ├── nodes.tsx            # Distributed sensor node management
│   ├── gateways.tsx         # Social Gateway management + test
│   ├── terminal.tsx         # AI-powered interactive terminal
│   └── not-found.tsx        # 404 page
├── hooks/                   # use-toast, use-mobile
└── lib/
    ├── queryClient.ts       # TanStack Query configuration
    └── utils.ts             # Utility functions
```

## Backend Structure
```
server/
├── index.ts                 # Express bootstrap
├── routes.ts                # API routes (proxy to FastAPI + local storage)
├── storage.ts               # In-memory storage (alerts, cron, nodes, gateways, stats)
├── vite.ts                  # Vite dev server integration
└── static.ts                # Static file serving (production)

shared/
└── schema.ts                # Drizzle ORM schema (users table)
```

## CyberSentinel AI Core
```
cybersentinel/app/
├── main.py                  # FastAPI Gateway v1.0.0 with all endpoints
├── core/
│   ├── config.py            # Pydantic Settings (incl. gateway config)
│   ├── engine.py            # AgentSupervisor (ReAct Loop)
│   ├── memory.py            # Multi-Tenant MemoryManager
│   ├── vault.py             # SecretVault (PBKDF2+HMAC-SHA256, immutable audit)
│   ├── tenant.py            # TenantContext
│   ├── queue.py             # Async TaskQueue (surge protection, metrics, TTL)
│   ├── plugin_loader.py     # Dynamic Plugin System
│   ├── skill_engine.py      # AI-generated skill creation + hot-load
│   ├── scheduler.py         # Cron job background scheduler
│   ├── database.py          # ChromaDB Playbook Indexer
│   ├── security.py          # API Key Auth (timing-safe, rate limited)
│   ├── resilience.py        # Circuit Breaker + Retry with Backoff
│   └── normalizer.py        # Log format normalizer (OCSF)
├── gateways/
│   ├── __init__.py          # MultiChannelGateway manager
│   ├── base.py              # Abstract BaseGateway interface
│   ├── telegram.py          # Full Telegram bot (alerts, HITL, commands)
│   ├── discord.py           # Stub Discord gateway
│   └── slack.py             # Stub Slack gateway
├── tools/
│   ├── blue_team.py         # Blue Team (Defensive) Agent
│   ├── red_team.py          # Red Team (Offensive) Agent
│   ├── purple_team.py       # Purple Team (Orchestrator) Agent
│   ├── analyst_tool.py      # SOC Analyst Agent
│   ├── skeptic_tool.py      # Skeptic Agent
│   ├── judge_tool.py        # Judge Agent
│   ├── log_correlator.py    # Log Correlation
│   └── ...                  # Other atomic tools
├── skills/                  # AI-generated dynamic skills directory
├── plugins/ticketing/       # Ticketing Plugin System
└── utils/                   # Masking, Reporting
```

## API Endpoints
### Express Proxy Layer (port 5000)
- GET  /api/sentinel/health        - System health (proxied to FastAPI)
- GET  /api/sentinel/health/pro    - Production health (memory, queue, agents)
- GET  /api/sentinel/stats         - Dashboard metrics
- GET  /api/sentinel/alerts        - Recent alert list
- POST /api/sentinel/ingest        - Submit alert for analysis
- POST /api/sentinel/agents/run    - Run Blue/Red/Purple agent
- GET  /api/sentinel/skills        - List loaded skills
- POST /api/sentinel/skills/generate - Generate new AI skill
- GET  /api/sentinel/cron          - List cron jobs
- POST /api/sentinel/cron          - Create cron job
- PATCH /api/sentinel/cron/:id/toggle - Toggle cron job
- DELETE /api/sentinel/cron/:id    - Delete cron job
- GET  /api/sentinel/nodes         - List sensor nodes
- GET  /api/sentinel/infra         - Infrastructure adapter status
- GET  /api/sentinel/gateways      - Social gateway status
- POST /api/sentinel/gateways/test - Test gateway connectivity
- POST /api/sentinel/terminal      - Terminal command execution

### FastAPI Core (port 8000)
- POST /v1/ingest              - Async alert ingestion
- GET  /v1/task/{task_id}      - Poll task status
- POST /v1/agents/run          - Run agent squad
- GET  /v1/skills              - List dynamic skills
- POST /v1/skills/generate     - Generate new skill
- POST /analyze                - Synchronous full analysis
- GET  /health                 - System health check
- GET  /v1/health/pro          - Production health (detailed)
- GET  /v1/gateways/status     - Gateway connection status
- POST /v1/gateways/test       - Test gateway connectivity
- GET  /v1/vault/audit         - Vault audit log
- GET  /v1/infra/status        - Infrastructure adapter status

## Key Dependencies
- React 18, wouter, @tanstack/react-query, Shadcn UI, Tailwind CSS
- Express.js, Drizzle ORM
- FastAPI, LangChain, Groq, ChromaDB, SQLAlchemy
- Dark mode enabled by default (class="dark" on html)

## Environment Variables
- GROQ_API_KEY: Groq AI API key
- APP_API_KEY: Internal API authentication
- DATABASE_URL: PostgreSQL connection string
- SECRET_VAULT_KEY: PII encryption key
- SESSION_SECRET: Express session secret
- ENABLE_SOCIAL_GATEWAY: Enable social gateway integrations
- TELEGRAM_BOT_TOKEN: Telegram bot token
- TELEGRAM_CHAT_ID: Default Telegram chat ID
- DISCORD_WEBHOOK_URL: Discord webhook URL
- SLACK_WEBHOOK_URL: Slack webhook URL

## Production Hardening (v1.0.0)
- Immutable vault audit logs (tuple-based append-only, capped at 10K entries)
- Vault entry eviction (capped at 50K entries, oldest evicted on overflow)
- Queue surge protection (adaptive worker scaling at 80% capacity, hard cap at 50 workers)
- Task TTL cleanup (expired tasks removed after 1 hour)
- Circuit breaker pattern for external API calls
- Exponential backoff retry for transient failures
- Timing-safe API key comparison (prevents timing attacks)
- Rate limiting on API key validation (120 req/min)
- APP_API_KEY must be set explicitly (no default — fails fast if missing)
- Telegram gateway uses stdlib urllib (no aiohttp dependency)
- Express proxy validates HTTP response status before parsing
- Standardized agent response format ({agent, result, status})
- Gateway data shape aligned between Express fallback and Python backend
- Critical alert broadcasting via social gateways

## Infrastructure Adapter
- `cybersentinel/config/infra_adapter.py` — Replit/AWS/LOCAL provider pattern
- `INFRA_PROVIDER=REPLIT` (default) reads DATABASE_URL from Replit secrets
- `Infra.get_database_url()` returns the correct connection string for the active provider
- `Infra.get_config()` returns full provider status (exposed at `/v1/infra/status`)
- Database: Replit Managed PostgreSQL (tables: `incidents`, `feedback`)

## Deployment Files
- `docker-compose.yml` — Multi-container deployment (API + Dashboard)
- `cybersentinel/Dockerfile` — Python FastAPI container
- `Dockerfile.dashboard` — Node.js dashboard container
- `setup.sh` — Automated setup script
- `FINAL_RELEASE_REPORT.md` — Complete go-live documentation

## Telegram Bot
- Bot: @CyberSentinel_V1_bot (verified and online)
- Commands: /status, /analyze <target>, /squad_stats, /help
- HITL: Reply to any alert to forward feedback to Purple Team
- Requires TELEGRAM_CHAT_ID to be set after sending /start to bot
