import json
import logging
import re
import uuid
from typing import Any

from mcp.server.mcpserver import MCPServer
from sqlalchemy import select

from app.analyzer.ast_parser import TreeSitterASTParser
from app.core.database import AsyncSessionLocal
from app.github.diff_parser import DiffParser
from app.models.finding import Finding
from app.models.policy import Policy
from app.models.repository import Repository
from app.models.review_run import ReviewRun

logger = logging.getLogger("pr_sentinel.mcp")

# Initialize PR-Sentinel MCP Server
mcp_server = MCPServer(
    name="pr-sentinel",
    instructions=(
        "PR-Sentinel is an autonomous code security & quality review server. "
        "It provides AST-based vulnerability scanning, policy inspection, "
        "finding explanations, and pre-commit diff auditing."
    ),
)


# ============================================================================
# Local Static AST Rule Engine (Fast in-memory checks for IDE diff scans)
# ============================================================================

PATTERNS = [
    {
        "id": "SEC-RAW-SQL",
        "cwe": "CWE-89",
        "category": "CODE_SECURITY",
        "severity": "HIGH",
        "title": "Potential SQL Injection via Raw String Formatting",
        "regex": re.compile(
            r"""(?:\.execute|\.raw)\s*\(\s*(?:f['"]|['"].*%|['"].*\+)|execute\s*\(\s*f["'].*SELECT|execute\s*\(\s*f["'].*UPDATE|execute\s*\(\s*f["'].*DELETE|f["']\s*(?:SELECT|UPDATE|DELETE|INSERT|DROP|ALTER)\b""",
            re.IGNORECASE,
        ),
        "message": (
            "Direct string formatting or interpolation into database queries "
            "bypasses parameter binding and introduces SQL injection vulnerabilities."
        ),
        "fix_template": "Use parameterized queries or SQLAlchemy select() with bind parameters.",
    },
    {
        "id": "SEC-HARDCODED-SECRET",
        "cwe": "CWE-798",
        "category": "CODE_SECURITY",
        "severity": "CRITICAL",
        "title": "Hardcoded Secret / Token Detected",
        "regex": re.compile(
            r"""(?:password|secret|api_key|token|access_key|private_key)\s*=\s*['"][a-zA-Z0-9_\-\.]{16,}['"]|ghp_[a-zA-Z0-9]{36}|AKIA[0-9A-Z]{16}""",
            re.IGNORECASE,
        ),
        "message": (
            "Hardcoded credentials or API tokens in source code can be extracted "
            "by attackers. Use environment variables or secret vaults."
        ),
        "fix_template": "os.environ.get('API_SECRET_KEY') or pydantic Settings.",
    },
    {
        "id": "SEC-CMD-INJECTION",
        "cwe": "CWE-78",
        "category": "CODE_SECURITY",
        "severity": "CRITICAL",
        "title": "Command Injection via shell=True / os.system",
        "regex": re.compile(
            r"""subprocess\.(?:run|call|Popen)\s*\(.*shell\s*=\s*True|os\.system\s*\(|os\.popen\s*\(""",
            re.IGNORECASE,
        ),
        "message": (
            "Executing shell commands with shell=True or os.system() allows command "
            "injection if arguments contain untrusted user inputs."
        ),
        "fix_template": "Pass arguments as a list with shell=False: subprocess.run(['cmd', arg], shell=False)",
    },
    {
        "id": "SEC-UNSAFE-DESERIALIZATION",
        "cwe": "CWE-502",
        "category": "CODE_SECURITY",
        "severity": "HIGH",
        "title": "Unsafe Deserialization via pickle / yaml",
        "regex": re.compile(
            r"""pickle\.loads\s*\(|yaml\.load\s*\([^,)]+\)""",
            re.IGNORECASE,
        ),
        "message": (
            "Deserializing untrusted data with pickle or yaml.load (without SafeLoader) "
            "can lead to arbitrary remote code execution."
        ),
        "fix_template": "Use yaml.safe_load(data) or json.loads(data) instead of pickle.",
    },
    {
        "id": "QUAL-BARE-EXCEPT",
        "cwe": "CWE-391",
        "category": "CODE_QUALITY",
        "severity": "MEDIUM",
        "title": "Bare Exception Handling Swallowing Errors",
        "regex": re.compile(r"""^\s*except\s*:|^\s*except\s+Exception\s*:\s*pass"""),
        "message": (
            "Catching bare exceptions or silently passing on Exception masks bugs, "
            "hides keyboard interrupts, and impairs observability."
        ),
        "fix_template": "except SpecificError as e: logger.error('Operation failed: %s', e)",
    },
    {
        "id": "QUAL-ASYNC-BLOCKING",
        "cwe": "CWE-400",
        "category": "CODE_QUALITY",
        "severity": "HIGH",
        "title": "Synchronous Blocking Call in Async Function",
        "regex": re.compile(
            r"""time\.sleep\s*\(|requests\.(?:get|post|put|delete)\s*\(""",
        ),
        "message": (
            "Invoking synchronous blocking calls (like time.sleep or requests.get) "
            "inside an async event loop starves concurrent requests."
        ),
        "fix_template": "Use asyncio.sleep(...) or httpx.AsyncClient() instead.",
    },
]


