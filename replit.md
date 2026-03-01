# CyberSentinel AI v1.0.0 - Sovereign Security Platform

## Overview
CyberSentinel AI is an AI-Native Autonomous Security Operations Center (SOC) platform with a full-stack Sovereign Gateway dashboard. It implements Blue/Red/Purple team agent squads, self-evolving dynamic skills, async task queues, multi-tenant scoping, social gateway integrations, dynamic settings-in-DB, modular provider/adapter patterns, and production hardening with circuit breakers.

## Architecture
- **Frontend**: React 18 + Vite + Tailwind CSS + Shadcn UI (dark cyber theme)
- **Backend Proxy**: Express.js proxying to FastAPI AI core
- **AI Core**: FastAPI (Python) with multi-agent ReAct loop
- **Database**: PostgreSQL (Replit Managed) + ChromaDB (vector memory)
- **Dynamic Settings**: PostgreSQL-backed DynamicSettings engine (replaces static .env)
- **Provider Pattern**: ModelProvider factory (Groq + stubs), IntegrationHub (6 adapters), SocialConnector stubs
- **Social Gateways**: Telegram (full), Discord (stub), Slack (stub), Line (stub), WhatsApp (stub)
- **Routing**: wouter (frontend), Express routes (backend)
- **State**: @tanstack/react-query for data fetching

## Frontend Structure
```
client/src/
├── App.tsx                  # Router with Layout wrapper + OnboardingGate
├── index.css                # Dark cyber theme (HSL variables)
├── components/
│   ├── layout.tsx           # Sidebar navigation (9 items incl. Settings)
│   └── ui/                  # Shadcn UI components
├── pages/
│   ├── dashboard.tsx        # Sovereign Gateway overview + integration status cards
│   ├── alerts.tsx           # Alert feed + ingest form
│   ├── agents.tsx           # Blue/Red/Purple squad management
│   ├── skills.tsx           # Dynamic skill generation + listing
│   ├── cron-jobs.tsx        # Security scheduler CRUD
│   ├── nodes.tsx            # Distributed sensor node management
│   ├── gateways.tsx         # Social Gateway management + test
│   ├── settings.tsx         # Integrations Marketplace (4 tabs: AI/Social/Integrations/Security)
│   ├── onboarding.tsx       # 4-step first-run setup wizard
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
├── routes.ts                # API routes (proxy to FastAPI + local storage + settings/providers)
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
│   ├── config.py            # Pydantic Settings (incl. gateway config, infra_provider)
│   ├── dynamic_settings.py  # DynamicSettings engine (PostgreSQL-backed, encrypted, singleton)
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
├── providers/
│   ├── __init__.py          # Provider package init
│   ├── model_provider.py    # ModelProvider factory (Groq, OpenAI/Anthropic/Ollama stubs)
│   ├── integration_hub.py   # IntegrationHub (Splunk/Jira/VT/ClickUp/Notion/HybridAnalysis)
│   └── social_connector.py  # SocialConnector stubs (Line, WhatsApp)
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
├── plugins/ticketing/       # Ticketing Plugin System (incl. excel_plugin, scraper_plugin stubs)
└── utils/                   # Masking, Reporting
```

## Dynamic Settings Engine
- `DynamicSettings` class in `cybersentinel/app/core/dynamic_settings.py`
- Loads/saves settings to PostgreSQL `system_settings` table
- Falls back to env vars if DB is empty (backward compatibility)
- Categories: ai_models, social_gateways, integrations, security, system
- `seed_from_env()` auto-populates DB from .env on first run
- Encrypted values (API keys) use PBKDF2-derived vault key + HMAC integrity
- Thread-safe singleton via `get_dynamic_settings()`
- Masked display: encrypted values shown as "****" in API responses

## Provider Pattern
- **ModelProvider**: Factory pattern with `get_model_provider(name)` and `list_providers()`
  - GroqProvider: fully configured, uses groq_api_key from settings
  - OpenAI/Anthropic/Ollama: stubs returning "not configured"
