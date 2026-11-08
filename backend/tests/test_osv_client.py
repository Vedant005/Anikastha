from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.analyzer.osv_client import OSVClient
from app.schemas.dependency import Dependency


@pytest.mark.asyncio
async def test_osv_query_batch_with_mock():
    mock_osv_response = {
        "results": [
            {
                "vulns": [
                    {
                        "id": "GHSA-j8r2-6x86-q33q",
                        "summary": "Requests vulnerable to session fixation",
                        "details": "A session fixation flaw exists in requests...",
                        "aliases": ["CVE-2018-18074"],
                        "database_specific": {
                            "severity": "HIGH",
                        },
                        "affected": [
                            {
                                "package": {"name": "requests", "ecosystem": "PyPI"},
                                "ranges": [
                                    {
                                        "type": "ECOSYSTEM",
                                        "events": [
                                            {"introduced": "0"},
                                            {"fixed": "2.20.0"},
                                        ],
                                    }
                                ],
                            }
                        ],
                    }
                ]
            }
        ]
    }

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    post_resp = MagicMock()
    post_resp.json = lambda: mock_osv_response
    post_resp.raise_for_status = MagicMock()
    mock_client.post = AsyncMock(return_value=post_resp)

    osv_client = OSVClient(client=mock_client)
    deps = [
        Dependency(
            name="requests", version="2.19.1", ecosystem="PyPI", manifest_file="requirements.txt"
        )
    ]

    vulns = await osv_client.query_batch(deps, fetch_details=False)

    assert len(vulns) == 1
    v = vulns[0]
    assert v.id == "GHSA-j8r2-6x86-q33q"
    assert v.cve_id == "CVE-2018-18074"
    assert v.package_name == "requests"
    assert v.current_version == "2.19.1"
    assert v.fixed_version == "2.20.0"
    assert v.severity == "HIGH"
    assert v.cvss_score == 8.0
    assert "session fixation" in v.summary


@pytest.mark.asyncio
async def test_osv_query_batch_empty_results():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    post_resp = MagicMock()
    post_resp.json = lambda: {"results": [{}]}
    post_resp.raise_for_status = MagicMock()
    mock_client.post = AsyncMock(return_value=post_resp)

    osv_client = OSVClient(client=mock_client)
    deps = [
        Dependency(
            name="fastapi", version="0.115.0", ecosystem="PyPI", manifest_file="requirements.txt"
        )
    ]

    vulns = await osv_client.query_batch(deps, fetch_details=False)
    assert len(vulns) == 0


@pytest.mark.asyncio
async def test_osv_query_batch_no_version():
    osv_client = OSVClient()
    deps = [
        Dependency(name="fastapi", version="", ecosystem="PyPI", manifest_file="requirements.txt")
    ]
    # No version specified should skip OSV call
    vulns = await osv_client.query_batch(deps, fetch_details=False)
    assert len(vulns) == 0
