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

config_app = typer.Typer(help="Manage TraceScribe configuration.", no_args_is_help=True)
app.add_typer(config_app, name="config")

console = Console()

_CONFIG_DIR = Path.home() / ".tracescribe"
_CONFIG_FILE = _CONFIG_DIR / "config.yaml"


def _version_callback(value: bool) -> None:
    if value:
        from tracescribe import __version__
        typer.echo(f"tracescribe {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", callback=_version_callback, is_eager=True,
        help="Print the version and exit.",
    ),
) -> None:
    pass


def _prompt_epic_manually() -> "EpicData":
    """Interactively prompt the engineer to paste epic details from Jira."""
    from tracescribe.jira_client import EpicData

    console.print()
    console.print(
        "[bold cyan]Manual Epic Input[/bold cyan] — paste the details from your Jira epic below.\n"
        "[dim]Press Enter to accept defaults where shown in brackets.[/dim]\n"
    )

    console.rule("[cyan]Epic Metadata[/cyan]")
    key = typer.prompt("  Epic key (e.g. INSTA-4821)")
    summary = typer.prompt("  Epic summary (title)")

    console.rule("[cyan]Epic Description[/cyan]")
    console.print(
        "  [dim]Paste the full epic description below.\n"
        "  When done, type [bold]END[/bold] on a new line and press Enter.[/dim]\n"
    )
    lines: list[str] = []
    while True:
        line = input()
        if line.strip().upper() == "END":
            break
        lines.append(line)
    description = "\n".join(lines).strip()

    console.rule("[cyan]Epic Details[/cyan]")
    component = typer.prompt(
        "  Component (e.g. java-agent, nodejs-agent, python-agent)", default="java-agent",
    )
    fix_version = typer.prompt("  Fix version / Quarter (e.g. 2026 Q2)", default="2026 Q2")
    assignee = typer.prompt("  Assignee (your name)", default="Unassigned")
    status = typer.prompt("  Status", default="In Progress")
    labels_raw = typer.prompt("  Labels (comma-separated, e.g. tracing,webflux)", default="")
    labels = [lbl.strip() for lbl in labels_raw.split(",") if lbl.strip()]

    return EpicData(
        key=key, summary=summary, description=description,
        components=[component] if component else [],
        fix_versions=[fix_version] if fix_version else [],
        assignee=assignee, status=status, labels=labels,
    )


