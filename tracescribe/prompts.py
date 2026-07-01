"""Focused prompt builders for each LLM-generated documentation section.

Matches the real Instana Internal Knowledge Center format as observed in:
- span-disabling, springwebflux_fup, rpg-tracing, java-tracer-otlp-exporter-design

Sections generated:
  Problem Statement | Summary |
  Config Examples (YAML / System Props / Env Vars) |
  Hierarchical Structure | Precedence Rules | Example Scenarios |
  Before/After | Technical Implementation | Architecture Diagram (Mermaid) |
  Business Outcome (Benefits + Use Cases) | QA & Testing Notes | Communication Plan

Style rules:
- Write for a technical audience of Instana engineers and users.
- Be specific and concrete. Reference actual config keys, class names, method names.
- Avoid marketing language.
- Do not include the section heading in your output.
- Output only the documentation content, nothing else.
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
        f"Assignee: {epic.assignee}\n"
        f"Labels: {', '.join(epic.labels) if epic.labels else 'none'}\n"
        f"Description:\n{epic.description}"
    )


_STYLE = (
    "Write for a technical audience of Instana engineers and users. "
    "Be specific and concrete — reference actual config keys, class names, or API details where inferable. "
    "Avoid marketing language. "
    "Do NOT include the section heading. "
    "Output only the documentation content, nothing else."
)


def problem_statement_prompt(epic: EpicData) -> str:
    return (
        f"{_epic_context(epic)}\n\n"
        "Write the 'Problem Statement' section for the Instana Internal Knowledge Center page. "
        "Clearly describe: (1) what currently exists and its limitations, (2) what customers "
        "cannot do today because of this gap, (3) why this matters — reference affected components, "
        "specific limitations, and any known impacted customers or use cases. "
        "Use bullet points for listing limitations where appropriate. "
        f"{_STYLE}"
    )


def summary_prompt(epic: EpicData) -> str:
    return (
        f"{_epic_context(epic)}\n\n"
        "Write the 'Summary' section for the Instana Internal Knowledge Center page. "
        "Provide a concise technical summary of what this epic delivers: what was built, "
        "what levels of control it introduces (if hierarchical), what specification it follows, "
        "and the overall scope. Use bullet points or a numbered list for the key deliverables. "
        "2-3 paragraphs maximum. "
        f"{_STYLE}"
    )


def config_yaml_prompt(epic: EpicData) -> str:
    return (
        f"{_epic_context(epic)}\n\n"
        "Write the 'Agent Configuration (YAML)' subsection for the Instana Internal Knowledge Center page. "
        "Show realistic YAML configuration examples for the feature described in the epic. "
        "Show multiple examples if the feature supports multiple configuration modes. "
        "Use fenced code blocks with 'yaml' syntax highlighting. "
        "Add inline comments explaining each key. "
        "Base the config key names on the existing Instana Java agent config conventions "
        "(e.g. com.instana.plugin.javatrace or com.instana.tracing). "
        f"{_STYLE}"
    )


def config_system_props_prompt(epic: EpicData) -> str:
    return (
        f"{_epic_context(epic)}\n\n"
        "Write the 'System Properties' subsection for the Instana Internal Knowledge Center page. "
        "Show JVM system property equivalents of the YAML configuration for the feature. "
        "Use fenced code blocks. Follow the Instana convention: "
        "-Dcom.instana.<feature>.<key>=<value>. "
        "Show 2-3 realistic examples. "
        f"{_STYLE}"
    )


def config_env_vars_prompt(epic: EpicData) -> str:
    return (
        f"{_epic_context(epic)}\n\n"
        "Write the 'Environment Variables' subsection for the Instana Internal Knowledge Center page. "
        "Show environment variable equivalents for the feature configuration. "
        "Use SCREAMING_SNAKE_CASE following Instana conventions (e.g. INSTANA_TRACING_*). "
        "Use fenced code blocks. Show 2-3 realistic examples with brief comments. "
        f"{_STYLE}"
    )


def hierarchical_structure_prompt(epic: EpicData) -> str:
    return (
        f"{_epic_context(epic)}\n\n"
        "Write the 'Hierarchical Structure' section for the Instana Internal Knowledge Center page. "
        "If the feature introduces any hierarchy or layering (e.g. category -> type -> plugin, "
        "or entry span -> exit span), describe it clearly. "
        "Use an ASCII diagram or indented list to show the hierarchy. "
        "Then include a Markdown table defining each level with columns: Level | Values | Description. "
        "If no hierarchy applies, write a brief paragraph about the feature's structural design instead. "
        f"{_STYLE}"
    )


def precedence_rules_prompt(epic: EpicData) -> str:
    return (
        f"{_epic_context(epic)}\n\n"
        "Write the 'Precedence Rules' section for the Instana Internal Knowledge Center page. "
        "Describe how conflicts are resolved when multiple configuration options apply. "
        "State the precedence order clearly in bold (e.g. **Plugin > Type > Category > Default**). "
        "Then explain each rule with concrete examples showing what happens when options conflict. "
        "If precedence rules don't apply to this feature, write about the feature's decision logic instead. "
        f"{_STYLE}"
    )


def example_scenarios_prompt(epic: EpicData) -> str:
    return (
        f"{_epic_context(epic)}\n\n"
        "Write the 'Example Scenarios' section for the Instana Internal Knowledge Center page. "
        "Create 3-4 numbered, named real-world scenarios that show how to use the feature. "
        "For each scenario: give it a descriptive name, show the configuration (YAML code block), "
        "and describe the result/outcome. "
        "Make the scenarios progressively more complex — simple case first, then edge cases. "
        f"{_STYLE}"
    )


def config_before_prompt(epic: EpicData) -> str:
    return (
        f"{_epic_context(epic)}\n\n"
        "Write the 'Before' subsection of the 'Before/After Comparison' section for the "
        "Instana Internal Knowledge Center page. "
        "Show the OLD way of doing things before this feature existed — the limited or missing "
        "configuration, with a YAML/properties code block. "
        "Then list the limitations of the old approach as bullet points. "
        f"{_STYLE}"
    )


def config_after_prompt(epic: EpicData) -> str:
    return (
        f"{_epic_context(epic)}\n\n"
        "Write the 'After' subsection of the 'Before/After Comparison' section for the "
        "Instana Internal Knowledge Center page. "
        "Show the NEW configuration this feature introduces with a YAML/properties code block "
        "and inline comments. "
        "Then list the benefits/improvements as bullet points. "
        f"{_STYLE}"
    )


def technical_implementation_prompt(epic: EpicData) -> str:
    return (
        f"{_epic_context(epic)}\n\n"
        "Write the 'Technical Implementation' section for the Instana Internal Knowledge Center page. "
        "Describe how the feature is implemented in the Java tracer: "
        "(1) List the files/classes modified with a brief description of each change. "
        "(2) Show the key data structures, enums, or interfaces introduced (use Java code blocks). "
        "(3) Describe the state management or resolution logic. "
        "(4) Note any performance considerations. "
        "Be specific — use real Java class names, method names, and data types where inferable. "
        f"{_STYLE}"
    )


def architecture_diagram_prompt(epic: EpicData) -> str:
    return (
        f"{_epic_context(epic)}\n\n"
        "Write the 'Architecture / Flow Diagram' section for the Instana Internal Knowledge Center page. "
        "Create ONE Mermaid flowchart diagram that shows the core decision or processing flow of this feature. "
        "The diagram should show the most important decision points or data flow. "
        "Use this exact format:\n\n"
        "```mermaid\n"
        "flowchart TD\n"
        "    A[Start] --> B{Decision}\n"
        "    B -->|Yes| C[Action]\n"
        "    B -->|No| D[Other Action]\n"
        "```\n\n"
        "Rules for the Mermaid syntax: "
        "- Use only alphanumeric node IDs (A, B, C1, etc.) "
        "- Keep node labels short and clear "
        "- Use TD direction (top-down) "
        "- Do NOT use parentheses inside square brackets "
        "- Do NOT use quotes inside node labels "
        "Output ONLY the mermaid code block, nothing else. "
        f"{_STYLE}"
    )


def business_benefits_prompt(epic: EpicData) -> str:
    return (
        f"{_epic_context(epic)}\n\n"
        "Write the 'Benefits' subsection of the 'Business Outcome' section for the "
        "Instana Internal Knowledge Center page. "
        "List the concrete benefits this feature delivers to customers as bullet points. "
        "Each benefit should have a bold label followed by a colon and explanation "
        "(e.g. **Compliance:** Easily disable sensitive data tracing...). "
        "Reference specific customer pain points from the epic description. "
        f"{_STYLE}"
    )


def business_use_cases_prompt(epic: EpicData) -> str:
    return (
        f"{_epic_context(epic)}\n\n"
        "Write the 'Use Cases' subsection of the 'Business Outcome' section for the "
        "Instana Internal Knowledge Center page. "
        "List 4-5 concrete real-world use cases as bullet points. "
        "Each use case should be a single sentence describing a specific scenario where "
        "a customer would use this feature. Be practical and specific. "
        f"{_STYLE}"
    )


def qa_notes_prompt(epic: EpicData) -> str:
    return (
        f"{_epic_context(epic)}\n\n"
        "Write the 'QA & Testing Notes' section for the Instana Internal Knowledge Center page. "
        "Structure it as: "
        "(1) A brief 'Test Approach' paragraph describing the overall testing strategy. "
        "(2) A 'Key Test Areas' section with bullet points covering: configuration parsing, "
        "functional correctness, precedence/edge cases, performance impact, "
        "backward compatibility, and integration tests. "
        "Reference the acceptance criteria from the epic description. "
        f"{_STYLE}"
    )


def communication_plan_prompt(epic: EpicData) -> str:
    return (
        f"{_epic_context(epic)}\n\n"
        "Write the 'Communication Plan' section for the Instana Internal Knowledge Center page. "
        "List as bullet points: release notes update, changelog entry, public documentation update, "
        "internal Slack notification, support team briefing, customer success team update, "
        "migration guide for existing users, and any other relevant communication actions. "
        "Keep it practical and actionable. "
        f"{_STYLE}"
    )
