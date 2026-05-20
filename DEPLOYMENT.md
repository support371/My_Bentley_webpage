# Deployment Guide - iTwin Ops Platform

This guide covers deploying both the Next.js frontend and FastAPI backend.

## Prerequisites

- Node.js 18+ (frontend)
- Python 3.11+ (backend)
- PostgreSQL 14+ (production database)
- Docker (optional, for containerized deployment)
- Vercel account (for frontend deployment)
- Azure/AWS/GCP account (for backend deployment)

## Frontend Deployment (Next.js on Vercel)

### 1. Prepare for Deployment

```bash
# Build the project locally first
npm run build

# Test production build
npm run start
```

### 2. Deploy to Vercel

**Option A: Using Vercel CLI**

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy to Vercel
vercel

# Set production environment
vercel --prod
```

**Option B: GitHub Integration (Recommended)**

1. Push code to GitHub
2. Log in to vercel.com
3. Click "Add New Project"
4. Select your repository
5. Configure environment variables
6. Click "Deploy"

### 3. Configure Environment Variables on Vercel

In Vercel dashboard, go to Settings → Environment Variables and add:

```
NEXT_PUBLIC_API_URL=https://your-backend.com
NEXT_PUBLIC_WS_URL=wss://your-backend.com
```

## Backend Deployment (FastAPI)

### 1. Production Database Setup

**PostgreSQL on Azure Database**

```bash
# Create PostgreSQL instance
az postgres server create \
  --resource-group myResourceGroup \
  --name itwin-ops-db \
  --location eastus \
  --admin-user dbadmin \
  --admin-password <secure-password> \
  --sku-name B_Gen5_1 \
  --storage-size 51200

# Get connection string
az postgres server show-connection-string \
  --server-name itwin-ops-db \
  --admin-user dbadmin
```

### 2. Create Production Environment File

```bash
# Copy example to production config
cp .env.example .env.production

# Edit with production values
nano .env.production
```

**Required production settings:**

```env
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=<generate-random-64-char-key>
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/itwin_ops
COOKIE_SECURE=True
CORS_ORIGINS=https://your-frontend.vercel.app,https://your-domain.com
WEBHOOK_SECRET=<generate-random-token>
SKIP_SIGNATURE_VERIFY=False

# OAuth Configuration
GOOGLE_CLIENT_ID=<prod-client-id>
GOOGLE_CLIENT_SECRET=<prod-secret>
GITHUB_CLIENT_ID=<prod-client-id>
GITHUB_CLIENT_SECRET=<prod-secret>

# Bentley Configuration
BENTLEY_CLIENT_ID=<prod-client-id>
BENTLEY_CLIENT_SECRET=<prod-secret>
```

### 3. Docker Deployment

**Build Docker image:**

```bash
# Build production image
docker build -t itwin-ops:latest .

# Test locally
docker run -p 5000:5000 \
  --env-file .env.production \
  itwin-ops:latest
```

**Docker Compose (local multi-container):**

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: itwin_ops
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build: .
    ports:
      - "5000:5000"
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:password@postgres:5432/itwin_ops
      ENVIRONMENT: production
    depends_on:
      - postgres

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://backend:5000
      NEXT_PUBLIC_WS_URL: ws://backend:5000
    depends_on:
      - backend

volumes:
  postgres_data:
```

**Run with Docker Compose:**

```bash
docker-compose up -d
```

### 4. Azure App Service Deployment

```bash
# Create resource group
az group create --name itwin-ops-rg --location eastus

# Create App Service plan
az appservice plan create \
  --name itwin-ops-plan \
  --resource-group itwin-ops-rg \
  --sku B1 \
  --is-linux

# Create web app
az webapp create \
  --resource-group itwin-ops-rg \
  --plan itwin-ops-plan \
  --name itwin-ops-api \
  --runtime "PYTHON|3.11"

# Configure environment variables
az webapp config appsettings set \
  --resource-group itwin-ops-rg \
  --name itwin-ops-api \
  --settings @appsettings.json

# Deploy from Git
az webapp deployment source config-zip \
  --resource-group itwin-ops-rg \
  --name itwin-ops-api \
  --src deploy.zip
```

