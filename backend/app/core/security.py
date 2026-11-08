import hashlib
import hmac
from typing import Optional


def verify_github_signature(
    payload_body: bytes,
    signature_header: Optional[str],
    secret: str,
) -> bool:
    """
    Verify GitHub webhook signature using HMAC-SHA256 with constant-time comparison.

    :param payload_body: Raw request body bytes.
    :param signature_header: Value of X-Hub-Signature-256 header (format: 'sha256=<hex>').
    :param secret: The configured webhook secret.
    :return: True if signature is valid, False otherwise.
    """
    if not secret:
        return False

    if not signature_header:
        return False

    if not signature_header.startswith("sha256="):
        return False

    received_sig = signature_header.split("sha256=", 1)[1]

    expected_sig = hmac.new(
        key=secret.encode("utf-8"),
        msg=payload_body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(received_sig, expected_sig)

