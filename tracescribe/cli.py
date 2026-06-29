"""TraceScribe CLI entry point."""

from __future__ import annotations

from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.rule import Rule
from rich.table import Table

from tracescribe.config import ConfigError, load_config

app = typer.Typer(
    name="tracescribe",
    help="Auto-generate Instana Knowledge Center documentation from Jira epics.",
    add_completion=False,
    no_args_is_help=True,
)

# Sub-app for config commands
config_app = typer.Typer(help="Manage TraceScribe configuration.", no_args_is_help=True)
app.add_typer(config_app, name="config")

console = Console()

_CONFIG_DIR = Path.home() / ".tracescribe"
_CONFIG_FILE = _CONFIG_DIR / "config.yaml"


# ---------------------------------------------------------------------------
# --version
# ---------------------------------------------------------------------------


def _version_callback(value: bool) -> None:
    if value:
        from tracescribe import __version__
        typer.echo(f"tracescribe {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Print the version and exit.",
    ),
) -> None:
    pass


# ---------------------------------------------------------------------------
# generate
# ---------------------------------------------------------------------------


@app.command("generate")
def generate(
    epic_key: str = typer.Argument(..., help="Jira epic key, e.g. INSTA-4821"),
    mock: bool = typer.Option(
        False,
        "--mock",
        help="Use local fixture data instead of calling Jira.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Print the generated doc to stdout; skip GitHub PR creation.",
    ),
    no_llm: bool = typer.Option(
        False,
        "--no-llm",
        help="Skip LLM generation and leave template stubs in place.",
    ),
) -> None:
    """Generate a Knowledge Center documentation page for an epic."""
    from tracescribe.github_client import GitHubError, create_doc_pr
    from tracescribe.jira_client import JiraError, get_epic, get_epic_mock
    from tracescribe.llm.base import LLMError
    from tracescribe.llm.factory import get_llm_provider
    from tracescribe.path_builder import build_doc_path
    from tracescribe.prompts import (
        motivation_prompt,
        overview_prompt,
        technical_approach_prompt,
        usage_prompt,
    )
    from tracescribe.renderer import render_doc
    from tracescribe.reviewer import review_loop

    try:
        # ── Step 1: Config ────────────────────────────────────────────────
        if mock:
            # In mock mode config is optional — use safe defaults for fields
            # that may not be set (jira.base_url, github creds).
            try:
                config = load_config()
            except ConfigError:
                from tracescribe.config import GitHubConfig, JiraConfig, LLMConfig, TraceScribeConfig
                config = TraceScribeConfig(
                    jira=JiraConfig(base_url="https://jsw.ibm.com", pat="mock-pat"),
                    github=GitHubConfig(token="mock-token", repo="instana/instana-knowledge-center"),
                )
        else:
            config = load_config()
        console.print("[green]  \u2714[/green] Config loaded")

        # ── Step 2: Fetch epic ────────────────────────────────────────────
        if mock:
            epic = get_epic_mock()
        else:
            epic = get_epic(epic_key, config.jira)
        console.print(
            f"[green]  \u2714[/green] Fetched Jira epic: [bold]{epic.summary}[/bold] [{epic.key}]"
        )

        # ── Step 3: Build doc path ────────────────────────────────────────
        doc_path = build_doc_path(epic)
        console.print(f"[green]  \u2714[/green] Doc path: [dim]{doc_path}[/dim]")

        # ── Step 4: Generate LLM prose ────────────────────────────────────
        overview = motivation = technical_approach = usage = ""
        if no_llm:
            console.print("[dim]  \u2500 LLM skipped (--no-llm)[/dim]")
        else:
            with console.status("[bold]  Generating documentation\u2026[/bold]", spinner="dots"):
                provider = get_llm_provider(config.llm)
                overview = provider.generate(overview_prompt(epic))
                motivation = provider.generate(motivation_prompt(epic))
                technical_approach = provider.generate(technical_approach_prompt(epic))
                usage = provider.generate(usage_prompt(epic))
            console.print("[green]  \u2714[/green] Documentation generated")

        # ── Step 5: Render doc ────────────────────────────────────────────
        jira_base_url = getattr(config.jira, "base_url", None) or "https://jsw.ibm.com"
        content = render_doc(
            epic,
            doc_path,
            jira_base_url,
            overview=overview,
            motivation=motivation,
            technical_approach=technical_approach,
            usage=usage,
        )

        # ── Step 6: Dry-run — print and exit ─────────────────────────────
        if dry_run:
            console.print()
            console.print(Rule("[dim]Generated document[/dim]"))
            console.print(content)
            console.print(Rule())
            raise typer.Exit(0)

        # ── Step 7: Interactive review loop ───────────────────────────────
        console.print()
        console.print(Rule("[bold]Review[/bold]"))
        approved, final_content = review_loop(content, epic.key)
        if not approved:
            raise typer.Exit(0)

        # ── Step 8: Create PR ─────────────────────────────────────────────
        with console.status("[bold]  Creating pull request\u2026[/bold]", spinner="dots"):
            pr = create_doc_pr(doc_path, final_content, epic, config.github)
        console.print(f"[green]  \u2714[/green] PR created: [link={pr.url}]{pr.url}[/link]")

    except ConfigError as exc:
        console.print(
            f"[red]  \u2718 Config error:[/red] {exc}\n"
            "  Run: [bold]tracescribe config init[/bold]"
        )
        raise typer.Exit(code=1)
    except JiraError as exc:
        console.print(f"[red]  \u2718 Jira error:[/red] {exc}")
        raise typer.Exit(code=1)
    except LLMError as exc:
        console.print(f"[red]  \u2718 LLM error:[/red] {exc}")
        raise typer.Exit(code=1)
    except GitHubError as exc:
        console.print(f"[red]  \u2718 GitHub error:[/red] {exc}")
        raise typer.Exit(code=1)
    except typer.Exit:
        raise
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]  \u2718 Unexpected error:[/red] {exc}")
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# config init
# ---------------------------------------------------------------------------


