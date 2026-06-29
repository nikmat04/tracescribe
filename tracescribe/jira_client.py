"""Jira REST API client for TraceScribe.

Fetches epic metadata from Jira Data Center using Bearer-token (PAT) auth.
ADF (Atlassian Document Format) descriptions are recursively extracted to
plain text so downstream components receive a clean string.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

from tracescribe.config import JiraConfig

# Default fixture path — resolved relative to this file's package directory
_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_epic.json"


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


@dataclass
class EpicData:
    key: str            # e.g. "INSTA-4821"
    summary: str        # e.g. "Spring WebFlux Tracing Follow-Up"
    description: str    # plain text extracted from ADF or raw string
    components: list[str]   # e.g. ["java-agent"]
    fix_versions: list[str] # e.g. ["2026 Q2"]
    assignee: str       # display name or "Unassigned"
    status: str         # e.g. "In Progress"
    labels: list[str]   # e.g. ["tracing", "webflux"]


class JiraError(Exception):
    """Raised when the Jira API returns an error or is unreachable."""


# ---------------------------------------------------------------------------
# ADF → plain text
# ---------------------------------------------------------------------------


def _extract_adf_text(node: Any) -> str:
    """Recursively extract all text node values from an ADF document.

    The Atlassian Document Format nests content nodes at arbitrary depth:
      doc → blockquote/paragraph/bulletList/… → listItem/… → text

    This function walks the tree and concatenates every ``"text"`` node,
    inserting a newline after block-level nodes so the result is readable.
    """
    if not isinstance(node, dict):
        return ""

    node_type = node.get("type", "")
    text_parts: list[str] = []

    # Leaf node: return the text value directly
    if node_type == "text":
        return node.get("text", "")

    # Recurse into child content nodes
    for child in node.get("content", []):
        child_text = _extract_adf_text(child)
        if child_text:
            text_parts.append(child_text)

    # Join children; add a trailing newline after block-level containers
    _BLOCK_TYPES = {
        "doc", "paragraph", "heading", "bulletList", "orderedList",
        "listItem", "blockquote", "codeBlock", "rule", "panel",
    }
    separator = "\n" if node_type in _BLOCK_TYPES else ""
    joined = "".join(text_parts)
    return joined + separator if joined else ""


def _parse_description(raw_desc: Any) -> str:
    """Return plain text from a Jira description field.

    Handles both ADF (dict with ``"type": "doc"``) and plain string values.
    """
    if raw_desc is None:
        return ""
    if isinstance(raw_desc, str):
        return raw_desc.strip()
    # ADF object
    return _extract_adf_text(raw_desc).strip()


# ---------------------------------------------------------------------------
# Response → EpicData
# ---------------------------------------------------------------------------


def _parse_response(data: dict) -> EpicData:
    """Map a Jira issue API response dict to an EpicData instance."""
    fields: dict = data.get("fields", {})

    assignee_obj = fields.get("assignee") or {}
    status_obj = fields.get("status") or {}

    return EpicData(
        key=data["key"],
        summary=fields.get("summary", ""),
        description=_parse_description(fields.get("description")),
        components=[c["name"] for c in fields.get("components", [])],
        fix_versions=[v["name"] for v in fields.get("fixVersions", [])],
        assignee=assignee_obj.get("displayName", "Unassigned"),
        status=status_obj.get("name", "Unknown"),
        labels=fields.get("labels", []),
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_epic(issue_key: str, config: JiraConfig) -> EpicData:
    """Fetch epic metadata from Jira and return an :class:`EpicData`.

    Raises:
        JiraError: On HTTP errors or connection failures with a clear message.
    """
    url = (
        f"{config.base_url.rstrip('/')}/rest/api/3/issue/{issue_key}"
        "?fields=summary,description,components,fixVersions,assignee,status,labels"
    )
    headers = {"Authorization": f"Bearer {config.pat}", "Accept": "application/json"}

    try:
        response = requests.get(url, headers=headers, timeout=15)
    except requests.exceptions.ConnectionError:
        raise JiraError(f"Cannot reach Jira at {config.base_url}")

    if response.status_code == 404:
        raise JiraError(f"Epic {issue_key} not found in Jira")
    if response.status_code == 401:
        raise JiraError("Invalid Jira PAT — check your config")
    if not response.ok:
        raise JiraError(
            f"Jira returned {response.status_code} for {issue_key}: {response.text[:200]}"
        )

    return _parse_response(response.json())


def get_epic_mock(fixture_path: str | None = None) -> EpicData:
    """Load fixture JSON and return an :class:`EpicData` without any network call.

    Args:
        fixture_path: Path to an alternative fixture file.  Defaults to
            ``tracescribe/fixtures/sample_epic.json``.
    """
    path = Path(fixture_path) if fixture_path else _FIXTURE_PATH
    with path.open() as fh:
        data = json.load(fh)
    return _parse_response(data)