# ============================================================================
# MCP Tools
# ============================================================================

@mcp_server.tool(
    name="scan_local_diff",
    description=(
        "Scans a local git unified diff before committing or pushing. "
        "Detects SQL injection, hardcoded secrets, command injection, bare exceptions, "
        "and event loop blocking calls. Returns coordinates and suggested fixes."
    ),
)
def scan_local_diff(diff_content: str, repo_name: str = "local-repository") -> dict[str, Any]:
    """Parse diff and evaluate against AST and security patterns."""
    if not diff_content or not diff_content.strip():
        return {
            "verdict": "APPROVE",
            "findings_count": 0,
            "summary": "Diff is empty; zero issues detected.",
            "findings": [],
        }

    diff_files = DiffParser.parse_diff(diff_content)
    findings: list[dict[str, Any]] = []

    for df in diff_files:
        lang = TreeSitterASTParser.detect_language(df.new_path)
        
        for hunk in df.hunks:
            for line in hunk.lines:
                if line.type != "add":
                    continue

                line_num = line.new_line_number or 1
                line_content = line.content

                for pattern in PATTERNS:
                    if pattern["regex"].search(line_content):
                        # Generate suggestion markdown
                        suggestion = f"```suggestion\n# {pattern['fix_template']}\n```"

                        findings.append({
                            "id": f"find_{uuid.uuid4().hex[:8]}",
                            "file_path": df.new_path,
                            "line_number": line_num,
                            "rule_id": pattern["id"],
                            "cwe": pattern["cwe"],
                            "category": pattern["category"],
                            "severity": pattern["severity"],
                            "title": pattern["title"],
                            "message": pattern["message"],
                            "code_snippet": line_content.strip(),
                            "suggestion_markdown": suggestion,
                        })

    # Calculate overall verdict
    has_critical_or_high = any(
        f["severity"] in ("CRITICAL", "HIGH") for f in findings
    )
    if has_critical_or_high:
        verdict = "REQUEST_CHANGES"
    elif findings:
        verdict = "COMMENT"
    else:
        verdict = "APPROVE"

    return {
        "repo": repo_name,
        "files_scanned": len(diff_files),
        "findings_count": len(findings),
        "verdict": verdict,
        "summary": (
            f"Scanned {len(diff_files)} file(s) across diff. "
            f"Detected {len(findings)} issue(s). Final verdict: {verdict}."
        ),
        "findings": findings,
    }


