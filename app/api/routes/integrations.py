import json
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select

from app.db.database import get_session
from app.models.integrations import Integration
from app.core.security import get_optional_user
from app.core.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger("itwin_ops.integrations")

INTEGRATION_CATALOG = [
    {"slug": "github", "name": "GitHub", "category": "Source Control", "icon_emoji": "🐙",
     "icon_color": "#24292f", "description": "Connect repositories, automate workflows, and sync code events.", "docs_url": "https://docs.github.com/en/rest"},
    {"slug": "gitlab", "name": "GitLab", "category": "Source Control", "icon_emoji": "🦊",
     "icon_color": "#fc6d26", "description": "Full DevOps platform — CI/CD, repos, and issues in one.", "docs_url": "https://docs.gitlab.com/ee/api/"},
    {"slug": "gitbucket", "name": "GitBucket", "category": "Source Control", "icon_emoji": "🪣",
     "icon_color": "#4183c4", "description": "Self-hosted GitHub clone for your infrastructure.", "docs_url": "https://github.com/gitbucket/gitbucket"},
    {"slug": "bitbucket", "name": "Bitbucket", "category": "Source Control", "icon_emoji": "🏢",
     "icon_color": "#0052cc", "description": "Atlassian Git hosting with Jira and Trello integration.", "docs_url": "https://developer.atlassian.com/cloud/bitbucket/"},
    {"slug": "vercel", "name": "Vercel", "category": "Cloud & Deploy", "icon_emoji": "▲",
     "icon_color": "#000000", "description": "Deploy frontends instantly with preview URLs on every push.", "docs_url": "https://vercel.com/docs/rest-api"},
    {"slug": "railway", "name": "Railway", "category": "Cloud & Deploy", "icon_emoji": "🚂",
     "icon_color": "#0b0d0e", "description": "Instant app deployment with databases and secrets management.", "docs_url": "https://docs.railway.app/reference/public-api"},
    {"slug": "cloudflare", "name": "Cloudflare", "category": "Cloud & Deploy", "icon_emoji": "🔶",
     "icon_color": "#f6821f", "description": "CDN, DNS, Workers, and edge security for your domains.", "docs_url": "https://developers.cloudflare.com/api/"},
    {"slug": "azure", "name": "Azure", "category": "Cloud & Deploy", "icon_emoji": "☁️",
     "icon_color": "#0078d4", "description": "Microsoft Azure cloud — AI, compute, and DevOps services.", "docs_url": "https://learn.microsoft.com/en-us/rest/api/azure/"},
    {"slug": "openai", "name": "ChatGPT / OpenAI", "category": "AI & LLM", "icon_emoji": "🤖",
     "icon_color": "#10a37f", "description": "GPT-4, DALL-E, and Whisper APIs for AI-powered features.", "docs_url": "https://platform.openai.com/docs"},
    {"slug": "gemini", "name": "Gemini (Google AI)", "category": "AI & LLM", "icon_emoji": "✨",
     "icon_color": "#4285f4", "description": "Google's multimodal AI models — text, image, and code.", "docs_url": "https://ai.google.dev/docs"},
    {"slug": "copilot", "name": "GitHub Copilot", "category": "AI & LLM", "icon_emoji": "🧠",
     "icon_color": "#6e40c9", "description": "AI pair programmer — code suggestions and chat in your IDE.", "docs_url": "https://docs.github.com/en/copilot"},
    {"slug": "deepseek", "name": "DeepSeek AI", "category": "AI & LLM", "icon_emoji": "🔍",
     "icon_color": "#0066ff", "description": "High-performance open-weight LLMs for reasoning and code.", "docs_url": "https://platform.deepseek.com/api-docs"},
    {"slug": "cursor", "name": "Cursor", "category": "AI & LLM", "icon_emoji": "⚡",
     "icon_color": "#7c3aed", "description": "AI-first code editor built on VSCode with full codebase context.", "docs_url": "https://cursor.sh"},
    {"slug": "devin", "name": "Devin", "category": "AI & LLM", "icon_emoji": "🦾",
     "icon_color": "#ff6b35", "description": "Fully autonomous AI software engineer for end-to-end tasks.", "docs_url": "https://cognition.ai"},
    {"slug": "v0", "name": "v0 by Vercel", "category": "AI & LLM", "icon_emoji": "🎨",
     "icon_color": "#000000", "description": "AI UI component generator — ship polished UI from a prompt.", "docs_url": "https://v0.dev/docs"},
    {"slug": "vscode", "name": "VS Code", "category": "Dev Tools", "icon_emoji": "🖥️",
     "icon_color": "#007acc", "description": "Receive VS Code extension events and workspace signals.", "docs_url": "https://code.visualstudio.com/api"},
    {"slug": "replit", "name": "Replit", "category": "Dev Tools", "icon_emoji": "🔁",
     "icon_color": "#f26207", "description": "Cloud IDE — sync Repls, deployments, and bounties.", "docs_url": "https://docs.replit.com"},
    {"slug": "lovable", "name": "Lovable", "category": "Dev Tools", "icon_emoji": "❤️",
     "icon_color": "#e11d48", "description": "AI-powered app builder — from prompt to shipped product.", "docs_url": "https://lovable.dev"},
    {"slug": "circleci", "name": "CircleCI", "category": "CI/CD", "icon_emoji": "⭕",
     "icon_color": "#161616", "description": "Continuous integration — pipeline status and test results.", "docs_url": "https://circleci.com/docs/api/v2/"},
    {"slug": "devto", "name": "Dev.to", "category": "Community", "icon_emoji": "📝",
     "icon_color": "#3b49df", "description": "Publish articles, follow tags, and surface community activity.", "docs_url": "https://developers.forem.com/api"},
    {"slug": "slack", "name": "Slack", "category": "Notifications", "icon_emoji": "💬",
     "icon_color": "#4a154b", "description": "Post alerts and event summaries to Slack channels.", "docs_url": "https://api.slack.com"},
    {"slug": "discord", "name": "Discord", "category": "Notifications", "icon_emoji": "🎮",
     "icon_color": "#5865f2", "description": "Push webhook notifications to Discord server channels.", "docs_url": "https://discord.com/developers/docs"},
    {"slug": "pagerduty", "name": "PagerDuty", "category": "Notifications", "icon_emoji": "🚨",
     "icon_color": "#06ac38", "description": "On-call alerting and incident management for your team.", "docs_url": "https://developer.pagerduty.com/api-reference"},
    {"slug": "jira", "name": "Jira", "category": "Project Mgmt", "icon_emoji": "🗂️",
     "icon_color": "#0052cc", "description": "Auto-create Jira issues when critical events are detected.", "docs_url": "https://developer.atlassian.com/cloud/jira/platform/rest/v3/"},
    {"slug": "linear", "name": "Linear", "category": "Project Mgmt", "icon_emoji": "📐",
     "icon_color": "#5e6ad2", "description": "Create and update Linear issues from iTwin event triggers.", "docs_url": "https://developers.linear.app/docs"},
    {"slug": "datadog", "name": "Datadog", "category": "Observability", "icon_emoji": "🐕",
     "icon_color": "#632ca6", "description": "Forward metrics and events to Datadog for monitoring.", "docs_url": "https://docs.datadoghq.com/api/"},
    {"slug": "sentry", "name": "Sentry", "category": "Observability", "icon_emoji": "🪲",
     "icon_color": "#362d59", "description": "Error tracking — send iTwin processing errors to Sentry.", "docs_url": "https://docs.sentry.io/api/"},
]

