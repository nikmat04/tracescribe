"""TraceScribe CLI entry point."""

from __future__ import annotations

import typer

app = typer.Typer(
    name="tracescribe",
    help="Auto-generate Instana Knowledge Center documentation from Jira epics.",
    add_completion=False,
    no_args_is_help=True,
)

# Sub-app for config commands (implemented in Sub-Task 2)
config_app = typer.Typer(help="Manage TraceScribe configuration.", no_args_is_help=True)
app.add_typer(config_app, name="config")


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


@config_app.command("init")
def config_init() -> None:
    """Interactively create ~/.tracescribe/config.yaml. (coming in Sub-Task 2)"""
    typer.echo("tracescribe config init — not yet implemented.")


@config_app.command("show")
def config_show() -> None:
    """Print the resolved configuration. (coming in Sub-Task 2)"""
    typer.echo("tracescribe config show — not yet implemented.")


if __name__ == "__main__":
    app()
