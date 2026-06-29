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

# Template directory resolved relative to this source file so the package
# works correctly both as an editable install and as a built distribution.
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
    overview: str = "",
    motivation: str = "",
    technical_approach: str = "",
    usage: str = "",
) -> str:
    """Render the epic documentation template to a Markdown string.

    Args:
        epic: Populated :class:`~tracescribe.jira_client.EpicData` instance.
        doc_path: Repo-relative path where the doc will be committed, e.g.
            ``docs/product_overview/tracing/java/epics/2026/q2/springwebflux_fup/index.md``.
        jira_base_url: Base URL of the Jira instance, e.g. ``https://jsw.ibm.com``.
        overview: LLM-generated overview prose.  Falls back to stub if empty.
        motivation: LLM-generated motivation prose.  Falls back to stub if empty.
        technical_approach: LLM-generated technical-approach prose.  Falls back
            to stub if empty.
        usage: LLM-generated configuration/usage prose.  Falls back to stub if empty.

    Returns:
        Rendered Markdown string ready to be written to a file or printed.
    """
    template = _jinja_env.get_template(_TEMPLATE_NAME)

    context = {
        "epic": epic,
        "doc_path": doc_path,
        "jira_base_url": jira_base_url.rstrip("/"),
        "generated_date": date.today().isoformat(),
        "overview": overview or _STUB,
        "motivation": motivation or _STUB,
        "technical_approach": technical_approach or _STUB,
        "usage": usage or _STUB,
    }

    return template.render(context)