CATEGORIES_ORDER = [
    "Source Control", "Cloud & Deploy", "AI & LLM", "Dev Tools",
    "CI/CD", "Community", "Notifications", "Project Mgmt", "Observability"
]


@router.get("/integrations", response_class=HTMLResponse, tags=["Integrations"])
async def integrations_page(request: Request, session: AsyncSession = Depends(get_session)):
    user = get_optional_user(request)
    result = await session.execute(select(Integration))
    connected = {row.slug: row for row in result.scalars().all()}
    catalog = []
    for item in INTEGRATION_CATALOG:
        entry = dict(item)
        row = connected.get(item["slug"])
        if row:
            entry["db_id"] = row.id
            entry["status"] = row.status
            entry["is_enabled"] = row.is_enabled
            entry["has_credentials"] = bool(row.api_key or row.webhook_url)
            entry["last_tested_at"] = row.last_tested_at
            entry["last_test_result"] = row.last_test_result
        else:
            entry["db_id"] = None
            entry["status"] = "disconnected"
            entry["is_enabled"] = False
            entry["has_credentials"] = False
            entry["last_tested_at"] = None
            entry["last_test_result"] = None
        catalog.append(entry)
    by_category = {}
    for item in catalog:
        cat = item["category"]
        by_category.setdefault(cat, []).append(item)
    categories = [(cat, by_category[cat]) for cat in CATEGORIES_ORDER if cat in by_category]
    connected_count = sum(1 for i in catalog if i["status"] == "connected")
    return templates.TemplateResponse("integrations.html", {
        "request": request,
        "user": user,
        "app_name": settings.APP_NAME,
        "categories": categories,
        "catalog": catalog,
        "connected_count": connected_count,
        "total_count": len(catalog),
    })