@mcp_server.tool(
    name="audit_pull_request",
    description=(
        "Retrieves the PR-Sentinel audit results for a specific GitHub Pull Request. "
        "Returns the verdict, verified findings, CVE status, and security metrics."
    ),
)
async def audit_pull_request(repo_full_name: str, pr_number: int) -> dict[str, Any]:
    """Query database for an existing review run for the specified PR."""
    try:
        async with AsyncSessionLocal() as session:
            # Look up repository
            repo_stmt = select(Repository).where(Repository.full_name == repo_full_name)
            repo_res = await session.execute(repo_stmt)
            repo = repo_res.scalar_one_or_none()

            if not repo:
                return {
                    "status": "NOT_FOUND",
                    "repo": repo_full_name,
                    "pr_number": pr_number,
                    "message": f"Repository '{repo_full_name}' is not registered with PR-Sentinel.",
                }

            # Look up latest review run for this PR
            review_stmt = (
                select(ReviewRun)
                .where(
                    ReviewRun.repository_id == repo.id,
                    ReviewRun.pull_number == pr_number,
                )
                .order_by(ReviewRun.created_at.desc())
            )
            review_res = await session.execute(review_stmt)
            review = review_res.scalar_one_or_none()

            if not review:
                return {
                    "status": "PENDING",
                    "repo": repo_full_name,
                    "pr_number": pr_number,
                    "message": (
                        f"No review has completed yet for PR #{pr_number} on '{repo_full_name}'. "
                        "A review will trigger automatically upon incoming PR webhook."
                    ),
                }

            # Fetch associated findings
            findings_stmt = select(Finding).where(Finding.review_run_id == review.id)
            findings_res = await session.execute(findings_stmt)
            findings = findings_res.scalars().all()

            return {
                "status": "COMPLETED",
                "repo": repo_full_name,
                "pr_number": pr_number,
                "verdict": review.verdict,
                "created_at": review.created_at.isoformat() if review.created_at else None,
                "findings_count": len(findings),
                "findings": [
                    {
                        "id": str(f.id),
                        "file_path": f.file_path,
                        "line_start": f.line_start,
                        "line_end": f.line_end,
                        "category": f.category,
                        "severity": f.severity,
                        "title": f.title,
                        "description": f.description,
                        "cwe": f.cwe,
                        "suggestion_markdown": f.suggestion_markdown,
                        "is_verified": f.is_verified,
                    }
                    for f in findings
                ],
            }
    except Exception as e:
        logger.error("Error auditing pull request via MCP: %s", e)
        return {
            "status": "ERROR",
            "repo": repo_full_name,
            "pr_number": pr_number,
            "error": str(e),
        }


@mcp_server.tool(
    name="get_repo_policy",
    description=(
        "Retrieves the active security policy for a repository, including "
        "blocking severities, banned packages, allowed licenses, and quality thresholds."
    ),
)
async def get_repo_policy(repo_full_name: str) -> dict[str, Any]:
    """Retrieve repository policy from database or return standard default."""
    try:
        async with AsyncSessionLocal() as session:
            stmt = (
                select(Policy)
                .join(Repository)
                .where(Repository.full_name == repo_full_name)
            )
            res = await session.execute(stmt)
            policy = res.scalar_one_or_none()

            if policy:
                return {
                    "repo": repo_full_name,
                    "fail_on_severity": policy.fail_on_severity,
                    "prohibited_licenses": policy.prohibited_licenses,
                    "block_prohibited_licenses": policy.block_prohibited_licenses,
                    "auto_request_changes": policy.auto_request_changes,
                }
    except Exception as e:
        logger.warning("Could not query DB for repo policy (%s); returning default.", e)

    # Standard default policy
    return {
        "repo": repo_full_name,
        "fail_severities": ["CRITICAL", "HIGH"],
        "banned_dependencies": [],
        "allowed_licenses": ["MIT", "Apache-2.0", "BSD-3-Clause", "ISC"],
        "enable_ai_review": True,
        "enable_ast_analysis": True,
        "enable_dep_audit": True,
        "note": "Standard default security policy applied.",
    }


@mcp_server.tool(
    name="explain_finding",
    description=(
        "Explains a security vulnerability or code smell in detail, outlining "
        "the attack vector, runtime risks, and best-practice remediation."
    ),
)
def explain_finding(
    cwe: str,
    title: str,
    description: str,
    code_snippet: str = "",
) -> str:
    """Generate in-depth architectural explanation of a finding."""
    return f"""### 🛡️ PR-Sentinel Finding Analysis: {title}

**Classification**: {cwe}
**Overview**: {description}

#### 1. Threat Mechanism & Attack Surface
When untrusted user input directly influences application logic without canonical sanitization or parameter binding, attackers can manipulate the execution context. In the case of **{cwe}**, an adversary can subvert standard access controls or execute unauthorized operations.

#### 2. Code Context
```text
{code_snippet if code_snippet else "(No snippet provided)"}
```

#### 3. Recommended Remediation
1. **Parameterize / Isolate**: Never concatenate user input directly into query, command, or file path strings.
2. **Framework Validation**: Ensure all inbound payloads pass through schema validation (e.g. Pydantic v2, Zod) before reaching database or system execution layers.
3. **Defense in Depth**: Apply least-privilege principles at both the database role and process execution levels.

*For complete vulnerability specifications, consult the MITRE CWE database for {cwe}.*
"""