@config_app.command("init")
def config_init() -> None:
    """Interactively create ~/.tracescribe/config.yaml."""
    console.print("[bold]TraceScribe \u2014 Configuration Setup[/bold]\n")
    console.print(
        "Press [bold]Enter[/bold] to accept the default shown in brackets.\n"
    )

    # Jira
    console.rule("[cyan]Jira[/cyan]")
    jira_base_url: str = typer.prompt("  Jira base URL (e.g. https://jsw.ibm.com)")
    jira_pat: str = typer.prompt("  Jira Personal Access Token", hide_input=True)

    # GitHub
    console.rule("[cyan]GitHub[/cyan]")
    github_token: str = typer.prompt("  GitHub token", hide_input=True)
    github_repo: str = typer.prompt(
        "  GitHub repo (owner/name)",
        default="instana/instana-knowledge-center",
    )
    github_base_branch: str = typer.prompt("  Base branch", default="main")
    github_base_url: str = typer.prompt(
        "  GitHub API base URL",
        default="https://api.github.com",
    )

    # LLM
    console.rule("[cyan]LLM[/cyan]")
    llm_provider: str = typer.prompt("  LLM provider", default="ollama")
    llm_model: str = typer.prompt(
        "  LLM model",
        default="llama3.3:70b-instruct-q4_K_M",
    )
    llm_base_url: str = typer.prompt(
        "  LLM base URL",
        default="http://localhost:11434",
    )

    config_data = {
        "jira": {
            "base_url": jira_base_url,
            "pat": jira_pat,
        },
        "github": {
            "token": github_token,
            "repo": github_repo,
            "base_branch": github_base_branch,
            "base_url": github_base_url,
        },
        "llm": {
            "provider": llm_provider,
            "model": llm_model,
            "base_url": llm_base_url,
        },
    }

    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with _CONFIG_FILE.open("w") as fh:
        yaml.dump(config_data, fh, default_flow_style=False, allow_unicode=True)

    console.print(f"\n[green]\u2713[/green] Config written to [bold]{_CONFIG_FILE}[/bold]")


# ---------------------------------------------------------------------------
# config show
# ---------------------------------------------------------------------------


def _mask(secret: str) -> str:
    """Return the last 4 characters of *secret* preceded by asterisks."""
    if len(secret) <= 4:
        return "*" * len(secret)
    return f"{'*' * (len(secret) - 4)}{secret[-4:]}"


@config_app.command("show")
def config_show() -> None:
    """Print the resolved configuration (secrets masked)."""
    try:
        cfg = load_config()
    except ConfigError as exc:
        console.print(f"[red]Configuration error:[/red] {exc}")
        raise typer.Exit(1) from exc

    table = Table(title="TraceScribe Configuration", show_header=True, header_style="bold cyan")
    table.add_column("Section", style="bold", no_wrap=True)
    table.add_column("Key", no_wrap=True)
    table.add_column("Value")

    # Jira
    table.add_row("jira", "base_url", cfg.jira.base_url)
    table.add_row("jira", "pat", _mask(cfg.jira.pat))

    # GitHub
    table.add_row("github", "token", _mask(cfg.github.token))
    table.add_row("github", "repo", cfg.github.repo)
    table.add_row("github", "base_branch", cfg.github.base_branch)
    table.add_row("github", "base_url", cfg.github.base_url)

    # LLM
    table.add_row("llm", "provider", cfg.llm.provider)
    table.add_row("llm", "model", cfg.llm.model)
    table.add_row("llm", "base_url", cfg.llm.base_url)

    console.print(table)


if __name__ == "__main__":
    app()
