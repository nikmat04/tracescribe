"""TraceScribe CLI entry point."""

from __future__ import annotations

import typer

app = typer.Typer(
    name="tracescribe",
    help="Auto-generate Instana Knowledge Center documentation from Jira epics.",
    add_completion=False,
)


@app.command()
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


if __name__ == "__main__":
    app()