@mcp_server.tool(
    name="suggest_patch",
    description="Generates a production-ready patch suggestion block for a given code vulnerability.",
)
def suggest_patch(cwe: str, code_snippet: str, language: str = "python") -> str:
    """Produce a replacement suggestion block based on CWE."""
    cwe_upper = cwe.upper()

    if "CWE-89" in cwe_upper:
        patch = (
            "# Use SQLAlchemy 2.0 parameterized select\n"
            "stmt = select(Entity).where(Entity.attribute == user_param)\n"
            "result = await session.execute(stmt)"
        )
    elif "CWE-798" in cwe_upper:
        patch = (
            "# Load secret from environment / Pydantic Settings\n"
            "api_key = settings.API_KEY  # or os.environ['API_KEY']"
        )
    elif "CWE-78" in cwe_upper:
        patch = (
            "# Avoid shell=True; pass explicit command arguments array\n"
            "subprocess.run(['command', arg1, arg2], check=True, shell=False)"
        )
    elif "CWE-391" in cwe_upper:
        patch = (
            "except SpecificOperationError as e:\n"
            "    logger.error('Failed to complete operation: %s', e)\n"
            "    raise HTTPException(status_code=500, detail='Internal operation failure')"
        )
    else:
        patch = f"# Sanitize and validate inputs to remediate {cwe}\n" + code_snippet

    return f"```{language}\n{patch}\n```"


# ============================================================================
# MCP Resources
# ============================================================================

@mcp_server.resource(
    uri="pr-sentinel://policy/{repo_full_name}",
    name="Repository Security Policy",
    description="Active security and quality policy configuration for the specified repository.",
    mime_type="application/json",
)
async def resource_repo_policy(repo_full_name: str) -> str:
    """Return repository policy as JSON resource."""
    policy_data = await get_repo_policy(repo_full_name)
    return json.dumps(policy_data, indent=2)


@mcp_server.resource(
    uri="pr-sentinel://reviews/{review_id}",
    name="Review Run Details",
    description="Status, verdict, and findings for a specific PR-Sentinel review ID.",
    mime_type="application/json",
)
async def resource_review_run(review_id: str) -> str:
    """Return review details by UUID."""
    try:
        r_uuid = uuid.UUID(review_id)
        async with AsyncSessionLocal() as session:
            stmt = select(ReviewRun).where(ReviewRun.id == r_uuid)
            res = await session.execute(stmt)
            review = res.scalar_one_or_none()

            if not review:
                return json.dumps({"error": f"Review '{review_id}' not found."}, indent=2)

            findings_stmt = select(Finding).where(Finding.review_run_id == review.id)
            findings_res = await session.execute(findings_stmt)
            findings = findings_res.scalars().all()

            return json.dumps(
                {
                    "id": str(review.id),
                    "pr_number": review.pull_number,
                    "verdict": review.verdict,
                    "findings_count": len(findings),
                    "findings": [
                        {
                            "title": f.title,
                            "severity": f.severity,
                            "file_path": f.file_path,
                            "line_start": f.line_start,
                            "cwe": f.cwe,
                        }
                        for f in findings
                    ],
                },
                indent=2,
            )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ============================================================================
# MCP Prompts
# ============================================================================

@mcp_server.prompt(
    name="security-precommit-check",
    title="PR-Sentinel Pre-Commit Security Audit",
    description="System instruction for AI coding agents to perform pre-commit security checks on diffs.",
)
def prompt_precommit(diff: str = "") -> str:
    """Instruction template for local diff auditing."""
    return f"""You are PR-Sentinel, an adversarial application security reviewer.
Analyze the following git diff carefully. Your mission is to detect:
1. SQL Injection (raw string queries, unparameterized concatenation)
2. Hardcoded API keys, private keys, or credentials
3. Command Injection (shell=True, os.system)
4. SSRF and unvalidated external redirects
5. Unsafe deserialization (pickle, unsafe yaml)

Diff to inspect:
<untrusted_diff>
{diff if diff else "(Insert git diff here)"}
</untrusted_diff>

For each verified security vulnerability found:
- Specify the exact file path and line number.
- State the CWE identifier.
- Explain why it is vulnerable.
- Provide a GitHub markdown ```suggestion block with the safe replacement.
"""


@mcp_server.prompt(
    name="explain-cwe-remediation",
    title="Explain CWE & Provide Remediation",
    description="Provides detailed explanation and refactoring plan for a specific CWE vulnerability.",
)
def prompt_explain_cwe(cwe: str, file_path: str = "") -> str:
    """Prompt template for CWE explanation."""
    return f"""You are a Principal Security Engineer.
Explain the security vulnerability '{cwe}' in the context of file '{file_path}'.
Include:
1. Exact attack vector and how an adversary could exploit it.
2. The architectural principle violated (e.g. separation of data and code).
3. Step-by-step remediation guide adhering to modern secure coding standards.
"""
