# PR-Sentinel Model Context Protocol (MCP) Setup Guide

PR-Sentinel provides a native Model Context Protocol (MCP) server that empowers AI coding assistants in your favorite IDE or terminal to inspect review findings, audit pre-commit diffs, and query security policies.

---

## 1. Supported IDEs & Client Setups

### Cursor
Add to your project's `.cursor/mcp.json` or your global Cursor settings:
```json
{
  "mcpServers": {
    "pr-sentinel": {
      "command": "python",
      "args": ["-m", "app.mcp", "--transport", "stdio"],
      "cwd": "${workspaceFolder}/backend",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/backend"
      }
    }
  }
}
```

### Claude Desktop
Add to `%APPDATA%\Claude\claude_desktop_config.json` (Windows) or `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):
```json
{
  "mcpServers": {
    "pr-sentinel": {
      "command": "python",
      "args": ["-m", "app.mcp", "--transport", "stdio"],
      "cwd": "/path/to/PrSentinel/backend",
      "env": {
        "PYTHONPATH": "/path/to/PrSentinel/backend"
      }
    }
  }
}
```

### Windsurf / Cascade (Codeium)
Add to `~/.codeium/windsurf/mcp_config.json`:
```json
{
  "mcpServers": {
    "pr-sentinel": {
      "command": "python",
      "args": ["-m", "app.mcp", "--transport", "stdio"],
      "cwd": "${workspaceRoot}/backend",
      "env": {
        "PYTHONPATH": "${workspaceRoot}/backend"
      }
    }
  }
}
```

### VS Code (Cline / Continue)
Add to Cline settings (`cline_mcp_settings.json`):
```json
{
  "mcpServers": {
    "pr-sentinel": {
      "command": "python",
      "args": ["-m", "app.mcp", "--transport", "stdio"],
      "cwd": "${workspaceFolder}/backend",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/backend"
      }
    }
  }
}
```

### JetBrains IDEs (IntelliJ, PyCharm, WebStorm)
Use the JetBrains Model Context Protocol plugin or `mcp-proxy` pointing to:
- **stdio**: `python -m app.mcp` inside the `backend` folder.
- **SSE (HTTP)**: Start PR-Sentinel (`uvicorn app.main:app --port 8000`) and point the JetBrains SSE endpoint to `http://localhost:8000/mcp/sse`.

---

## 2. Available MCP Tools

| Tool | Parameters | Description |
| :--- | :--- | :--- |
| `scan_local_diff` | `diff_content`, `repo_name` | Scans unstaged/staged git diffs before pushing. Returns findings & suggestions. |
| `audit_pull_request` | `repo_full_name`, `pr_number` | Fetches PR review verdict, verified findings, and metrics from PR-Sentinel. |
| `get_repo_policy` | `repo_full_name` | Retrieves active blocking severities, banned packages, and allowed licenses. |
| `explain_finding` | `cwe`, `title`, `description`, `code_snippet` | Deep architectural explanation and exploit vector breakdown. |
| `suggest_patch` | `cwe`, `code_snippet`, `language` | Returns production-ready GitHub suggestion block. |

---

## 3. Available MCP Resources & Prompts

### Resources
- `pr-sentinel://policy/{repo_full_name}`: Live JSON payload of repository security and compliance policy.
- `pr-sentinel://reviews/{review_id}`: Live JSON payload of review results and verified findings.

### Prompts
- `security-precommit-check`: Pre-commit adversarial security inspection template.
- `explain-cwe-remediation`: Deep CWE breakdown and fix instruction template.
