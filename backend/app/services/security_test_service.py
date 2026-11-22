"""
Security Verification Module for PR-Sentinel.
Contains controlled security test cases to verify AST parsing, OWASP analysis,
Adversarial Verifier gate, and GitHub inline code suggestion generation.
NOTE: Avoid real API key patterns so GitHub Push Protection is not triggered.
"""

import os
import pickle
import subprocess
from typing import Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


# 1. SQL INJECTION VULNERABILITY (CWE-89: Improper Neutralization of Special Elements used in an SQL Command)
# Target for Detection: SQLi Specialist Node -> Verifier should generate parameterized query suggestion
async def fetch_user_profile_insecure(db: AsyncSession, username: str) -> list[Any]:
    """
    VULNERABLE: Direct f-string interpolation into SQL statement.
    Allows authentication bypass or data exfiltration via ' OR 1=1 --
    """
    raw_query = f"SELECT id, username, email, is_active FROM users WHERE username = '{username}'"
    result = await db.execute(text(raw_query))
    return list(result.fetchall())


# 2. COMMAND INJECTION VULNERABILITY (CWE-78: Improper Neutralization of Special Elements used in an OS Command)
# Target for Detection: Command Injection Specialist Node -> Verifier should generate shlex / subprocess.run list suggestion
def execute_system_diagnostics(target_host: str) -> int:
    """
    VULNERABLE: Direct concatenation of user input into OS shell command.
    Allows command execution via '127.0.0.1; cat /etc/passwd'
    """
    command = f"ping -c 1 {target_host}"
    return os.system(command)


# 3. PATH TRAVERSAL VULNERABILITY (CWE-22: Improper Limitation of a Pathname to a Restricted Directory)
# Target for Detection: Path traversal / Arbitrary file read
def read_system_log_file(filename: str) -> str:
    """
    VULNERABLE: Unsanitized path concatenation allows ../ directory traversal.
    """
    log_dir = "/var/log/app"
    target_path = os.path.join(log_dir, filename)
    with open(target_path, "r", encoding="utf-8") as f:
        return f.read()


# 4. INSECURE DESERIALIZATION (CWE-502: Deserialization of Untrusted Data)
# Target for Detection: Untrusted pickle.loads leading to remote code execution
def deserialize_cached_session(session_payload: bytes) -> Any:
    """
    VULNERABLE: Unpickling untrusted user payload allows arbitrary code execution.
    """
    return pickle.loads(session_payload)


# 5. BENCHMARK SAFE PATTERNS (Adversarial Verifier Test)
# Target for Detection: Adversarial Verifier Gate MUST NOT flag or comment on these functions
async def fetch_user_profile_secure(db: AsyncSession, username: str) -> list[Any]:
    """
    SAFE: Uses SQLAlchemy bind parameters (:username).
    Safe from SQL injection attacks. Verifier must dismiss candidate false positives.
    """
    safe_query = text("SELECT id, username, email, is_active FROM users WHERE username = :username")
    result = await db.execute(safe_query, {"username": username})
    return list(result.fetchall())


def execute_diagnostics_secure(target_host: str) -> subprocess.CompletedProcess[str]:
    """
    SAFE: Uses parameterized command array with shell=False.
    Safe from OS command injection.
    """
    safe_cmd = ["ping", "-c", "1", target_host]
    return subprocess.run(safe_cmd, capture_output=True, text=True, check=False)
