"""
Tests for the Bentley diagnostics service.
Run with: pytest tests/test_diagnostics.py -v
"""
import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import httpx


# ─── Unit tests (no network, no DB) ──────────────────────────────────────────

class TestCheckEnvConfiguration:
    def test_both_missing(self):
        from app.services.bentley.diagnostics import check_env_configuration
        with patch("app.services.bentley.diagnostics.settings") as s:
            s.BENTLEY_CLIENT_ID = None
            s.BENTLEY_CLIENT_SECRET = None
            r = check_env_configuration()
        assert r["ok"] is False
        assert r["error_class"] == "missing_credentials"
        assert "both missing" in r["short_message"].lower()

    def test_id_missing(self):
        from app.services.bentley.diagnostics import check_env_configuration
        with patch("app.services.bentley.diagnostics.settings") as s:
            s.BENTLEY_CLIENT_ID = None
            s.BENTLEY_CLIENT_SECRET = "secret"
            r = check_env_configuration()
        assert r["ok"] is False
        assert "BENTLEY_CLIENT_ID" in r["short_message"]

    def test_secret_missing(self):
        from app.services.bentley.diagnostics import check_env_configuration
        with patch("app.services.bentley.diagnostics.settings") as s:
            s.BENTLEY_CLIENT_ID = "some-id"
            s.BENTLEY_CLIENT_SECRET = None
            r = check_env_configuration()
        assert r["ok"] is False
        assert "BENTLEY_CLIENT_SECRET" in r["short_message"]

    def test_both_present(self):
        from app.services.bentley.diagnostics import check_env_configuration
        with patch("app.services.bentley.diagnostics.settings") as s:
            s.BENTLEY_CLIENT_ID = "abc123id"
            s.BENTLEY_CLIENT_SECRET = "supersecret"
            r = check_env_configuration()
        assert r["ok"] is True


class TestMaskClientId:
    def test_none(self):
        from app.services.bentley.diagnostics import mask_client_id
        assert mask_client_id(None) == "(not set)"

    def test_short(self):
        from app.services.bentley.diagnostics import mask_client_id
        assert mask_client_id("abc") == "****"

    def test_long(self):
        from app.services.bentley.diagnostics import mask_client_id
        result = mask_client_id("abcd1234efgh5678")
        assert result.startswith("abcd")
        assert result.endswith("5678")
        assert "****" in result
        assert "1234" not in result   # middle is masked

    def test_no_secret_leaked(self):
        from app.services.bentley.diagnostics import mask_client_id
        full = "my-super-secret-client-id-full"
        masked = mask_client_id(full)
        assert full not in masked


class TestCheckWebhookSecurityState:
    def test_secret_missing(self):
        from app.services.bentley.diagnostics import check_webhook_security_state
        with patch("app.services.bentley.diagnostics.settings") as s:
            s.WEBHOOK_SECRET = ""
            s.SKIP_SIGNATURE_VERIFY = True
            s.ENVIRONMENT = "development"
            r = check_webhook_security_state()
        assert r["ok"] is False
        assert r["error_class"] in ("webhook_secret_missing", "signature_verification_disabled")

    def test_all_secure(self):
        from app.services.bentley.diagnostics import check_webhook_security_state
        with patch("app.services.bentley.diagnostics.settings") as s:
            s.WEBHOOK_SECRET = "a" * 32
            s.SKIP_SIGNATURE_VERIFY = False
            s.ENVIRONMENT = "development"
            r = check_webhook_security_state()
        assert r["ok"] is True

    def test_production_warnings_in_detail(self):
        from app.services.bentley.diagnostics import check_webhook_security_state
        with patch("app.services.bentley.diagnostics.settings") as s:
            s.WEBHOOK_SECRET = ""
            s.SKIP_SIGNATURE_VERIFY = True
            s.ENVIRONMENT = "production"
            r = check_webhook_security_state()
        assert "CRITICAL" in r["technical_detail"]


