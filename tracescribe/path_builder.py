"""Helpers for deriving Knowledge Center documentation paths from epic metadata."""

from __future__ import annotations

import re

from tracescribe.jira_client import EpicData

_COMPONENT_SECTION_MAP = {
    "java-agent": "java",
    "java": "java",
    "nodejs-agent": "nodejs",
    "nodejs": "nodejs",
    "python-agent": "python",
    "python": "python",
    "dotnet-agent": "dotnet",
    "dotnet": "dotnet",
    "go-agent": "go",
    "go": "go",
    "ruby-agent": "ruby",
    "ruby": "ruby",
}


def slugify(text: str) -> str:
    """Convert free-form text into an underscore-delimited slug."""
    slug = text.lower()
    slug = re.sub(r"[\s-]+", "_", slug)
    slug = re.sub(r"[^a-z0-9_]", "", slug)
    slug = re.sub(r"_+", "_", slug)
    return slug.strip("_")


def parse_fix_version(version: str) -> tuple[str, str]:
    """Extract year and quarter from a Jira fix version string."""
    normalized = version.strip().lower()
    patterns = (
        r"^(\d{4})[-\s]+(q[1-4])$",
        r"^(q[1-4])[-\s]+(\d{4})$",
    )

    for pattern in patterns:
        match = re.match(pattern, normalized)
        if not match:
            continue
        first, second = match.groups()
        if first.startswith("q"):
            return second, first
        return first, second

    return "unknown", "unknown"


def component_to_section(component: str) -> str:
    """Map a Jira component name to a tracing documentation section."""
    normalized = component.strip().lower()
    return _COMPONENT_SECTION_MAP.get(normalized, slugify(component))


def build_doc_path(epic: EpicData) -> str:
    """Build the repo-relative documentation path for an epic."""
    section = component_to_section(epic.components[0]) if epic.components else "general"
    year, quarter = parse_fix_version(epic.fix_versions[0]) if epic.fix_versions else ("unknown", "unknown")
    slug = slugify(epic.summary)
    return f"docs/product_overview/tracing/{section}/epics/{year}/{quarter}/{slug}/index.md"
