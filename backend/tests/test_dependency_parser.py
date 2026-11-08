from app.analyzer.dependency_parser import DependencyParser

SAMPLE_REQUIREMENTS = """
# Production requirements
fastapi==0.115.0
uvicorn[standard]>=0.30.0; python_version >= '3.10'
pydantic>=2.8.0,<3.0.0
# Comment line
-e .
requests==2.31.0 # Pinned for security
flask
"""

SAMPLE_PYPROJECT = """
[project]
name = "demo-app"
version = "0.1.0"
dependencies = [
    "requests==2.28.1",
    "sqlalchemy>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "ruff==0.5.0",
]

[tool.poetry.dependencies]
python = "^3.12"
jinja2 = "^3.1.2"
"""

SAMPLE_PACKAGE_JSON = """
{
  "name": "frontend",
  "dependencies": {
    "react": "^18.2.0",
    "next": "14.2.3",
    "lodash": "~4.17.21"
  },
  "devDependencies": {
    "typescript": "^5.4.0",
    "tailwindcss": "4.0.0-alpha"
  }
}
"""


def test_is_manifest_file():
    assert DependencyParser.is_manifest_file("requirements.txt") is True
    assert DependencyParser.is_manifest_file("backend/requirements.txt") is True
    assert DependencyParser.is_manifest_file("requirements/dev.txt") is True
    assert DependencyParser.is_manifest_file("pyproject.toml") is True
    assert DependencyParser.is_manifest_file("package.json") is True
    assert DependencyParser.is_manifest_file("src/main.py") is False


def test_parse_requirements_txt():
    deps = DependencyParser.parse_manifest("requirements.txt", SAMPLE_REQUIREMENTS)
    dep_map = {d.name: d for d in deps}

    assert "fastapi" in dep_map
    assert dep_map["fastapi"].version == "0.115.0"
    assert dep_map["fastapi"].ecosystem == "PyPI"

    assert "uvicorn" in dep_map
    assert dep_map["uvicorn"].version == "0.30.0"

    assert "pydantic" in dep_map
    assert dep_map["pydantic"].version == "2.8.0"

    assert "requests" in dep_map
    assert dep_map["requests"].version == "2.31.0"

    assert "flask" in dep_map


def test_parse_pyproject_toml():
    deps = DependencyParser.parse_manifest("pyproject.toml", SAMPLE_PYPROJECT)
    dep_map = {d.name: d for d in deps}

    assert "requests" in dep_map
    assert dep_map["requests"].version == "2.28.1"
    assert dep_map["requests"].is_dev is False

    assert "sqlalchemy" in dep_map
    assert dep_map["sqlalchemy"].version == "2.0.0"

    assert "pytest" in dep_map
    assert dep_map["pytest"].is_dev is True

    assert "jinja2" in dep_map
    assert dep_map["jinja2"].version == "3.1.2"


def test_parse_package_json():
    deps = DependencyParser.parse_manifest("package.json", SAMPLE_PACKAGE_JSON)
    dep_map = {d.name: d for d in deps}

    assert "react" in dep_map
    assert dep_map["react"].version == "18.2.0"
    assert dep_map["react"].ecosystem == "npm"
    assert dep_map["react"].is_dev is False

    assert "next" in dep_map
    assert dep_map["next"].version == "14.2.3"

    assert "lodash" in dep_map
    assert dep_map["lodash"].version == "4.17.21"

    assert "typescript" in dep_map
    assert dep_map["typescript"].is_dev is True


def test_extract_changed_dependencies():
    old_reqs = "requests==2.20.0\nurllib3==1.25.0"
    new_reqs = "requests==2.31.0\nurllib3==1.25.0\nfastapi==0.115.0"

    changed = DependencyParser.extract_changed_dependencies("requirements.txt", old_reqs, new_reqs)
    names = {d.name: d.version for d in changed}

    # requests was upgraded, fastapi was newly added
    assert "requests" in names
    assert names["requests"] == "2.31.0"
    assert "fastapi" in names
    assert names["fastapi"] == "0.115.0"

    # urllib3 was unchanged
    assert "urllib3" not in names
