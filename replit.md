# Bentley iTwin Webhooks Dashboard MVP

## Overview
This project is a webhook service for the Bentley iTwin platform that receives webhook events and displays them in a live dashboard. It's built with Python/FastAPI for simplicity and reliability.

## Current State
- All endpoints functional and returning HTTP 200
- Dashboard auto-refreshes every 15 seconds
- In-memory event storage (resets on restart)

## Project Structure
```
/
├── main.py              # FastAPI application with all endpoints
├── requirements.txt     # Python dependencies (fastapi, uvicorn, requests)
├── smoke-test.sh        # Tests all endpoints
├── seed.sh              # Seeds 20 test events
├── README.md            # Documentation with URLs
├── .gitignore           # Python ignores
└── GemAiAgent/          # Legacy folder (original import)
```

## Key Endpoints
- `/` - Service info
- `/health` - Health check
- `/webhook` - POST endpoint for iTwin events
- `/events` - List recent events
- `/dashboard` - HTML dashboard
- `/dashboard/feed` - JSON data for dashboard

## URLs
- Dev: https://workspace.suarezcarolina8.replit.dev/dashboard
- Prod: https://workspace.suarezcarolina8.replit.app/dashboard

## Recent Changes
- 2024-12-10: Initial MVP setup with FastAPI
- All required endpoints implemented
- Dashboard with KPIs, health status, and events table
- Smoke test and seed scripts created

## User Preferences
- Keep implementation simple and lightweight
- Use vanilla HTML/CSS/JS for dashboard (no external frameworks)
- In-memory storage is acceptable for MVP
