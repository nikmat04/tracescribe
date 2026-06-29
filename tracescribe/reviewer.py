"""Interactive review loop — shown to the engineer before a PR is created."""

from __future__ import annotations

import os
import subprocess
import tempfile
import webbrowser
from pathlib import Path

import markdown
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()

_PREVIEW_LINES = 20

_HTML_WRAPPER = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>TraceScribe Preview</title>
<style>
  body {{ font-family: -apple-system, "Segoe UI", system-ui, sans-serif;
          max-width: 760px; margin: 40px auto; padding: 0 20px;
          line-height: 1.6; color: #1f2328; }}
  pre  {{ background: #f7f8fa; padding: 12px; border-radius: 4px; overflow-x: auto; }}
  code {{ font-size: 0.9em; }}
</style>
</head>
<body>
{body}
</body>
</html>
"""

_PROMPT_TEXT = (
    "  [y] Submit PR   [e] Edit in editor\n"
    "  [p] Preview in browser   [n] Cancel"
)


def _show_preview(content: str) -> None:
    """Print the first 20 lines of *content* using rich Syntax highlighting."""
    lines = content.splitlines()
    snippet = "\n".join(lines[:_PREVIEW_LINES])
    console.print(Syntax(snippet, "markdown", theme="ansi_dark", word_wrap=True))
    remaining = len(lines) - _PREVIEW_LINES
    if remaining > 0:
        console.print(f"[dim][... {remaining} more line{'s' if remaining != 1 else ''}][/dim]")


def _edit_in_editor(content: str) -> str:
    """Write *content* to a temp .md file, open $EDITOR, return edited content."""
    editor = os.environ.get("EDITOR", "nano")
    with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False, encoding="utf-8") as fh:
        fh.write(content)
        tmp_path = fh.name
    try:
        subprocess.call([editor, tmp_path])
        return Path(tmp_path).read_text(encoding="utf-8")
    finally:
        os.unlink(tmp_path)


def _preview_in_browser(content: str) -> None:
    """Render *content* as HTML, open in the default browser, wait for Enter."""
    body = markdown.markdown(content, extensions=["fenced_code", "tables"])
    html = _HTML_WRAPPER.format(body=body)
    with tempfile.NamedTemporaryFile(suffix=".html", mode="w", delete=False, encoding="utf-8") as fh:
        fh.write(html)
        tmp_path = fh.name
    webbrowser.open(f"file://{tmp_path}")
    input("Preview opened in browser. Press Enter to continue...")


def review_loop(content: str, epic_key: str) -> tuple[bool, str]:
    """Show an inline preview and prompt the engineer before PR creation.

    Returns:
        (True,  final_content) — engineer approved, proceed to PR.
        (False, final_content) — engineer cancelled, content saved to draft.
    """
    while True:
        _show_preview(content)
        console.print(Panel(_PROMPT_TEXT, title="Review", expand=False))

        choice = input("Your choice: ").strip().lower()

        if choice == "y":
            return (True, content)

        elif choice == "e":
            content = _edit_in_editor(content)

        elif choice == "p":
            _preview_in_browser(content)

        elif choice == "n":
            drafts_dir = Path.home() / ".tracescribe" / "drafts"
            drafts_dir.mkdir(parents=True, exist_ok=True)
            draft_path = drafts_dir / f"{epic_key}.md"
            draft_path.write_text(content, encoding="utf-8")
            console.print(f"Draft saved to ~/.tracescribe/drafts/{epic_key}.md")
            return (False, content)

        else:
            console.print("[yellow]Please enter y, e, p, or n.[/yellow]")
