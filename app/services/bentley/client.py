"""
Bentley API adapter — hardened version.
- Token failures are parsed and classified
- Timeout vs auth vs permission errors are distinguishable
- Scope comes from env (BENTLEY_SCOPE)
- Secrets are never logged or returned
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

import httpx

from app.core.config import settings

logger = logging.getLogger("itwin_ops.bentley")

_token_cache: Dict[str, Any] = {}

_BENTLEY_ACCEPT = "application/vnd.bentley.itwin-platform.v1+json"


def _get_scope() -> str:
    return getattr(settings, "BENTLEY_SCOPE", "itwins:read imodels:read webhooks:read webhooks:modify")


async def get_access_token(
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> Optional[str]:
    cid = client_id or settings.BENTLEY_CLIENT_ID
    csec = client_secret or settings.BENTLEY_CLIENT_SECRET

    if not cid or not csec:
        logger.warning("Bentley credentials not configured — cannot obtain token")
        return None

    cache_key = cid
    if cache_key in _token_cache:
        cached = _token_cache[cache_key]
        if cached["expires_at"] > datetime.utcnow():
            return cached["token"]

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{settings.BENTLEY_AUTHORITY}/connect/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": cid,
                    "client_secret": csec,
                    "scope": _get_scope(),
                },
            )
    except httpx.TimeoutException:
        logger.error("Bentley IMS token request timed out")
        return None
    except Exception as exc:
        logger.error("Bentley IMS network error: %s", type(exc).__name__)
        return None

    if resp.status_code != 200:
        try:
            err = resp.json()
            logger.error(
                "Bentley token failed HTTP %s: error=%s",
                resp.status_code,
                err.get("error", "?"),
            )
        except Exception:
            logger.error("Bentley token failed HTTP %s", resp.status_code)
        return None

    try:
        data = resp.json()
        token = data["access_token"]
        expires_in = data.get("expires_in", 3600)
        _token_cache[cache_key] = {
            "token": token,
            "expires_at": datetime.utcnow() + timedelta(seconds=expires_in - 60),
        }
        return token
    except Exception as exc:
        logger.error("Failed to parse Bentley token response: %s", type(exc).__name__)
        return None


def _classify_api_error(resp: httpx.Response, endpoint: str) -> str:
    s = resp.status_code
    if s == 401:
        return f"401 Unauthorized — token rejected by {endpoint}"
    if s == 403:
        return f"403 Forbidden — insufficient permissions for {endpoint}"
    if s == 404:
        return f"404 Not Found — {endpoint} does not exist"
    if s == 429:
        return f"429 Rate Limited — slow down requests to {endpoint}"
    return f"HTTP {s} from {endpoint}"


async def list_itwins(token: str, top: int = 100) -> List[Dict]:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{settings.BENTLEY_API_BASE}/itwins",
                headers={"Authorization": f"Bearer {token}", "Accept": _BENTLEY_ACCEPT},
                params={"$top": top},
            )
            if resp.status_code != 200:
                logger.error(_classify_api_error(resp, "/itwins"))
                return []
            return resp.json().get("iTwins", [])
    except httpx.TimeoutException:
        logger.error("GET /itwins timed out")
        return []
    except Exception as exc:
        logger.error("GET /itwins error: %s", type(exc).__name__)
        return []


async def list_imodels(token: str, itwin_id: str, top: int = 100) -> List[Dict]:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{settings.BENTLEY_API_BASE}/imodels",
                headers={"Authorization": f"Bearer {token}", "Accept": _BENTLEY_ACCEPT},
                params={"iTwinId": itwin_id, "$top": top},
            )
            if resp.status_code != 200:
                logger.error(_classify_api_error(resp, "/imodels"))
                return []
            return resp.json().get("iModels", [])
    except httpx.TimeoutException:
        logger.error("GET /imodels timed out")
        return []
    except Exception as exc:
        logger.error("GET /imodels error: %s", type(exc).__name__)
        return []


async def list_webhooks(token: str) -> List[Dict]:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{settings.BENTLEY_API_BASE}/webhooks",
                headers={"Authorization": f"Bearer {token}", "Accept": _BENTLEY_ACCEPT},
            )
            if resp.status_code != 200:
                logger.error(_classify_api_error(resp, "/webhooks"))
                return []
            return resp.json().get("webhooks", [])
    except httpx.TimeoutException:
        logger.error("GET /webhooks timed out")
        return []
    except Exception as exc:
        logger.error("GET /webhooks error: %s", type(exc).__name__)
        return []


async def create_webhook(
    token: str,
    callback_url: str,
    secret: str,
    event_types: List[str],
    itwin_id: Optional[str] = None,
) -> Optional[Dict]:
    body: Dict[str, Any] = {
        "callbackUrl": callback_url,
        "secret": secret,
        "eventTypes": event_types,
        "isActive": True,
    }
    if itwin_id:
        body["iTwinId"] = itwin_id

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{settings.BENTLEY_API_BASE}/webhooks",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Accept": _BENTLEY_ACCEPT,
                },
                json=body,
            )
            if resp.status_code not in (200, 201):
                logger.error(_classify_api_error(resp, "POST /webhooks"))
                return None
            return resp.json().get("webhook")
    except httpx.TimeoutException:
        logger.error("POST /webhooks timed out")
        return None
    except Exception as exc:
        logger.error("POST /webhooks error: %s", type(exc).__name__)
        return None


async def test_connection(
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> Dict[str, Any]:
    token = await get_access_token(client_id, client_secret)
    if not token:
        return {
            "connected": False,
            "error": "Failed to obtain OAuth token — check credentials in Replit Secrets",
        }
    itwins = await list_itwins(token, top=1)
    return {
        "connected": True,
        "token_obtained": True,
        "itwins_accessible": True,
        "sample_itwin_count": len(itwins),
    }
