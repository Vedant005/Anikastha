import json
import pytest
from app.main import app
from app.mcp.client import ExternalMCPConnector, mcp_connector
from app.mcp.server import (
    explain_finding,
    get_repo_policy,
    mcp_server,
    prompt_explain_cwe,
    prompt_precommit,
    resource_repo_policy,
    scan_local_diff,
    suggest_patch,
)

SAMPLE_CLEAN_DIFF = """diff --git a/app/service.py b/app/service.py
index 1234567..89abcdef 100644
--- a/app/service.py
+++ b/app/service.py
@@ -10,3 +10,4 @@ def add(a: int, b: int) -> int:
     return a + b
+    # safe comment
"""

SAMPLE_VULN_SQL_DIFF = """diff --git a/app/db.py b/app/db.py
index 1234567..89abcdef 100644
--- a/app/db.py
+++ b/app/db.py
@@ -10,3 +10,4 @@ async def get_user(username: str):
-    pass
+    query = f"SELECT * FROM users WHERE name = '{username}'"
+    await session.execute(query)
"""

SAMPLE_VULN_SECRET_DIFF = """diff --git a/app/config.py b/app/config.py
index 1234567..89abcdef 100644
--- a/app/config.py
+++ b/app/config.py
@@ -5,2 +5,3 @@
-API_KEY = None
+API_KEY = "ghp_1234567890abcdef1234567890abcdef1234"
"""

SAMPLE_QUALITY_DIFF = """diff --git a/app/worker.py b/app/worker.py
index 1234567..89abcdef 100644
--- a/app/worker.py
+++ b/app/worker.py
@@ -15,3 +15,5 @@ async def process_job():
+    try:
+        time.sleep(5)
+    except:
+        pass
"""


def test_scan_local_diff_clean():
    """Verify clean diff produces APPROVE and zero findings."""
    result = scan_local_diff(SAMPLE_CLEAN_DIFF, repo_name="test-org/clean-repo")
    assert result["verdict"] == "APPROVE"
    assert result["findings_count"] == 0
    assert len(result["findings"]) == 0


def test_scan_local_diff_sql_injection():
    """Verify raw SQL string concatenation flags CWE-89."""
    result = scan_local_diff(SAMPLE_VULN_SQL_DIFF, repo_name="test-org/vuln-repo")
    assert result["verdict"] == "REQUEST_CHANGES"
    assert result["findings_count"] >= 1
    sql_findings = [f for f in result["findings"] if f["cwe"] == "CWE-89"]
    assert len(sql_findings) > 0
    assert "SQL Injection" in sql_findings[0]["title"]
    assert "```suggestion" in sql_findings[0]["suggestion_markdown"]


def test_scan_local_diff_hardcoded_secret():
    """Verify hardcoded GitHub token flags CWE-798."""
    result = scan_local_diff(SAMPLE_VULN_SECRET_DIFF, repo_name="test-org/secret-repo")
    assert result["verdict"] == "REQUEST_CHANGES"
    assert result["findings_count"] >= 1
    secret_findings = [f for f in result["findings"] if f["cwe"] == "CWE-798"]
    assert len(secret_findings) > 0
    assert secret_findings[0]["severity"] == "CRITICAL"


def test_scan_local_diff_quality_smells():
    """Verify bare except and sync sleep in async context are detected."""
    result = scan_local_diff(SAMPLE_QUALITY_DIFF, repo_name="test-org/quality-repo")
    assert result["findings_count"] >= 2
    cwes = [f["cwe"] for f in result["findings"]]
    assert "CWE-391" in cwes  # Bare except
    assert "CWE-400" in cwes  # Sync blocking call


@pytest.mark.asyncio
async def test_get_repo_policy_default():
    """Verify default repository policy has fail severities and allowed licenses."""
    policy = await get_repo_policy("test-org/new-repo")
    assert policy["repo"] == "test-org/new-repo"
    assert "CRITICAL" in policy["fail_severities"]
    assert "MIT" in policy["allowed_licenses"]


def test_explain_finding():
    """Verify finding explanation includes CWE and architectural guidance."""
    explanation = explain_finding(
        cwe="CWE-89",
        title="SQL Injection",
        description="Direct parameter interpolation",
        code_snippet="session.execute(f'SELECT * FROM {name}')",
    )
    assert "CWE-89" in explanation
    assert "Attack Surface" in explanation
    assert "Recommended Remediation" in explanation


def test_suggest_patch():
    """Verify suggest_patch returns formatted suggestion block."""
    patch = suggest_patch(cwe="CWE-89", code_snippet="execute(f'...')")
    assert "select" in patch.lower()
    assert "```python" in patch


def test_mcp_prompts():
    """Verify MCP prompt templates generate actionable system instructions."""
    p1 = prompt_precommit("diff --git a/...")
    assert "PR-Sentinel" in p1
    assert "SQL Injection" in p1

    p2 = prompt_explain_cwe("CWE-798", "app/config.py")
    assert "CWE-798" in p2
    assert "app/config.py" in p2


@pytest.mark.asyncio
async def test_mcp_resources():
    """Verify policy resource generates valid JSON payload."""
    resource_json = await resource_repo_policy("test-org/sample-repo")
    parsed = json.loads(resource_json)
    assert parsed["repo"] == "test-org/sample-repo"
    assert "fail_severities" in parsed


@pytest.mark.asyncio
async def test_external_mcp_connector():
    """Verify external MCP client connector operates gracefully."""
    connector = ExternalMCPConnector()
    # Unconfigured returns None gracefully
    assert await connector.get_issue_context("SEC-101") is None
    assert await connector.get_branch_protection("org/repo", "main") is None

    # Configured returns structured context
    configured = ExternalMCPConnector(server_url="http://localhost:8080/mcp")
    ctx = await configured.get_issue_context("SEC-101")
    assert ctx is not None
    assert ctx["issue_key"] == "SEC-101"


def test_mcp_mounted_on_fastapi():
    """Verify /mcp sub-application is registered on the FastAPI app."""
    paths = []
    for r in app.routes:
        if hasattr(r, "path"):
            paths.append(r.path)
        elif hasattr(r, "prefix"):
            paths.append(r.prefix)
    assert any("/mcp" in p for p in paths)
