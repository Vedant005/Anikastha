from typing import Literal

from pydantic import BaseModel, Field

Ecosystem = Literal["PyPI", "npm"]
SeverityLevel = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
LicenseCategory = Literal[
    "PERMISSIVE", "WEAK_COPYLEFT", "STRONG_COPYLEFT", "PROPRIETARY", "UNKNOWN"
]


class Dependency(BaseModel):
    name: str
    version: str
    ecosystem: Ecosystem
    manifest_file: str
    is_dev: bool = False


class Vulnerability(BaseModel):
    id: str  # GHSA-xxx or OSV ID
    cve_id: str | None = None
    package_name: str
    ecosystem: Ecosystem
    current_version: str
    fixed_version: str | None = None
    severity: SeverityLevel
    cvss_score: float | None = None
    summary: str
    details: str | None = None
    advisory_url: str | None = None


class LicenseCheckResult(BaseModel):
    package_name: str
    ecosystem: Ecosystem
    license_spdx: str
    category: LicenseCategory
    is_prohibited: bool
    policy_reason: str | None = None


class DependencyAuditReport(BaseModel):
    dependencies_scanned: int = 0
    vulnerabilities: list[Vulnerability] = Field(default_factory=list)
    license_alerts: list[LicenseCheckResult] = Field(default_factory=list)
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
