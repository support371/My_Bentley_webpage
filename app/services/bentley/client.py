"""
Bentley API adapter layer.
Handles OAuth token acquisition and API calls to the Bentley platform.
Requires BENTLEY_CLIENT_ID and BENTLEY_CLIENT_SECRET to be configured.
"""
import logging
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from app.core.config import settings

logger = logging.getLogger("itwin_ops.bentley")

_token_cache: Dict[str, Any] = {}


async def get_access_token(client_id: Optional[str] = None, client_secret: Optional[str] = None) -> Optional[str]:
    cid = client_id or settings.BENTLEY_CLIENT_ID
    csec = client_secret or settings.BENTLEY_CLIENT_SECRET

    if not cid or not csec:
        logger.warning("Bentley credentials not configured")
        return None

    cache_key = cid
    if cache_key in _token_cache:
        cached = _token_cache[cache_key]
        if cached["expires_at"] > datetime.utcnow():
            return cached["token"]

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.BENTLEY_AUTHORITY}/connect/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": cid,
                    "client_secret": csec,
                    "scope": "itwins:read imodels:read",
                },
                timeout=15,
            )
            resp.raise_for_status()
            token_data = resp.json()
            token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)

            _token_cache[cache_key] = {
                "token": token,
                "expires_at": datetime.utcnow() + timedelta(seconds=expires_in - 60),
            }
            return token
    except Exception as e:
        logger.error(f"Failed to get Bentley token: {e}")
        return None


async def list_itwins(token: str, top: int = 100) -> List[Dict]:
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.BENTLEY_API_BASE}/itwins",
                headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.bentley.itwin-platform.v1+json"},
                params={"$top": top},
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json().get("iTwins", [])
    except Exception as e:
        logger.error(f"Failed to list iTwins: {e}")
        return []


async def list_imodels(token: str, itwin_id: str, top: int = 100) -> List[Dict]:
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.BENTLEY_API_BASE}/imodels",
                headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.bentley.itwin-platform.v1+json"},
                params={"iTwinId": itwin_id, "$top": top},
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json().get("iModels", [])
    except Exception as e:
        logger.error(f"Failed to list iModels for {itwin_id}: {e}")
        return []


async def list_webhooks(token: str) -> List[Dict]:
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.BENTLEY_API_BASE}/webhooks",
                headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.bentley.itwin-platform.v1+json"},
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json().get("webhooks", [])
    except Exception as e:
        logger.error(f"Failed to list webhooks: {e}")
        return []


async def create_webhook(token: str, callback_url: str, secret: str, event_types: List[str], itwin_id: Optional[str] = None) -> Optional[Dict]:
    body: Dict[str, Any] = {
        "callbackUrl": callback_url,
        "secret": secret,
        "eventTypes": event_types,
        "isActive": True,
    }
    if itwin_id:
        body["iTwinId"] = itwin_id

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.BENTLEY_API_BASE}/webhooks",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Accept": "application/vnd.bentley.itwin-platform.v1+json",
                },
                json=body,
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json().get("webhook")
    except Exception as e:
        logger.error(f"Failed to create webhook: {e}")
        return None


async def test_connection(client_id: Optional[str] = None, client_secret: Optional[str] = None) -> Dict[str, Any]:
    token = await get_access_token(client_id, client_secret)
    if not token:
        return {"connected": False, "error": "Failed to obtain access token — check credentials"}
    itwins = await list_itwins(token, top=1)
    return {
        "connected": True,
        "token_obtained": True,
        "sample_itwin_count": len(itwins),
    }