class TestComputeCallbackUrl:
    def test_public_base_url(self):
        from app.services.bentley.diagnostics import compute_callback_url
        with patch.dict(os.environ, {"PUBLIC_BASE_URL": "https://myapp.replit.app"}, clear=False):
            r = compute_callback_url()
        assert r["short_message"] == "https://myapp.replit.app/webhook"
        assert r["ok"] is True

    def test_replit_domain(self):
        from app.services.bentley.diagnostics import compute_callback_url
        env = {"REPLIT_DOMAIN": "myapp.replit.app"}
        # Remove PUBLIC_BASE_URL if set
        clean = {k: v for k, v in os.environ.items() if k != "PUBLIC_BASE_URL"}
        clean.update(env)
        clean.pop("PUBLIC_BASE_URL", None)
        with patch.dict(os.environ, clean, clear=True):
            r = compute_callback_url()
        assert "myapp.replit.app/webhook" in r["short_message"]

    def test_request_fallback(self):
        from app.services.bentley.diagnostics import compute_callback_url
        req = MagicMock()
        req.base_url = "http://localhost:5000/"
        clean = {k: v for k, v in os.environ.items()
                 if k not in ("PUBLIC_BASE_URL", "REPLIT_DOMAIN", "REPLIT_DEV_DOMAIN")}
        with patch.dict(os.environ, clean, clear=True):
            r = compute_callback_url(req)
        assert "/webhook" in r["short_message"]

    def test_no_env_no_request(self):
        from app.services.bentley.diagnostics import compute_callback_url
        clean = {k: v for k, v in os.environ.items()
                 if k not in ("PUBLIC_BASE_URL", "REPLIT_DOMAIN", "REPLIT_DEV_DOMAIN")}
        with patch.dict(os.environ, clean, clear=True):
            r = compute_callback_url(None)
        assert r["ok"] is False
        assert r["error_class"] == "callback_url_not_ready"


class TestSummaryProductionWarnings:
    @pytest.mark.asyncio
    async def test_production_warnings_emitted(self):
        from app.services.bentley.diagnostics import summarize_bentley_readiness
        with patch("app.services.bentley.diagnostics.settings") as s:
            s.ENVIRONMENT = "production"
            s.SKIP_SIGNATURE_VERIFY = True
            s.WEBHOOK_SECRET = ""
            s.BENTLEY_CLIENT_ID = None
            s.BENTLEY_CLIENT_SECRET = None
            s.COOKIE_SECURE = False
            result = await summarize_bentley_readiness()
        assert len(result["production_warnings"]) >= 2

    @pytest.mark.asyncio
    async def test_no_warnings_in_dev(self):
        from app.services.bentley.diagnostics import summarize_bentley_readiness
        with patch("app.services.bentley.diagnostics.settings") as s:
            s.ENVIRONMENT = "development"
            s.SKIP_SIGNATURE_VERIFY = True
            s.WEBHOOK_SECRET = ""
            s.BENTLEY_CLIENT_ID = None
            s.BENTLEY_CLIENT_SECRET = None
            s.COOKIE_SECURE = False
            result = await summarize_bentley_readiness()
        assert result["production_warnings"] == []


class TestOAuthClassification:
    @pytest.mark.asyncio
    async def test_missing_credentials(self):
        from app.services.bentley.diagnostics import test_oauth_token
        with patch("app.services.bentley.diagnostics.settings") as s:
            s.BENTLEY_CLIENT_ID = None
            s.BENTLEY_CLIENT_SECRET = None
            s.BENTLEY_AUTHORITY = "https://ims.bentley.com"
            s.BENTLEY_SCOPE = "itwins:read"
            r = await test_oauth_token(None, None)
        assert r["ok"] is False
        assert r["error_class"] == "missing_credentials"

    @pytest.mark.asyncio
    async def test_invalid_client_400(self):
        from app.services.bentley.diagnostics import test_oauth_token
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.json.return_value = {"error": "invalid_client", "error_description": "Unknown client"}
        with patch("app.services.bentley.diagnostics.settings") as s:
            s.BENTLEY_CLIENT_ID = "bad-id"
            s.BENTLEY_CLIENT_SECRET = "bad-secret"
            s.BENTLEY_AUTHORITY = "https://ims.bentley.com"
            s.BENTLEY_SCOPE = "itwins:read"
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_client.post = AsyncMock(return_value=mock_resp)
                mock_client_cls.return_value = mock_client
                r = await test_oauth_token("bad-id", "bad-secret")
        assert r["ok"] is False
        assert r["error_class"] == "invalid_client"

    @pytest.mark.asyncio
    async def test_timeout(self):
        from app.services.bentley.diagnostics import test_oauth_token
        with patch("app.services.bentley.diagnostics.settings") as s:
            s.BENTLEY_CLIENT_ID = "some-id"
            s.BENTLEY_CLIENT_SECRET = "some-secret"
            s.BENTLEY_AUTHORITY = "https://ims.bentley.com"
            s.BENTLEY_SCOPE = "itwins:read"
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
                mock_client_cls.return_value = mock_client
                r = await test_oauth_token("some-id", "some-secret")
        assert r["ok"] is False
        assert "timeout" in r["short_message"].lower()
