from tracescribe.jira_client import EpicData, get_epic_mock
from tracescribe.path_builder import (
    build_doc_path,
    component_to_section,
    parse_fix_version,
    slugify,
)


def test_slugify_handles_spaces_hyphens_special_chars_and_case() -> None:
    assert slugify("Spring WebFlux Tracing Follow-Up") == "spring_webflux_tracing_follow_up"
    assert slugify("Hello   World") == "hello_world"
    assert slugify("Alpha-Beta-Gamma") == "alpha_beta_gamma"
    assert slugify("Mixed CASE & Special!! Chars") == "mixed_case_special_chars"


def test_parse_fix_version_handles_supported_formats() -> None:
    assert parse_fix_version("2026 Q2") == ("2026", "q2")
    assert parse_fix_version("2026-Q2") == ("2026", "q2")
    assert parse_fix_version("Q2 2026") == ("2026", "q2")
    assert parse_fix_version("q2-2026") == ("2026", "q2")


def test_parse_fix_version_returns_unknown_for_unparseable_input() -> None:
    assert parse_fix_version("FY26 Quarter 2") == ("unknown", "unknown")


def test_component_to_section_maps_known_components() -> None:
    assert component_to_section("java-agent") == "java"
    assert component_to_section("java") == "java"
    assert component_to_section("nodejs-agent") == "nodejs"
    assert component_to_section("nodejs") == "nodejs"
    assert component_to_section("python-agent") == "python"
    assert component_to_section("python") == "python"
    assert component_to_section("dotnet-agent") == "dotnet"
    assert component_to_section("dotnet") == "dotnet"
    assert component_to_section("go-agent") == "go"
    assert component_to_section("go") == "go"
    assert component_to_section("ruby-agent") == "ruby"
    assert component_to_section("ruby") == "ruby"


def test_component_to_section_slugifies_unknown_components() -> None:
    assert component_to_section("Custom Agent") == "custom_agent"


def test_build_doc_path_with_sample_insta_4821_fixture() -> None:
    epic = get_epic_mock()

    assert build_doc_path(epic) == (
        "docs/product_overview/tracing/java/epics/2026/q2/"
        "spring_webflux_tracing_follow_up/index.md"
    )


def test_build_doc_path_uses_general_and_unknown_defaults() -> None:
    epic = EpicData(
        key="INSTA-0000",
        summary="General Tracing Improvement",
        description="",
        components=[],
        fix_versions=[],
        assignee="Unassigned",
        status="Open",
        labels=[],
    )

    assert build_doc_path(epic) == (
        "docs/product_overview/tracing/general/epics/unknown/unknown/"
        "general_tracing_improvement/index.md"
    )