@app.command("generate")
def generate(
    epic_key: str = typer.Argument("", help="Jira epic key. Omit when using --manual or --mock."),
    mock: bool = typer.Option(False, "--mock", help="Use local fixture data instead of calling Jira."),
    manual: bool = typer.Option(False, "--manual", help="Manually paste epic details instead of fetching from Jira."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print the generated doc to stdout; skip GitHub PR creation."),
    no_llm: bool = typer.Option(False, "--no-llm", help="Skip LLM generation and leave template stubs in place."),
) -> None:
    """Generate a Knowledge Center documentation page for an epic."""
    from tracescribe.github_client import GitHubError, create_doc_pr
    from tracescribe.jira_client import JiraError, get_epic, get_epic_mock
    from tracescribe.llm.base import LLMError
    from tracescribe.llm.factory import get_llm_provider
    from tracescribe.path_builder import build_doc_path
    from tracescribe.prompts import (
        architecture_diagram_prompt, business_benefits_prompt, business_use_cases_prompt,
        communication_plan_prompt, config_after_prompt, config_before_prompt,
        config_env_vars_prompt, config_system_props_prompt, config_yaml_prompt,
        example_scenarios_prompt, hierarchical_structure_prompt, precedence_rules_prompt,
        problem_statement_prompt, qa_notes_prompt, summary_prompt, technical_implementation_prompt,
    )
    from tracescribe.renderer import render_doc
    from tracescribe.reviewer import review_loop

    try:
        if mock or manual:
            try:
                config = load_config()
            except ConfigError:
                from tracescribe.config import GitHubConfig, JiraConfig, TraceScribeConfig
                config = TraceScribeConfig(
                    jira=JiraConfig(base_url="https://jsw.ibm.com", pat=""),
                    github=GitHubConfig(token="", repo="instana/instana-knowledge-center"),
                )
        else:
            config = load_config()
        console.print("[green]  \u2714[/green] Config loaded")

        if manual:
            epic = _prompt_epic_manually()
        elif mock:
            epic = get_epic_mock()
        else:
            if not epic_key:
                console.print("[red]  \u2718[/red] Provide an epic key, or use [bold]--manual[/bold] to enter details manually.")
                raise typer.Exit(code=1)
            epic = get_epic(epic_key, config.jira)
        console.print(f"[green]  \u2714[/green] Epic loaded: [bold]{epic.summary}[/bold] [{epic.key}]")

        doc_path = build_doc_path(epic)
        console.print(f"[green]  \u2714[/green] Doc path: [dim]{doc_path}[/dim]")

        prose: dict[str, str] = {
            "problem_statement": "", "summary": "", "config_yaml": "",
            "config_system_props": "", "config_env_vars": "", "hierarchical_structure": "",
            "precedence_rules": "", "example_scenarios": "", "config_before": "",
            "config_after": "", "technical_implementation": "", "architecture_diagram": "",
            "business_benefits": "", "business_use_cases": "", "qa_notes": "", "communication_plan": "",
        }
        if no_llm:
            console.print("[dim]  \u2500 LLM skipped (--no-llm)[/dim]")
        else:
            provider = get_llm_provider(config.llm)
            sections = [
                ("Problem Statement",      "problem_statement",       problem_statement_prompt(epic)),
                ("Summary",                "summary",                 summary_prompt(epic)),
                ("Config YAML",            "config_yaml",             config_yaml_prompt(epic)),
                ("Config System Props",    "config_system_props",     config_system_props_prompt(epic)),
                ("Config Env Vars",        "config_env_vars",         config_env_vars_prompt(epic)),
                ("Hierarchical Structure", "hierarchical_structure",  hierarchical_structure_prompt(epic)),
                ("Precedence Rules",       "precedence_rules",        precedence_rules_prompt(epic)),
                ("Example Scenarios",      "example_scenarios",       example_scenarios_prompt(epic)),
                ("Before",                 "config_before",           config_before_prompt(epic)),
                ("After",                  "config_after",            config_after_prompt(epic)),
                ("Technical Impl",         "technical_implementation", technical_implementation_prompt(epic)),
                ("Architecture Diagram",   "architecture_diagram",    architecture_diagram_prompt(epic)),
                ("Business Benefits",      "business_benefits",       business_benefits_prompt(epic)),
                ("Business Use Cases",     "business_use_cases",      business_use_cases_prompt(epic)),
                ("QA & Testing Notes",     "qa_notes",                qa_notes_prompt(epic)),
                ("Communication Plan",     "communication_plan",      communication_plan_prompt(epic)),
            ]
            total = len(sections)
            for idx, (label, key, prompt) in enumerate(sections, 1):
                with console.status(f"[bold]  [{idx}/{total}] Generating: {label}\u2026[/bold]", spinner="dots"):
                    prose[key] = provider.generate(prompt)
            console.print("[green]  \u2714[/green] Documentation generated")

        jira_base_url = getattr(config.jira, "base_url", None) or "https://jsw.ibm.com"
        content = render_doc(epic, doc_path, jira_base_url, **prose)

        if dry_run:
            console.print()
            console.print(Rule("[dim]Generated document[/dim]"))
            console.print(content)
            console.print(Rule())
            raise typer.Exit(0)

        console.print()
        console.print(Rule("[bold]Review[/bold]"))
        approved, final_content = review_loop(content, epic.key)
        if not approved:
            raise typer.Exit(0)

        with console.status("[bold]  Creating pull request\u2026[/bold]", spinner="dots"):
            pr = create_doc_pr(doc_path, final_content, epic, config.github)
        console.print(f"[green]  \u2714[/green] PR created: [link={pr.url}]{pr.url}[/link]")

    except ConfigError as exc:
        console.print(f"[red]  \u2718 Config error:[/red] {exc}\n  Run: [bold]tracescribe config init[/bold]")
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


@config_app.command("init")
def config_init() -> None:
    """Interactively create ~/.tracescribe/config.yaml."""
    console.print("[bold]TraceScribe \u2014 Configuration Setup[/bold]\n")
    console.print("Press [bold]Enter[/bold] to accept the default shown in brackets.\n")

    console.rule("[cyan]Jira[/cyan]")
    jira_base_url: str = typer.prompt("  Jira base URL (e.g. https://jsw.ibm.com)")
    jira_pat: str = typer.prompt("  Jira Personal Access Token", hide_input=True)

    console.rule("[cyan]GitHub[/cyan]")
    github_token: str = typer.prompt("  GitHub token", hide_input=True)
    github_repo: str = typer.prompt("  GitHub repo (owner/name)", default="instana/instana-knowledge-center")
    github_base_branch: str = typer.prompt("  Base branch", default="main")
    github_base_url: str = typer.prompt("  GitHub API base URL", default="https://api.github.com")

    console.rule("[cyan]LLM[/cyan]")
    llm_provider: str = typer.prompt("  LLM provider", default="ollama")
    llm_model: str = typer.prompt("  LLM model", default="llama3.3:70b-instruct-q4_K_M")
    llm_base_url: str = typer.prompt("  LLM base URL", default="http://localhost:11434")

    config_data = {
        "jira": {"base_url": jira_base_url, "pat": jira_pat},
        "github": {"token": github_token, "repo": github_repo, "base_branch": github_base_branch, "base_url": github_base_url},
        "llm": {"provider": llm_provider, "model": llm_model, "base_url": llm_base_url},
    }

    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with _CONFIG_FILE.open("w") as fh:
        yaml.dump(config_data, fh, default_flow_style=False, allow_unicode=True)
    console.print(f"\n[green]\u2713[/green] Config written to [bold]{_CONFIG_FILE}[/bold]")


def _mask(secret: str) -> str:
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
    table.add_row("jira", "base_url", cfg.jira.base_url)
    table.add_row("jira", "pat", _mask(cfg.jira.pat))
    table.add_row("github", "token", _mask(cfg.github.token))
    table.add_row("github", "repo", cfg.github.repo)
    table.add_row("github", "base_branch", cfg.github.base_branch)
    table.add_row("github", "base_url", cfg.github.base_url)
    table.add_row("llm", "provider", cfg.llm.provider)
    table.add_row("llm", "model", cfg.llm.model)
    table.add_row("llm", "base_url", cfg.llm.base_url)
    console.print(table)


if __name__ == "__main__":
    app()