@router.get("/api/integrations", tags=["Integrations"])
async def list_integrations(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Integration))
    rows = result.scalars().all()
    return {"integrations": [
        {"id": r.id, "slug": r.slug, "name": r.name, "category": r.category,
         "status": r.status, "is_enabled": r.is_enabled,
         "has_api_key": bool(r.api_key), "has_webhook": bool(r.webhook_url),
         "last_tested_at": r.last_tested_at.isoformat() if r.last_tested_at else None,
         "last_test_result": r.last_test_result}
        for r in rows
    ]}


@router.post("/api/integrations", tags=["Integrations"])
async def create_or_update_integration(request: Request, session: AsyncSession = Depends(get_session)):
    body = await request.json()
    slug = body.get("slug", "").strip().lower().replace(" ", "-")
    if not slug:
        raise HTTPException(status_code=400, detail="slug is required")
    result = await session.execute(select(Integration).where(Integration.slug == slug))
    existing = result.scalars().first()
    catalog_entry = next((c for c in INTEGRATION_CATALOG if c["slug"] == slug), None)
    if existing:
        if body.get("api_key") is not None:
            existing.api_key = body["api_key"] or None
        if body.get("webhook_url") is not None:
            existing.webhook_url = body["webhook_url"] or None
        if body.get("base_url") is not None:
            existing.base_url = body["base_url"] or None
        if body.get("custom_fields") is not None:
            existing.custom_fields = json.dumps(body["custom_fields"]) if isinstance(body["custom_fields"], dict) else body["custom_fields"]
        existing.is_enabled = body.get("is_enabled", existing.is_enabled)
        if existing.api_key or existing.webhook_url:
            existing.status = "connected"
        existing.updated_at = datetime.utcnow()
        await session.commit()
        await session.refresh(existing)
        return {"id": existing.id, "slug": existing.slug, "status": existing.status, "action": "updated"}
    else:
        name = body.get("name") or (catalog_entry["name"] if catalog_entry else slug.title())
        category = body.get("category") or (catalog_entry["category"] if catalog_entry else "Custom")
        row = Integration(
            slug=slug, name=name, category=category,
            description=body.get("description") or (catalog_entry["description"] if catalog_entry else ""),
            icon_emoji=body.get("icon_emoji") or (catalog_entry.get("icon_emoji") if catalog_entry else "🔌"),
            icon_color=body.get("icon_color") or (catalog_entry.get("icon_color") if catalog_entry else "#64748b"),
            docs_url=body.get("docs_url") or (catalog_entry.get("docs_url") if catalog_entry else None),
            api_key=body.get("api_key") or None,
            webhook_url=body.get("webhook_url") or None,
            base_url=body.get("base_url") or None,
            custom_fields=json.dumps(body.get("custom_fields", {})),
            is_enabled=body.get("is_enabled", False),
            status="connected" if (body.get("api_key") or body.get("webhook_url")) else "disconnected",
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return {"id": row.id, "slug": row.slug, "status": row.status, "action": "created"}


@router.post("/api/integrations/{slug}/test", tags=["Integrations"])
async def test_integration(slug: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Integration).where(Integration.slug == slug))
    row = result.scalars().first()
    if not row:
        raise HTTPException(status_code=404, detail="Integration not connected")
    import httpx
    success = False
    message = "No credentials to test"
    if row.webhook_url:
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                r = await client.post(row.webhook_url, json={"test": True, "source": "iTwin Ops Center", "slug": slug})
                success = r.status_code < 400
                message = f"HTTP {r.status_code}"
        except Exception as e:
            message = f"Error: {str(e)[:100]}"
    elif row.api_key:
        success = True
        message = "API key present (not verified)"
    row.last_tested_at = datetime.utcnow()
    row.last_test_result = message
    row.status = "connected" if success else "error"
    await session.commit()
    return {"success": success, "message": message, "status": row.status}


@router.delete("/api/integrations/{slug}", tags=["Integrations"])
async def disconnect_integration(slug: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Integration).where(Integration.slug == slug))
    row = result.scalars().first()
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    row.api_key = None
    row.api_secret = None
    row.webhook_url = None
    row.status = "disconnected"
    row.is_enabled = False
    await session.commit()
    return {"slug": slug, "status": "disconnected"}


@router.get("/api/integrations/catalog", tags=["Integrations"])
async def get_catalog():
    return {"catalog": INTEGRATION_CATALOG, "categories": CATEGORIES_ORDER}
