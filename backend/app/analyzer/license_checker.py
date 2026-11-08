import logging
from typing import Any

import httpx

from app.schemas.dependency import Dependency, LicenseCategory, LicenseCheckResult

logger = logging.getLogger("pr_sentinel.license")

# Standard license classifications
PERMISSIVE_LICENSES = {
    "MIT",
    "APACHE-2.0",
    "BSD-2-CLAUSE",
    "BSD-3-CLAUSE",
    "ISC",
    "UNLICENSE",
    "CC0-1.0",
    "ZLIB",
    "PYTHON-2.0",
    "POSTGRESQL",
    "0BSD",
}

WEAK_COPYLEFT_LICENSES = {
    "LGPL-2.0",
    "LGPL-2.1",
    "LGPL-3.0",
    "MPL-1.1",
    "MPL-2.0",
    "EPL-1.0",
    "EPL-2.0",
    "CDDL-1.0",
}

STRONG_COPYLEFT_LICENSES = {
    "GPL-2.0",
    "GPL-3.0",
    "AGPL-3.0",
    "SSPL-1.0",
    "EUPL-1.1",
    "EUPL-1.2",
    "OSL-3.0",
}

_license_cache: dict[str, str] = {}


class LicenseChecker:
    """
    Resolves package SPDX licenses and validates against organizational compliance policies.
    """

    def __init__(self, client: httpx.AsyncClient | None = None):
        self._external_client = client is not None
        self._client = client or httpx.AsyncClient(timeout=10.0)

    async def __aenter__(self) -> "LicenseChecker":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if not self._external_client:
            await self._client.aclose()

    async def check_dependencies(
        self,
        dependencies: list[Dependency],
        prohibited_licenses: list[str],
    ) -> list[LicenseCheckResult]:
        """
        Check license for each dependency and verify against prohibited license rules.
        """
        results: list[LicenseCheckResult] = []
        normalized_prohibited = {lic.upper().strip() for lic in prohibited_licenses}

        for dep in dependencies:
            license_spdx = await self.resolve_package_license(dep)
            category = self.categorize_license(license_spdx)

            is_prohibited = False
            policy_reason = None

            norm_lic = license_spdx.upper().strip()
            # Check direct match
            if norm_lic in normalized_prohibited:
                is_prohibited = True
                policy_reason = f"License '{license_spdx}' is explicitly prohibited by policy."
            # Check strong copyleft block
            elif "GPL" in norm_lic and any("GPL" in p for p in normalized_prohibited):
                is_prohibited = True
                policy_reason = (
                    f"Copyleft license '{license_spdx}' matches prohibited license rule."
                )

            results.append(
                LicenseCheckResult(
                    package_name=dep.name,
                    ecosystem=dep.ecosystem,
                    license_spdx=license_spdx,
                    category=category,
                    is_prohibited=is_prohibited,
                    policy_reason=policy_reason,
                )
            )

        return results

    async def resolve_package_license(self, dep: Dependency) -> str:
        """Fetch package license from registry metadata or cache."""
        cache_key = f"{dep.ecosystem}:{dep.name.lower()}"
        if cache_key in _license_cache:
            return _license_cache[cache_key]

        license_str = "UNKNOWN"
        try:
            if dep.ecosystem == "PyPI":
                license_str = await self._fetch_pypi_license(dep.name)
            elif dep.ecosystem == "npm":
                license_str = await self._fetch_npm_license(dep.name)
        except Exception as exc:
            logger.debug("Could not resolve license for %s: %s", dep.name, exc)

        cleaned_license = self._normalize_spdx(license_str)
        _license_cache[cache_key] = cleaned_license
        return cleaned_license

    async def _fetch_pypi_license(self, pkg_name: str) -> str:
        url = f"https://pypi.org/pypi/{pkg_name}/json"
        response = await self._client.get(url)
        if response.status_code == 200:
            data = response.json()
            info = data.get("info", {})

            # Check license expression or license field
            if info.get("license"):
                return info["license"]

            # Check classifiers
            for classifier in info.get("classifiers", []):
                if classifier.startswith("License :: OSI Approved ::"):
                    return classifier.split("::")[-1].strip()

        return "UNKNOWN"

    async def _fetch_npm_license(self, pkg_name: str) -> str:
        url = f"https://registry.npmjs.org/{pkg_name}"
        response = await self._client.get(url)
        if response.status_code == 200:
            data = response.json()
            lic = data.get("license")
            if isinstance(lic, str):
                return lic
            elif isinstance(lic, dict) and "type" in lic:
                return lic["type"]
        return "UNKNOWN"

    @classmethod
    def categorize_license(cls, license_spdx: str) -> LicenseCategory:
        norm = license_spdx.upper().strip()
        if norm in PERMISSIVE_LICENSES or any(p in norm for p in ("MIT", "APACHE", "BSD", "ISC")):
            return "PERMISSIVE"
        elif norm in WEAK_COPYLEFT_LICENSES or "LGPL" in norm or "MPL" in norm:
            return "WEAK_COPYLEFT"
        elif (
            norm in STRONG_COPYLEFT_LICENSES or "AGPL" in norm or "GPL-3" in norm or "GPL-2" in norm
        ):
            return "STRONG_COPYLEFT"
        elif norm == "UNKNOWN" or not norm:
            return "UNKNOWN"
        return "PROPRIETARY"

    @classmethod
    def _normalize_spdx(cls, raw_license: str) -> str:
        if not raw_license or raw_license.strip() in ("", "UNKNOWN", "UNKNOWN LICENSE"):
            return "UNKNOWN"

        clean = raw_license.strip().strip("()")
        upper = clean.upper()

        if "MIT" in upper:
            return "MIT"
        elif "APACHE 2" in upper or "APACHE-2" in upper or "APACHE SOFTWARE LICENSE" in upper:
            return "Apache-2.0"
        elif "BSD 3" in upper or "BSD-3" in upper:
            return "BSD-3-Clause"
        elif "BSD 2" in upper or "BSD-2" in upper:
            return "BSD-2-Clause"
        elif "AGPL-3" in upper or "AGPL 3" in upper:
            return "AGPL-3.0"
        elif "GPL-3" in upper or "GPL 3" in upper or "GNU GENERAL PUBLIC LICENSE V3" in upper:
            return "GPL-3.0"
        elif "GPL-2" in upper or "GPL 2" in upper:
            return "GPL-2.0"
        elif "LGPL-3" in upper:
            return "LGPL-3.0"
        elif "LGPL-2" in upper:
            return "LGPL-2.1"
        elif "MPL-2" in upper:
            return "MPL-2.0"
        elif "ISC" in upper:
            return "ISC"

        return clean
