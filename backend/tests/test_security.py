import hashlib
import hmac

from app.core.security import verify_github_signature


def test_verify_github_signature_valid():
    secret = "super_secret_webhook_key"
    payload = b'{"action": "opened", "number": 42}'
    computed_hash = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    signature_header = f"sha256={computed_hash}"

    assert verify_github_signature(payload, signature_header, secret) is True


def test_verify_github_signature_invalid_hash():
    secret = "super_secret_webhook_key"
    payload = b'{"action": "opened", "number": 42}'
    tampered_hash = "0" * 64
    signature_header = f"sha256={tampered_hash}"

    assert verify_github_signature(payload, signature_header, secret) is False


def test_verify_github_signature_tampered_payload():
    secret = "super_secret_webhook_key"
    payload = b'{"action": "opened", "number": 42}'
    computed_hash = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    signature_header = f"sha256={computed_hash}"

    tampered_payload = b'{"action": "opened", "number": 43}'
    assert verify_github_signature(tampered_payload, signature_header, secret) is False


def test_verify_github_signature_missing_header():
    secret = "super_secret_webhook_key"
    payload = b'{"action": "opened"}'

    assert verify_github_signature(payload, None, secret) is False
    assert verify_github_signature(payload, "", secret) is False


def test_verify_github_signature_missing_prefix():
    secret = "super_secret_webhook_key"
    payload = b'{"action": "opened"}'
    computed_hash = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    # Missing 'sha256=' prefix
    assert verify_github_signature(payload, computed_hash, secret) is False


def test_verify_github_signature_empty_secret():
    payload = b'{"action": "opened"}'
    assert verify_github_signature(payload, "sha256=123", "") is False
