# GEM AI Agent for Bentley

## Overview
This is a Python FastAPI webhook service that integrates Bentley iTwin Webhooks (v2) with the DeepSeek AI reasoning API. The agent receives webhook events from Bentley iTwin, analyzes them using DeepSeek AI, and logs the results.

## Current State
- **Status**: Active and running
- **Framework**: FastAPI with Uvicorn
- **Python Version**: 3.11

## Architecture

### Main Application (`gem_ai_agent.py`)
- **FastAPI Application**: Handles HTTP requests
- **Webhook Endpoint** (`POST /webhook`): Receives Bentley iTwin webhook events
- **Health Check** (`GET /health`): Returns service status and timestamp
- **DeepSeek Integration**: Analyzes incoming events using AI
- **HMAC Signature Verification**: Secures webhook endpoint

### Key Features
1. **Webhook Security**: HMAC-SHA256 signature verification
2. **AI Analysis**: DeepSeek chat API for event summarization
3. **Event Logging**: Markdown files with AI summaries stored in `logs/` directory
4. **Async Processing**: Non-blocking API calls using asyncio

## Environment Variables

### Required Secrets (configure in Replit Secrets panel):
- `BENTLEY_CLIENT_ID` - Your Bentley iTwin client ID
- `BENTLEY_CLIENT_SECRET` - Your Bentley iTwin client secret
- `DEEPSEEK_API_KEY` - Your DeepSeek API key

### Auto-configured:
- `WEBHOOK_SECRET` - Secret for webhook signature verification (default: `gem_webhook_secret`)
- `CALLBACK_URL` - Webhook callback URL (auto-set to Replit domain)
- `SESSION_SECRET` - Session management secret

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check - returns `{"status": "running", "time": "..."}` |
| `/webhook` | POST | Receives Bentley iTwin webhook events |

## File Structure
```
.
├── gem_ai_agent.py      # Main FastAPI application
├── requirements.txt     # Python dependencies
├── logs/                # Event logs directory (auto-created)
│   └── agent.log        # Main application log
└── replit.md            # This documentation
```

## Dependencies
- fastapi
- uvicorn[standard]
- requests

## Running the Service

### Development
The service runs automatically via the configured workflow:
```
uvicorn gem_ai_agent:app --host 0.0.0.0 --port 5000
```

### Production Deployment
Configured for Reserved VM deployment to ensure always-on availability.

### Keep-Alive for Free Plan (No Publish Access)

If you're on Replit's free plan and can't use the Publish feature, your app is still accessible via the development URL while running. To prevent it from sleeping during inactivity, use a free external ping service:

#### Option 1: UptimeRobot (Recommended)
1. Go to [UptimeRobot.com](https://uptimerobot.com) and create a free account
2. Click "Add New Monitor"
3. Configure:
   - **Monitor Type**: HTTP(s)
   - **Friendly Name**: GEM AI Agent
   - **URL**: `https://YOUR-REPLIT-URL/health`
   - **Monitoring Interval**: 5 minutes
4. Click "Create Monitor"

#### Option 2: Cron-Job.org
1. Go to [Cron-Job.org](https://cron-job.org) and create a free account
2. Click "Create cronjob"
3. Configure:
   - **Title**: GEM AI Agent Keep-Alive
   - **URL**: `https://YOUR-REPLIT-URL/health`
   - **Schedule**: Every 5 minutes
4. Click "Create"

#### Option 3: Freshping
1. Go to [Freshping.io](https://www.freshping.io) and create a free account
2. Add a new check pointing to your `/health` endpoint
3. Set check interval to 1 minute (free tier allows this)

**Note**: Replace `YOUR-REPLIT-URL` with your actual Replit URL (visible in the webview panel).

## Usage

### Testing Health Check
```bash
curl https://YOUR-REPLIT-URL/health
```

### Webhook Integration
Configure your Bentley iTwin webhook to point to:
```
https://YOUR-REPLIT-URL/webhook
```

## Recent Changes
- 2024-12-04: Initial project setup
  - Created FastAPI application with webhook and health endpoints
  - Integrated DeepSeek AI for event analysis
  - Configured environment variables and deployment settings