- **IntegrationHub**: Registry of 6 integrations with `list_all()`, `test_integration(name)`, `get_status()`
  - Splunk, Jira, VirusTotal: configured adapters (read from settings)
  - ClickUp, Notion, HybridAnalysis: stubs
- **SocialConnector**: Line + WhatsApp stubs with `list_social_connectors()`

## Onboarding Flow
- App.tsx queries `GET /api/settings/onboarding` on load
- If `completed: false`, redirects to `/onboarding` wizard
- 4-step wizard: Welcome > AI Model Setup > Integrations > Complete
- On completion, POST to `/api/settings/onboarding/complete` marks done
- Subsequent loads skip onboarding and go to dashboard

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
- GET  /api/settings               - All settings (dynamic, grouped by category)
- POST /api/settings               - Update a setting
- GET  /api/settings/onboarding    - Onboarding state
- POST /api/settings/onboarding/complete - Mark onboarding complete
- GET  /api/providers/models       - List model providers + status
- GET  /api/providers/integrations - List integrations + status
- GET  /api/providers/social       - List social connectors + status
- POST /api/providers/integrations/test - Test integration connectivity
- POST /api/settings/api-key/rotate - Rotate APP_API_KEY

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
- GET  /v1/settings            - Dynamic settings (all categories)
- POST /v1/settings            - Update setting
- GET  /v1/settings/onboarding - Onboarding state
- POST /v1/settings/onboarding/complete - Complete onboarding
- GET  /v1/providers/models    - Model providers list
- GET  /v1/providers/integrations - Integrations list
- POST /v1/providers/integrations/test - Test integration
- POST /v1/settings/api-key/rotate - Rotate API key

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
- INFRA_PROVIDER: Infrastructure provider (REPLIT/AWS/LOCAL)

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
- Database: Replit Managed PostgreSQL (tables: `incidents`, `feedback`, `system_settings`, `onboarding_state`)

## Deployment Files
- `docker-compose.yml` — Multi-container deployment (API + Dashboard)
- `cybersentinel/Dockerfile` — Python FastAPI container
- `Dockerfile.dashboard` — Node.js dashboard container
- `setup.sh` — Auto-healing setup script (ASCII art, no API key prompts, directs to Web UI)
- `FINAL_RELEASE_REPORT.md` — Complete go-live documentation

## Test Suite
- 130/130 tests across 7 phases:
  1. Infrastructure & Multi-Tenancy (Vault, Queue, PII Masking) — 19 tests
  2. Triple-Threat Squad Simulation (Blue/Red/Purple agents) — 13 tests
  3. AI Self-Evolution (Dynamic skills, Cron scheduler) — 14 tests
  4. UI/UX Gateway Connectivity (Express proxy, terminal) — 17 tests
  5. Social Gateway Framework (Telegram, multi-channel) — 21 tests
  6. Production Hardening (Immutable audit, metrics, circuit breakers) — 18 tests
  7. Dynamic Platform & Modular Architecture (DynamicSettings, Providers, Hub, API) — 28 tests

## Telegram Bot
- Bot: @CyberSentinel_V1_bot (verified and online)
- Commands: /status, /analyze <target>, /squad_stats, /help
- HITL: Reply to any alert to forward feedback to Purple Team
- Requires TELEGRAM_CHAT_ID to be set after sending /start to bot

## Critical Notes
- `infra_provider` field MUST exist in config.py Settings class (Pydantic validation)
- ChromaDB MUST use LightweightEmbedding (SHA256-based) — sentence-transformers causes OOM
- FastAPI may OOM kill during startup (665MB from blue_team import) — tests pass without running it
- DynamicSettings `seed_from_env()` only seeds on first run (skips if DB has entries)
- IntegrationHub method is `test_integration(name)` not `test(name)`
- All Python imports must be absolute (from app.xxx import ...)
- Platform "Optional" philosophy: missing API keys disable features gracefully, never crash
