import logging
from typing import Any

import httpx

from app.schemas.dependency import Dependency, SeverityLevel, Vulnerability

logger = logging.getLogger("pr_sentinel.osv")

_vuln_detail_cache: dict[str, dict[str, Any]] = {}


class OSVClient:
    """
    Async client for OSV.dev vulnerability database.
    Queries batch advisories for PyPI and npm dependencies.
    """

    BASE_URL = "https://api.osv.dev/v1"

    def __init__(self, client: httpx.AsyncClient | None = None):
        self._external_client = client is not None
        self._client = client or httpx.AsyncClient(timeout=15.0)

    async def __aenter__(self) -> "OSVClient":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if not self._external_client:
            await self._client.aclose()

    async def query_batch(
        self,
        dependencies: list[Dependency],
        fetch_details: bool = True,
    ) -> list[Vulnerability]:
        """
        Query OSV.dev batch API for known vulnerabilities in the provided dependencies.
        """
        # Filter for dependencies with versions
        valid_deps = [d for d in dependencies if d.version]
        if not valid_deps:
            return []

        # OSV batch API accepts up to 500 queries per request; chunk into batches of 100
        chunk_size = 100
        all_vulnerabilities: list[Vulnerability] = []

        for i in range(0, len(valid_deps), chunk_size):
            chunk = valid_deps[i : i + chunk_size]
            queries = [
                {
                    "package": {
                        "name": dep.name,
                        "ecosystem": dep.ecosystem,
                    },
                    "version": dep.version,
                }
                for dep in chunk
            ]

            try:
                response = await self._client.post(
                    f"{self.BASE_URL}/querybatch",
                    json={"queries": queries},
                )
                response.raise_for_status()
                data = response.json()
                results = data.get("results", [])

                # Map results back to dependencies
                for dep, result in zip(chunk, results, strict=False):
                    vulns = result.get("vulns", [])
                    for vuln_data in vulns:
                        vuln_id = vuln_data.get("id", "")

                        # Optionally fetch full details if missing summary or aliases
                        detailed_data = vuln_data
                        if fetch_details and (
                            not vuln_data.get("aliases") or not vuln_data.get("summary")
                        ):
                            detailed_data = (
                                await self.get_vulnerability_details(vuln_id) or vuln_data
                            )

                        parsed_vuln = self._parse_vulnerability(dep, detailed_data)
                        if parsed_vuln:
                            all_vulnerabilities.append(parsed_vuln)

            except Exception as exc:
                logger.error("Error querying OSV.dev batch API: %s", exc)

        return all_vulnerabilities

    async def get_vulnerability_details(self, vuln_id: str) -> dict[str, Any] | None:
        """Fetch detailed advisory information for a specific vulnerability ID with caching."""
        if not vuln_id:
            return None

        if vuln_id in _vuln_detail_cache:
            return _vuln_detail_cache[vuln_id]

        try:
            response = await self._client.get(f"{self.BASE_URL}/vulns/{vuln_id}")
            if response.status_code == 200:
                data = response.json()
                _vuln_detail_cache[vuln_id] = data
                return data
        except Exception as exc:
            logger.debug("Failed to fetch detailed OSV advisory %s: %s", vuln_id, exc)

        return None

    def _parse_vulnerability(
        self,
        dep: Dependency,
        data: dict[str, Any],
    ) -> Vulnerability | None:
        vuln_id = data.get("id")
        if not vuln_id:
            return None

        # Extract CVE identifier from aliases
        aliases = data.get("aliases", []) or []
        cve_id = None
        for alias in aliases:
            if alias.startswith("CVE-"):
                cve_id = alias
                break

        # If vuln_id itself is a CVE
        if not cve_id and vuln_id.startswith("CVE-"):
            cve_id = vuln_id

        # Determine severity level and CVSS score
        severity, cvss_score = self._extract_severity(data)

        # Extract fixed version from affected ranges
        fixed_version = self._extract_fixed_version(dep.name, data)

        summary = data.get("summary") or f"Security advisory for {dep.name}"
        details = data.get("details")

        advisory_url = None
        for ref in data.get("references", []):
            if ref.get("type") in ("ADVISORY", "WEB"):
                advisory_url = ref.get("url")
                break
        if not advisory_url:
            advisory_url = f"https://osv.dev/vulnerability/{vuln_id}"

        return Vulnerability(
            id=vuln_id,
            cve_id=cve_id,
            package_name=dep.name,
            ecosystem=dep.ecosystem,
            current_version=dep.version,
            fixed_version=fixed_version,
            severity=severity,
            cvss_score=cvss_score,
            summary=summary,
            details=details,
            advisory_url=advisory_url,
        )

    @staticmethod
    def _extract_severity(data: dict[str, Any]) -> tuple[SeverityLevel, float | None]:
        # Check database_specific severity (GitHub/NVD advisory severity)
        db_specific = data.get("database_specific", {})
        raw_sev = db_specific.get("severity", "").upper() if isinstance(db_specific, dict) else ""

        if raw_sev == "CRITICAL":
            return "CRITICAL", 9.5
        elif raw_sev == "HIGH":
            return "HIGH", 8.0
        elif raw_sev in ("MODERATE", "MEDIUM"):
            return "MEDIUM", 5.5
        elif raw_sev == "LOW":
            return "LOW", 3.0

        # Check CVSS v3 score / vector in severity array
        cvss_score = None
        for sev_obj in data.get("severity", []):
            score_str = sev_obj.get("score", "")
            # If numeric string or vector
            if score_str.startswith("CVSS:3"):
                # Approximate severity from base metrics or assign default HIGH
                return "HIGH", 7.5

        return "MEDIUM", cvss_score

    @staticmethod
    def _extract_fixed_version(pkg_name: str, data: dict[str, Any]) -> str | None:
        for affected in data.get("affected", []):
            pkg = affected.get("package", {})
            if pkg.get("name", "").lower() == pkg_name.lower():
                for r in affected.get("ranges", []):
                    for event in r.get("events", []):
                        if "fixed" in event:
                            return str(event["fixed"])
        return None
