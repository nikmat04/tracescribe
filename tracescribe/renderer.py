"""Markdown document renderer for TraceScribe.

Renders the Jinja2 template at ``tracescribe/templates/epic_doc.md.jinja``
into a complete Markdown document, substituting EpicData metadata and
optional LLM-generated prose.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from tracescribe.jira_client import EpicData

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_TEMPLATE_NAME = "epic_doc.md.jinja"

_STUB = "*[LLM generation skipped — run without --no-llm to populate this section.]*"

_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    keep_trailing_newline=True,
    autoescape=False,
)


def render_doc(
    epic: EpicData,
    doc_path: str,
    jira_base_url: str,
    problem_statement: str = "",
    summary: str = "",
    config_yaml: str = "",
    config_system_props: str = "",
    config_env_vars: str = "",
    hierarchical_structure: str = "",
    precedence_rules: str = "",
    example_scenarios: str = "",
    config_before: str = "",
    config_after: str = "",
    technical_implementation: str = "",
    architecture_diagram: str = "",
    business_benefits: str = "",
    business_use_cases: str = "",
    qa_notes: str = "",
    communication_plan: str = "",
) -> str:
    """Render the epic documentation template to a Markdown string."""
    template = _jinja_env.get_template(_TEMPLATE_NAME)

    context = {
        "epic": epic,
        "doc_path": doc_path,
        "jira_base_url": jira_base_url.rstrip("/"),
        "generated_date": date.today().isoformat(),
        "problem_statement": problem_statement or _STUB,
        "summary": summary or _STUB,
        "config_yaml": config_yaml or _STUB,
        "config_system_props": config_system_props or _STUB,
        "config_env_vars": config_env_vars or _STUB,
        "hierarchical_structure": hierarchical_structure or _STUB,
        "precedence_rules": precedence_rules or _STUB,
        "example_scenarios": example_scenarios or _STUB,
        "config_before": config_before or _STUB,
        "config_after": config_after or _STUB,
        "technical_implementation": technical_implementation or _STUB,
        "architecture_diagram": architecture_diagram or _STUB,
        "business_benefits": business_benefits or _STUB,
        "business_use_cases": business_use_cases or _STUB,
        "qa_notes": qa_notes or _STUB,
        "communication_plan": communication_plan or _STUB,
    }

    return template.render(context)
