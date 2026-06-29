"""TraceScribe CLI entry point."""

from __future__ import annotations

from pathlib import Path

import typer
import yaml
from rich.console import Console
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
    typer.echo(f"Generating docs for {epic_key}...")


# ---------------------------------------------------------------------------
# config init
# ---------------------------------------------------------------------------


@config_app.command("init")
def config_init() -> None:
    """Interactively create ~/.tracescribe/config.yaml."""
    console.print("[bold]TraceScribe — Configuration Setup[/bold]\n")
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

    console.print(f"\n[green]✓[/green] Config written to [bold]{_CONFIG_FILE}[/bold]")


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

    # LLM
    table.add_row("llm", "provider", cfg.llm.provider)
    table.add_row("llm", "model", cfg.llm.model)
    table.add_row("llm", "base_url", cfg.llm.base_url)

    console.print(table)


if __name__ == "__main__":
    app()
