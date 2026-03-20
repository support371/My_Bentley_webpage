import hmac
import hashlib
import pytest
from app.core.security import verify_webhook_signature, hash_password, verify_password, create_token, decode_token


def test_password_hash_and_verify():
    hashed = hash_password("mypassword")
    assert verify_password("mypassword", hashed)
    assert not verify_password("wrong", hashed)


def test_jwt_create_and_decode():
    token = create_token({"sub": "user123", "role": "admin"})
    payload = decode_token(token)
    assert payload["sub"] == "user123"
    assert payload["role"] == "admin"


def test_jwt_invalid():
    result = decode_token("not.a.valid.token")
    assert result is None


def test_webhook_signature_skip_when_empty():
    assert verify_webhook_signature(b"payload", "") is True


def test_webhook_signature_valid(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "SKIP_SIGNATURE_VERIFY", False)
    monkeypatch.setattr(settings, "WEBHOOK_SECRET", "test-secret")
    payload = b'{"eventType":"test"}'
    sig = hmac.new(b"test-secret", payload, hashlib.sha256).hexdigest()
    assert verify_webhook_signature(payload, sig) is True


def test_webhook_signature_invalid(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "SKIP_SIGNATURE_VERIFY", False)
    monkeypatch.setattr(settings, "WEBHOOK_SECRET", "test-secret")
    payload = b'{"eventType":"test"}'
    assert verify_webhook_signature(payload, "bad-signature") is False
