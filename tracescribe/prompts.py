"""Focused prompt builders for each LLM-generated documentation section.

Each function receives an EpicData and returns a prompt string that instructs
the LLM to write a specific section of the Knowledge Center page.

Style rules embedded in every prompt:
- Write for a technical audience (Instana engineers and users).
- Be specific and concrete; avoid marketing language.
- Output only the documentation prose \u2014 no preamble, no \"Here is the doc:\".
"""

from __future__ import annotations

from tracescribe.jira_client import EpicData


def _epic_context(epic: EpicData) -> str:
    """Common context block included in every prompt."""
    components = ", ".join(epic.components) if epic.components else "N/A"
    fix_versions = ", ".join(epic.fix_versions) if epic.fix_versions else "N/A"
    return (
        f"Epic key: {epic.key}\n"
        f"Summary: {epic.summary}\n"
        f"Components: {components}\n"
        f"Fix versions: {fix_versions}\n"
        f"Description:\n{epic.description}"
    )


def overview_prompt(epic: EpicData) -> str:
    """Return a prompt that asks the LLM to write a 2-3 paragraph overview."""
    return (
        f"{_epic_context(epic)}\n\n"
        "Write a 2-3 paragraph overview of this feature for the Instana Internal "
        "Knowledge Center. Explain what the feature is, what it delivers, and what "
        "problem space it addresses. Write for a technical audience of Instana "
        "engineers and users. Be specific and concrete. Avoid marketing language. "
        "Output only the documentation prose."
    )


def motivation_prompt(epic: EpicData) -> str:
    """Return a prompt that asks the LLM to explain why the feature matters."""
    return (
        f"{_epic_context(epic)}\n\n"
        "Write a section titled 'Motivation / Why This Feature' for the Instana "
        "Internal Knowledge Center. Explain the problem this feature solves, the "
        "limitations it removes, and the concrete benefit to Instana engineers or "
        "end users. Write for a technical audience. Be specific; reference the "
        "affected component(s) where relevant. Avoid marketing language. "
        "Output only the documentation prose."
    )


def technical_approach_prompt(epic: EpicData) -> str:
    """Return a prompt that asks the LLM to describe the implementation approach."""
    return (
        f"{_epic_context(epic)}\n\n"
        "Write a 'Technical Approach' section for the Instana Internal Knowledge "
        "Center. Describe how this feature was implemented: key design decisions, "
        "which components or layers were changed, the overall approach taken, and "
        "any notable trade-offs. Write for a technical audience of Instana "
        "engineers. Be specific and concrete. Avoid marketing language. "
        "Output only the documentation prose."
    )


def usage_prompt(epic: EpicData) -> str:
    """Return a prompt that asks the LLM to document configuration and usage."""
    return (
        f"{_epic_context(epic)}\n\n"
        "Write a 'Configuration / Usage' section for the Instana Internal Knowledge "
        "Center. Document how to configure or use this feature: list any relevant "
        "configuration keys, environment variables, or API options. Include concise "
        "code or YAML snippets where applicable. Write for a technical audience. "
        "Be specific and concrete. Avoid marketing language. "
        "Output only the documentation prose."
    )
