# CyberSentinel - Autonomous SOC AI System

## Overview
CyberSentinel is a production-grade autonomous Security Operations Center (SOC) AI system designed to automate Tier 1 Analyst tasks while maintaining strict data privacy and security (Data Sovereignty).

## Architecture
Multi-Agent Workflow using LangGraph:
- **Analyst Agent** (DeepSeek-R1): Initial alert investigation and reasoning
- **Skeptic Agent** (Llama 3.3): Adversarial analysis to find False Positives
- **Judge Agent**: Final consensus-based verdict using RAG (ChromaDB playbooks)

## Key Features
- **Privacy-First**: All AI reasoning happens via Local LLMs (Ollama)
- **PII Masking**: Automatic masking of IP addresses, emails, and employee IDs
- **RAG-Enhanced**: ChromaDB stores security playbooks for context-aware decisions
- **Mock-Ready**: Works immediately with mock data if external services unavailable
- **Production-Grade**: Modular, commented, and ready for always-on execution

## Installation

```bash
cd cybersentinel
pip install -r requirements.txt
```

## Configuration
Edit `.env` file with your credentials:
```
SPLUNK_URL=https://your-splunk.local
SPLUNK_TOKEN=your-token
OLLAMA_BASE_URL=http://localhost:11434
JIRA_URL=https://your-jira.local
JIRA_TOKEN=your-token
VT_API_KEY=your-virustotal-key
```

## Running the System

```bash
# Start the FastAPI server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### POST /analyze
Analyze a security alert via webhook from Splunk.

**Request Body:**
```json
{
  "alert_id": "ALT-2026-001",
  "description": "Multiple failed login attempts",
  "raw_data": "User john@company.com from 192.168.1.100 failed login 5 times then succeeded",
  "risk_score": 85,
  "source": "splunk",
  "timestamp": "2026-02-24T10:00:00Z"
}
```

**Response:**
```json
{
  "alert_id": "ALT-2026-001",
  "verdict": "True Positive",
  "analyst_report": "...",
  "skeptic_report": "...",
  "judge_reasoning": "...",
  "executive_report": "...",
  "technical_report": "...",
  "jira_ticket": {...}
}
```

### GET /
Health check endpoint

### GET /health
Detailed health check with component status

## Splunk Integration
In Splunk, configure Alert Actions:
1. Go to Alert Settings
2. Add Webhook Action
3. URL: `http://your-server:8000/analyze`
4. Method: POST
5. Body: Include alert_id, description, raw_data, risk_score

## Local LLM Setup (Ollama)
```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Pull required models
ollama pull deepseek-r1:latest
ollama pull llama3.3:latest

# Verify
ollama list
```

## Directory Structure
```
cybersentinel/
├── app/
│   ├── main.py              # FastAPI + Webhook Listener
│   ├── agents/              # Multi-Agent Logic
│   │   ├── workflow.py      # LangGraph State Machine
│   │   ├── analyst.py       # Reasoning Agent (DeepSeek-R1)
│   │   ├── skeptic.py       # Adversarial Agent (Llama 3.3)
│   │   └── judge.py         # Consensus Agent
│   ├── core/
│   │   ├── config.py        # Security & Env Settings
│   │   └── database.py      # ChromaDB (RAG for Playbooks)
│   ├── integrations/        # Connectors
│   │   ├── splunk_client.py # SIEM Integration
│   │   ├── vt_client.py     # Threat Intel
│   │   └── jira_client.py   # Ticketing
│   └── utils/
│       ├── masking.py       # PII Masking (Security Layer)
│       └── reporter.py      # Executive/Technical Reports
├── data/
│   └── playbooks/           # Security SOPs (SOP.md)
├── requirements.txt
└── .env
```

## Security Notes
- All PII is masked before LLM processing
- Local LLMs ensure data never leaves your infrastructure
- Mock mode allows testing without exposing credentials
- Modular design for easy security audits

## Testing
```bash
# Test with mock data
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "alert_id": "TEST-001",
    "description": "Test alert",
    "raw_data": "Failed login from 10.0.0.1 for user admin@example.com EMP12345",
    "risk_score": 75
  }'
```

## License
Production-ready for enterprise SOC deployment.
