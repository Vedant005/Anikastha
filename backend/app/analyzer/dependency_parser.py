import json
import os
import re
import tomllib

from app.schemas.dependency import Dependency

# Regex to parse Python package specification (PEP 508 subset)
# e.g.: requests==2.31.0, urllib3>=1.26.5,<2.0.0; python_version >= '3.8'
PY_REQUIREMENT_REGEX = re.compile(
    r"^([a-zA-Z0-9_\-\.]+)(?:\[.*?\])?\s*([=><~^!]+)?\s*([0-9a-zA-Z\.\-\*]*)"
)


class DependencyParser:
    """
    Parses project manifest files to discover Python (PyPI) and TypeScript/JavaScript (npm) dependencies.
    """

    MANIFEST_PATTERNS = {
        "requirements.txt": "PyPI",
        "pyproject.toml": "PyPI",
        "package.json": "npm",
    }

    @classmethod
    def is_manifest_file(cls, file_path: str) -> bool:
        """Check if a file path matches a supported dependency manifest."""
        clean_path = file_path.lower().replace("\\", "/")
        base_name = os.path.basename(clean_path)
        if base_name in cls.MANIFEST_PATTERNS:
            return True
        # Match requirements/*.txt or requirements-dev.txt
        return bool(
            base_name.endswith(".txt")
            and ("requirement" in base_name or "requirements/" in clean_path)
        )

    @classmethod
    def parse_manifest(cls, file_path: str, content: str) -> list[Dependency]:
        """Parse dependency manifest content based on its filename."""
        base_name = os.path.basename(file_path.lower())
        if not content or not content.strip():
            return []

        if base_name in ("requirements.txt",) or (
            base_name.endswith(".txt") and "requirement" in base_name
        ):
            return cls._parse_requirements_txt(file_path, content)
        elif base_name == "pyproject.toml":
            return cls._parse_pyproject_toml(file_path, content)
        elif base_name == "package.json":
            return cls._parse_package_json(file_path, content)

        return []

    @classmethod
    def extract_changed_dependencies(
        cls,
        file_path: str,
        old_content: str | None,
        new_content: str | None,
    ) -> list[Dependency]:
        """
        Compare old manifest content with new manifest content to identify
        dependencies that were newly added or had their version changed.
        """
        old_deps = {d.name.lower(): d for d in cls.parse_manifest(file_path, old_content or "")}
        new_deps = {d.name.lower(): d for d in cls.parse_manifest(file_path, new_content or "")}

        changed_deps: list[Dependency] = []
        for name, new_dep in new_deps.items():
            if name not in old_deps:
                # Newly added package
                changed_deps.append(new_dep)
            elif old_deps[name].version != new_dep.version:
                # Upgraded / changed package version
                changed_deps.append(new_dep)

        return changed_deps

    # -------------------------------------------------------------------------
    # Requirements.txt Parser
    # -------------------------------------------------------------------------

    @classmethod
    def _parse_requirements_txt(cls, file_path: str, content: str) -> list[Dependency]:
        deps: list[Dependency] = []
        lines = content.splitlines()

        for line in lines:
            line = line.strip()
            # Ignore empty lines, comments, and flags
            if not line or line.startswith(("#", "-r", "-f", "-i", "--", "-e")):
                continue

            # Strip inline comments and environment markers
            line = line.split(";", 1)[0].split("#", 1)[0].strip()

            match = PY_REQUIREMENT_REGEX.match(line)
            if match:
                name = match.group(1).strip()
                version = match.group(3).strip() if match.group(3) else ""
                # Clean version (strip quotes, wildcards)
                version = version.replace("*", "0").strip()

                deps.append(
                    Dependency(
                        name=name,
                        version=version,
                        ecosystem="PyPI",
                        manifest_file=file_path,
                        is_dev="dev" in file_path.lower() or "test" in file_path.lower(),
                    )
                )

        return deps

    # -------------------------------------------------------------------------
    # pyproject.toml Parser (PEP 621 & Poetry)
    # -------------------------------------------------------------------------

    @classmethod
    def _parse_pyproject_toml(cls, file_path: str, content: str) -> list[Dependency]:
        deps: list[Dependency] = []
        try:
            data = tomllib.loads(content)
        except Exception:
            return []

        # 1. PEP 621 Standard project.dependencies
        project_deps = data.get("project", {}).get("dependencies", [])
        if isinstance(project_deps, list):
            for dep_str in project_deps:
                match = PY_REQUIREMENT_REGEX.match(dep_str.strip())
                if match:
                    name = match.group(1).strip()
                    version = match.group(3).strip() if match.group(3) else ""
                    deps.append(
                        Dependency(
                            name=name,
                            version=version,
                            ecosystem="PyPI",
                            manifest_file=file_path,
                            is_dev=False,
                        )
                    )

        # 2. PEP 621 Optional / Dev dependencies
        optional_deps = data.get("project", {}).get("optional-dependencies", {})
        if isinstance(optional_deps, dict):
            for group, group_deps in optional_deps.items():
                is_dev = group.lower() in ("dev", "test", "lint", "docs")
                for dep_str in group_deps:
                    match = PY_REQUIREMENT_REGEX.match(dep_str.strip())
                    if match:
                        name = match.group(1).strip()
                        version = match.group(3).strip() if match.group(3) else ""
                        deps.append(
                            Dependency(
                                name=name,
                                version=version,
                                ecosystem="PyPI",
                                manifest_file=file_path,
                                is_dev=is_dev,
                            )
                        )

        # 3. Poetry tool.poetry.dependencies
        poetry_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
        if isinstance(poetry_deps, dict):
            for name, ver in poetry_deps.items():
                if name.lower() == "python":
                    continue
                version_str = cls._clean_poetry_version(ver)
                deps.append(
                    Dependency(
                        name=name,
                        version=version_str,
                        ecosystem="PyPI",
                        manifest_file=file_path,
                        is_dev=False,
                    )
                )

        # 4. Poetry dev-dependencies or group.dev.dependencies
        dev_groups = data.get("tool", {}).get("poetry", {}).get("group", {})
        for _group_name, group_data in dev_groups.items():
            group_deps = group_data.get("dependencies", {})
            for name, ver in group_deps.items():
                deps.append(
                    Dependency(
                        name=name,
                        version=cls._clean_poetry_version(ver),
                        ecosystem="PyPI",
                        manifest_file=file_path,
                        is_dev=True,
                    )
                )

        return deps

    @staticmethod
    def _clean_poetry_version(ver: any) -> str:
        if isinstance(ver, str):
            # Strip carets, tildes: ^1.2.3 -> 1.2.3
            return re.sub(r"[\^~>=<]", "", ver).strip()
        elif isinstance(ver, dict) and "version" in ver:
            return re.sub(r"[\^~>=<]", "", str(ver["version"])).strip()
        return ""

    # -------------------------------------------------------------------------
    # package.json Parser (npm)
    # -------------------------------------------------------------------------

    @classmethod
    def _parse_package_json(cls, file_path: str, content: str) -> list[Dependency]:
        deps: list[Dependency] = []
        try:
            data = json.loads(content)
        except Exception:
            return []

        # Production dependencies
        prod_deps = data.get("dependencies", {})
        if isinstance(prod_deps, dict):
            for name, ver in prod_deps.items():
                clean_ver = cls._clean_npm_version(str(ver))
                deps.append(
                    Dependency(
                        name=name,
                        version=clean_ver,
                        ecosystem="npm",
                        manifest_file=file_path,
                        is_dev=False,
                    )
                )

        # Dev dependencies
        dev_deps = data.get("devDependencies", {})
        if isinstance(dev_deps, dict):
            for name, ver in dev_deps.items():
                clean_ver = cls._clean_npm_version(str(ver))
                deps.append(
                    Dependency(
                        name=name,
                        version=clean_ver,
                        ecosystem="npm",
                        manifest_file=file_path,
                        is_dev=True,
                    )
                )

        return deps

    @staticmethod
    def _clean_npm_version(version: str) -> str:
        # e.g.: ^18.2.0 -> 18.2.0, ~4.1.0 -> 4.1.0, >=2.0.0 -> 2.0.0
        return re.sub(r"[\^~>=<v]", "", version).strip()
