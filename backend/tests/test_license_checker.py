from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.analyzer.license_checker import LicenseChecker
from app.schemas.dependency import Dependency


def test_categorize_license():
    assert LicenseChecker.categorize_license("MIT") == "PERMISSIVE"
    assert LicenseChecker.categorize_license("Apache-2.0") == "PERMISSIVE"
    assert LicenseChecker.categorize_license("BSD-3-Clause") == "PERMISSIVE"

    assert LicenseChecker.categorize_license("GPL-3.0") == "STRONG_COPYLEFT"
    assert LicenseChecker.categorize_license("AGPL-3.0") == "STRONG_COPYLEFT"
    assert LicenseChecker.categorize_license("SSPL-1.0") == "STRONG_COPYLEFT"

    assert LicenseChecker.categorize_license("LGPL-3.0") == "WEAK_COPYLEFT"
    assert LicenseChecker.categorize_license("MPL-2.0") == "WEAK_COPYLEFT"

    assert LicenseChecker.categorize_license("UNKNOWN") == "UNKNOWN"
    assert LicenseChecker.categorize_license("Custom Commercial") == "PROPRIETARY"


@pytest.mark.asyncio
async def test_license_checker_prohibited_rules():
    mock_client = AsyncMock(spec=httpx.AsyncClient)

    # Mock PyPI responses
    async def mock_get(url):
        resp = MagicMock()
        resp.status_code = 200
        if "fastapi" in url:
            resp.json = lambda: {"info": {"license": "MIT"}}
        elif "copyleft-pkg" in url:
            resp.json = lambda: {"info": {"license": "GPL-3.0-only"}}
        elif "agpl-tool" in url:
            resp.json = lambda: {"info": {"license": "AGPL-3.0"}}
        else:
            resp.status_code = 404
            resp.json = lambda: {}
        return resp

    mock_client.get = AsyncMock(side_effect=mock_get)
    checker = LicenseChecker(client=mock_client)

    deps = [
        Dependency(
            name="fastapi", version="0.115.0", ecosystem="PyPI", manifest_file="requirements.txt"
        ),
        Dependency(
            name="copyleft-pkg", version="1.0.0", ecosystem="PyPI", manifest_file="requirements.txt"
        ),
        Dependency(
            name="agpl-tool", version="2.0.0", ecosystem="PyPI", manifest_file="requirements.txt"
        ),
    ]

    prohibited = ["GPL-3.0", "AGPL-3.0"]
    results = await checker.check_dependencies(deps, prohibited_licenses=prohibited)

    res_map = {r.package_name: r for r in results}

    assert res_map["fastapi"].is_prohibited is False
    assert res_map["fastapi"].category == "PERMISSIVE"

    assert res_map["copyleft-pkg"].is_prohibited is True
    assert res_map["copyleft-pkg"].category == "STRONG_COPYLEFT"
    assert "prohibited" in (res_map["copyleft-pkg"].policy_reason or "").lower()

    assert res_map["agpl-tool"].is_prohibited is True
    assert res_map["agpl-tool"].category == "STRONG_COPYLEFT"
