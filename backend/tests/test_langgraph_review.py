import pytest

from app.review_engine.graph import review_engine_graph
from app.review_engine.nodes.synthesizer import synthesizer_node
from app.review_engine.nodes.verdict import verdict_node
from app.review_engine.nodes.verifier import verifier_node
from app.review_engine.state import RawFinding, ReviewState, VerifiedFinding


@pytest.mark.asyncio
async def test_synthesizer_deduplication():
    f1 = RawFinding(
        category="CODE_SECURITY",
        severity="MEDIUM",
        title="SQL Injection",
        description="Possible sql injection",
        file_path="app/db.py",
        line_start=15,
        line_end=15,
    )
    # Duplicate with higher severity
    f2 = RawFinding(
        category="CODE_SECURITY",
        severity="HIGH",
        title="SQL Injection",
        description="Confirmed sql injection",
        file_path="app/db.py",
        line_start=15,
        line_end=15,
    )
    f3 = RawFinding(
        category="DEPENDENCY_CVE",
        severity="CRITICAL",
        title="Vulnerable requests",
        description="CVE-2018-18074",
        file_path="requirements.txt",
        cve_id="CVE-2018-18074",
    )

    state: ReviewState = {
        "repo_name": "test/repo",
        "pull_number": 1,
        "commit_sha": "abc",
        "diff_files": [],
        "file_contexts": [],
        "dependencies": [],
        "vulnerabilities": [],
        "license_alerts": [],
        "policy": {},
        "raw_findings": [f1, f2, f3],
        "synthesized_findings": [],
        "verified_findings": [],
        "verdict": "",
        "summary_markdown": "",
    }

    result = await synthesizer_node(state)
    synth = result["synthesized_findings"]

    # f1 and f2 should be merged into 1 finding with HIGH severity
    assert len(synth) == 2
    sql_findings = [f for f in synth if f.title == "SQL Injection"]
    assert len(sql_findings) == 1
    assert sql_findings[0].severity == "HIGH"


@pytest.mark.asyncio
async def test_verifier_coordinate_gate():
    f_in_hunk = RawFinding(
        category="CODE_SECURITY",
        severity="HIGH",
        title="Command Injection",
        description="os.system call",
        file_path="app/main.py",
        line_start=12,
        line_end=12,
    )
    f_out_of_hunk = RawFinding(
        category="CODE_SECURITY",
        severity="MEDIUM",
        title="Hardcoded Password",
        description="Pre-existing password",
        file_path="app/main.py",
        line_start=99,  # line not in diff hunk
        line_end=99,
    )

    diff_files = [
        {
            "new_path": "app/main.py",
            "hunks": [
                {
                    "valid_new_lines": [10, 11, 12, 13],
                }
            ],
        }
    ]

    state: ReviewState = {
        "repo_name": "test/repo",
        "pull_number": 1,
        "commit_sha": "abc",
        "diff_files": diff_files,
        "file_contexts": [],
        "dependencies": [],
        "vulnerabilities": [],
        "license_alerts": [],
        "policy": {},
        "raw_findings": [],
        "synthesized_findings": [f_in_hunk, f_out_of_hunk],
        "verified_findings": [],
        "verdict": "",
        "summary_markdown": "",
    }

    result = await verifier_node(state)
    verified = result["verified_findings"]

    assert len(verified) == 2
    vf_map = {vf.title: vf for vf in verified}

    # In-hunk finding is approved for inline publishing
    assert vf_map["Command Injection"].is_in_diff_hunk is True

    # Out-of-hunk finding is preserved for summary but marked false for inline publishing
    assert vf_map["Hardcoded Password"].is_in_diff_hunk is False


@pytest.mark.asyncio
async def test_verdict_calculation():
    # 1. Clean PR -> APPROVE
    state_clean: ReviewState = {
        "repo_name": "org/clean-pr",
        "pull_number": 42,
        "commit_sha": "sha",
        "diff_files": [],
        "file_contexts": [],
        "dependencies": [],
        "vulnerabilities": [],
        "license_alerts": [],
        "policy": {"fail_on_severity": "HIGH", "auto_request_changes": True},
        "raw_findings": [],
        "synthesized_findings": [],
        "verified_findings": [],
        "verdict": "",
        "summary_markdown": "",
    }
    res_clean = await verdict_node(state_clean)
    assert res_clean["verdict"] == "APPROVE"
    assert "No security vulnerabilities" in res_clean["summary_markdown"]

    # 2. Critical / High finding -> REQUEST_CHANGES
    vf_high = VerifiedFinding(
        category="CODE_SECURITY",
        severity="HIGH",
        title="Path Traversal",
        description="Path traversal in file reader",
        file_path="app/reader.py",
        line_start=15,
        is_verified=True,
    )
    state_high: ReviewState = {
        **state_clean,
        "verified_findings": [vf_high],
    }
    res_high = await verdict_node(state_high)
    assert res_high["verdict"] == "REQUEST_CHANGES"
    assert "Changes Requested" in res_high["summary_markdown"]

    # 3. Policy with auto_request_changes=False -> COMMENT
    state_advisory: ReviewState = {
        **state_clean,
        "policy": {"fail_on_severity": "HIGH", "auto_request_changes": False},
        "verified_findings": [vf_high],
    }
    res_adv = await verdict_node(state_advisory)
    assert res_adv["verdict"] == "COMMENT"

    # 4. Prohibited license -> REQUEST_CHANGES
    vf_license = VerifiedFinding(
        category="LICENSE",
        severity="HIGH",
        title="Prohibited AGPL-3.0",
        description="Copyleft license",
        file_path="package.json",
        is_verified=True,
    )
    state_lic: ReviewState = {
        **state_clean,
        "policy": {
            "fail_on_severity": "CRITICAL",
            "block_prohibited_licenses": True,
            "auto_request_changes": True,
        },
        "verified_findings": [vf_license],
    }
    res_lic = await verdict_node(state_lic)
    assert res_lic["verdict"] == "REQUEST_CHANGES"


@pytest.mark.asyncio
async def test_full_review_engine_graph_execution():
    """End-to-end execution of compiled LangGraph with initial clean state."""
    initial_state: ReviewState = {
        "repo_name": "acme/web-app",
        "pull_number": 10,
        "commit_sha": "testsha",
        "diff_files": [],
        "file_contexts": [],
        "dependencies": [],
        "vulnerabilities": [],
        "license_alerts": [],
        "policy": {"fail_on_severity": "HIGH", "auto_request_changes": True},
        "raw_findings": [],
        "synthesized_findings": [],
        "verified_findings": [],
        "verdict": "",
        "summary_markdown": "",
    }

    final_state = await review_engine_graph.ainvoke(initial_state)

    assert final_state["verdict"] == "APPROVE"
    assert len(final_state["verified_findings"]) == 0
    assert "PR-Sentinel Security Review" in final_state["summary_markdown"]