### 5. AWS Elastic Beanstalk Deployment

```bash
# Initialize Elastic Beanstalk application
eb init -p python-3.11 itwin-ops

# Create environment
eb create itwin-ops-prod

# Deploy application
eb deploy

# View logs
eb logs
```

## Database Migrations

### Initial Schema Setup

```bash
# Run migrations (if using Alembic)
alembic upgrade head

# Or manually create schema
python -c "
from app.db.database import engine
from app.models import Base
Base.metadata.create_all(bind=engine)
"
```

### Seed Initial Data

```bash
# Seed admin user and default data
python -m app.db.seed
```

## SSL/TLS Configuration

### For Vercel Frontend
Vercel automatically provides free SSL certificates.

### For Backend (Azure/AWS)

**Azure:**
```bash
az webapp config ssl create \
  --resource-group itwin-ops-rg \
  --name itwin-ops-api \
  --certificate-path /path/to/certificate.pfx \
  --certificate-password <password>
```

**AWS:**
```bash
# Request certificate in ACM, then attach to load balancer
```

## Health Checks

```bash
# Frontend health check
curl https://your-frontend.vercel.app/api/health

# Backend health check
curl https://your-backend.com/health

# WebSocket health check
wscat -c wss://your-backend.com/ws/events
```

## Monitoring & Logging

### Application Monitoring

- **Frontend**: Vercel Analytics (automatic)
- **Backend**: Add to FastAPI:

```python
from fastapi_prometheus_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

### Centralized Logging

**Option 1: Azure Monitor**

```python
from opencensus.ext.azure.log_exporter import AzureLogHandler
import logging

logging.getLogger().addHandler(AzureLogHandler(
    connection_string="InstrumentationKey=..."
))
```

**Option 2: Sentry (Error Tracking)**

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FastApiIntegration()],
)
```

## Troubleshooting

### Common Issues

**1. CORS Errors**
- Check `CORS_ORIGINS` environment variable
- Ensure frontend URL is in the list
- Verify no trailing slashes

**2. WebSocket Connection Failed**
- Check `NEXT_PUBLIC_WS_URL` matches backend
- Ensure backend allows WebSocket upgrades
- Check firewall rules

**3. OAuth Not Working**
- Verify redirect URIs match exactly
- Check client ID/secret in environment
- Ensure OAuth provider is configured

**4. Database Connection Issues**
- Test connection: `psql <DATABASE_URL>`
- Check network security groups allow port 5432
- Verify credentials in .env

## Rollback Procedure

**Vercel:**
```bash
# Rollback to previous deployment
vercel rollback
```

**Azure:**
```bash
# View deployment history
az webapp deployment list --resource-group itwin-ops-rg --name itwin-ops-api

# Redeploy previous version
az webapp deployment slot swap --resource-group itwin-ops-rg --name itwin-ops-api
```

## Performance Optimization

### Frontend
- Enable static generation: `getStaticProps`
- Implement image optimization: `next/image`
- Code splitting: automatic with Next.js
- CDN: Vercel provides global CDN

### Backend
- Enable HTTP caching headers
- Implement database connection pooling
- Use async operations throughout
- Cache API responses with Redis

## Backup & Recovery

### Database Backups

```bash
# Azure automated backups
az postgres server backup create \
  --resource-group itwin-ops-rg \
  --server-name itwin-ops-db \
  --backup-name manual-backup-$(date +%s)

# Restore from backup
az postgres server restore \
  --resource-group itwin-ops-rg \
  --name itwin-ops-db-restored \
  --restore-point-in-time 2024-01-01T12:00:00
```

## Support & Documentation

- **Frontend**: https://nextjs.org/docs
- **Backend**: https://fastapi.tiangolo.com
- **Bentley API**: https://developer.bentley.com
- **Issues**: GitHub Issues in your repository
