"""TraceScribe configuration loader.

Priority (highest → lowest):
  1. Values in ~/.tracescribe/config.yaml
  2. Environment variables
  3. Hard-coded defaults (for optional fields only)

${ENV_VAR} placeholders inside the YAML are expanded via os.path.expandvars.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

CONFIG_PATH = Path.home() / ".tracescribe" / "config.yaml"


class ConfigError(Exception):
    """Raised when a required configuration value cannot be resolved."""


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class JiraConfig:
    base_url: str   # e.g. https://jsw.ibm.com
    pat: str        # Personal Access Token


@dataclass
class GitHubConfig:
    token: str
    repo: str                    # e.g. instana/instana-knowledge-center
    base_branch: str = "main"
    base_url: str = "https://api.github.com"


@dataclass
class LLMConfig:
    provider: str = "ollama"
    model: str = "llama3.3:70b-instruct-q4_K_M"
    base_url: str = "http://localhost:11434"


@dataclass
class TraceScribeConfig:
    jira: JiraConfig
    github: GitHubConfig
    llm: LLMConfig = field(default_factory=LLMConfig)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _expand(value: Any) -> str:
    """Return *value* as a string with ${ENV_VAR} placeholders expanded."""
    return os.path.expandvars(str(value))


def _require(value: str | None, field_name: str, env_var: str) -> str:
    """Return *value* if non-empty, else raise a helpful ConfigError."""
    if value:
        return value
    raise ConfigError(
        f"Missing required config: {field_name} — "
        f"set {env_var} env var or run: tracescribe config init"
    )


def _get(raw: dict, *keys: str, env_var: str = "", default: str = "") -> str:
    """Walk nested *keys* in *raw*, expand vars, fall back to env / default."""
    node: Any = raw
    for key in keys:
        if not isinstance(node, dict):
            node = None
            break
        node = node.get(key)

    if node is not None:
        value = _expand(node)
        if value:
            return value

    # Fall back to environment variable
    if env_var:
        env_value = os.environ.get(env_var, "")
        if env_value:
            return env_value

    return default


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_config(config_path: Path = CONFIG_PATH) -> TraceScribeConfig:
    """Load and validate the TraceScribe configuration."""
    raw: dict = {}
    if config_path.exists():
        with config_path.open() as fh:
            raw = yaml.safe_load(fh) or {}

    jira_base_url = _require(
        _get(raw, "jira", "base_url", env_var="JIRA_BASE_URL"),
        "jira.base_url",
        "JIRA_BASE_URL",
    )
    jira_pat = _require(
        _get(raw, "jira", "pat", env_var="JIRA_PAT"),
        "jira.pat",
        "JIRA_PAT",
    )
    github_token = _require(
        _get(raw, "github", "token", env_var="GITHUB_TOKEN"),
        "github.token",
        "GITHUB_TOKEN",
    )
    github_repo = _require(
        _get(raw, "github", "repo", env_var="GITHUB_REPO"),
        "github.repo",
        "GITHUB_REPO",
    )
    github_base_branch = _get(raw, "github", "base_branch", default="main")
    github_base_url = _get(raw, "github", "base_url", default="https://api.github.com")

    llm_provider = _get(raw, "llm", "provider", default="ollama")
    llm_model = _get(raw, "llm", "model", default="llama3.3:70b-instruct-q4_K_M")
    llm_base_url = _get(raw, "llm", "base_url", default="http://localhost:11434")

    return TraceScribeConfig(
        jira=JiraConfig(base_url=jira_base_url, pat=jira_pat),
        github=GitHubConfig(
            token=github_token,
            repo=github_repo,
            base_branch=github_base_branch,
            base_url=github_base_url,
        ),
        llm=LLMConfig(
            provider=llm_provider,
            model=llm_model,
            base_url=llm_base_url,
        ),
    )
