# TraceScribe

TraceScribe is a CLI tool that turns a Jira epic into an Instana Knowledge Center
documentation draft and, after review, opens a GitHub pull request — all from a
single command:

```bash
tracescribe generate INSTA-4821
```

All data stays local. The LLM runs on-device via Ollama (default: `llama3.3:70b-instruct-q4_K_M`).

---

## Features

- Fetch epic metadata from Jira Data Center (PAT auth)
- Derive the correct Knowledge Center folder path automatically
- Render a structured Markdown document from a Jinja2 template
- Optionally enrich prose sections using a local LLM via Ollama
- Interactive review loop: edit in `$EDITOR`, preview in browser, approve, or cancel
- Open a GitHub PR with the generated document ready to merge
- Pluggable LLM backend via config (Ollama supported; watsonx / OpenAI coming)

---

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com/) for local LLM generation (skip with `--no-llm`)
- A Jira PAT and a GitHub personal access token

---

## Team Onboarding

Follow these five steps to get from nothing to your first generated PR.

### 1 — Install Ollama

```bash
brew install ollama
```

Start the Ollama daemon (keep this running in a separate terminal or configure it
to start at login):

```bash
ollama serve
```

### 2 — Pull the default model

```bash
ollama pull llama3.3:70b-instruct-q4_K_M
```

This is a one-time download (~24 GB). Coffee break recommended.

### 3 — Install TraceScribe

Pin to the stable release:

```bash
pip install git+https://github.com/nikmat04/tracescribe.git@v0.1.0
```

Or install from the latest `main`:

```bash
pip install git+https://github.com/nikmat04/tracescribe.git
```

For contributors — editable install from a local clone:

```bash
git clone https://github.com/nikmat04/tracescribe.git
cd tracescribe
pip install -e .
```

### 4 — Configure TraceScribe

```bash
tracescribe config init
```

This launches an interactive prompt and writes `~/.tracescribe/config.yaml`.
You will need:

| Value | Where to get it |
|---|---|
| **Jira base URL** | e.g. `https://jsw.ibm.com` |
| **Jira PAT** | Jira → Profile → Personal Access Tokens |
| **GitHub token** | GitHub → Settings → Developer settings → Personal access tokens |
| **GitHub repo** | e.g. `instana/instana-knowledge-center` |
| **GitHub API base URL** | `https://api.github.com` (public) or `https://github.ibm.com/api/v3` (IBM GHE) |

### 5 — Generate your first doc

```bash
tracescribe generate INSTA-4821
```

---

## CLI Reference

### `tracescribe generate <EPIC_KEY>`

Generate a Knowledge Center documentation page for a Jira epic.

```
Usage: tracescribe generate [OPTIONS] EPIC_KEY

Arguments:
  EPIC_KEY  Jira epic key, e.g. INSTA-4821  [required]

Options:
  --mock        Use local fixture data instead of calling Jira.
  --dry-run     Print the generated doc to stdout; skip GitHub PR creation.
  --no-llm      Skip LLM generation and leave template stubs in place.
  --help        Show this message and exit.
```

#### Flag combinations

| Flags | Behaviour |
|---|---|
| _(none)_ | Full pipeline: Jira → LLM → review → PR |
| `--mock` | Use fixture epic; still runs LLM and review loop |
| `--no-llm` | Skip LLM; template stubs appear in the output |
| `--dry-run` | Print rendered doc to terminal; skip review loop and GitHub |
| `--mock --dry-run --no-llm` | Safest for local testing — no network calls at all |

#### Progress output

```
  ✔ Config loaded
  ✔ Fetched Jira epic: Spring WebFlux Tracing Follow-Up [INSTA-4821]
  ✔ Doc path: docs/product_overview/tracing/java/epics/2026/q2/…/index.md
  ⠸ Generating documentation…
  ✔ Documentation generated
  ──────────────────── Review ────────────────────
  [interactive review loop]
  ✔ PR created: https://github.com/instana/instana-knowledge-center/pull/847
```

#### Review loop options

After generation, if you are not using `--dry-run` you will see an inline preview
followed by a prompt:

```
  [y] Submit PR   [e] Edit in editor
  [p] Preview in browser   [n] Cancel
```

- **y** — approve and create the PR immediately
- **e** — open the doc in `$EDITOR` (falls back to `nano`); re-prompts after save
- **p** — render Markdown to HTML and open in your default browser; re-prompts on Enter
- **n** — cancel; draft saved to `~/.tracescribe/drafts/<EPIC_KEY>.md`

---

### `tracescribe config init`

Interactively create or overwrite `~/.tracescribe/config.yaml`.

### `tracescribe config show`

Print the resolved configuration with secrets masked to the last 4 characters.

### `tracescribe --version`

Print the installed version and exit.

```bash
$ tracescribe --version
tracescribe 0.1.0
```

---

## Configuration Reference

TraceScribe reads `~/.tracescribe/config.yaml`.  
Missing keys fall back to the corresponding environment variables.  
`${ENV_VAR}` placeholders inside the YAML are expanded at load time.

```yaml
# ~/.tracescribe/config.yaml

jira:
  base_url: https://jsw.ibm.com      # required — also: JIRA_BASE_URL env var
  pat: ${JIRA_PAT}                   # required — also: JIRA_PAT env var

github:
  token: ${GITHUB_TOKEN}             # required — also: GITHUB_TOKEN env var
  repo: instana/instana-knowledge-center  # required — also: GITHUB_REPO env var
  base_branch: main                  # default: main
  base_url: https://api.github.com   # IBM GitHub Enterprise: https://github.ibm.com/api/v3

llm:
  provider: ollama                   # default: ollama (only supported provider in v0.1)
  model: llama3.3:70b-instruct-q4_K_M  # default model
  base_url: http://localhost:11434   # default Ollama address
```

### IBM GitHub Enterprise

If your knowledge-center repo lives on IBM's GitHub Enterprise instance, set:

```yaml
github:
  base_url: https://github.ibm.com/api/v3
  repo: instana/instana-knowledge-center
```

---

## Environment Variables

All required config values can be supplied as environment variables instead of
(or alongside) the YAML file.

| Variable | Config key |
|---|---|
| `JIRA_BASE_URL` | `jira.base_url` |
| `JIRA_PAT` | `jira.pat` |
| `GITHUB_TOKEN` | `github.token` |
| `GITHUB_REPO` | `github.repo` |

---

## Error Messages

| Error | Cause | Fix |
|---|---|---|
| `✘ Config error` | Missing required config value | Run `tracescribe config init` |
| `✘ Jira error: Cannot reach Jira` | Jira URL unreachable | Check VPN / Jira URL |
| `✘ Jira error: Invalid Jira PAT` | Bad token | Regenerate Jira PAT |
| `✘ LLM error` | Ollama not running or wrong model | Run `ollama serve` and `ollama pull <model>` |
| `✘ GitHub error: Invalid GitHub token` | Bad token | Regenerate GitHub token |

---

## Development

```bash
git clone https://github.com/nikmat04/tracescribe.git
cd tracescribe
pip install -e .
pytest
```

### Project layout

```
tracescribe/
├── tracescribe/
│   ├── __init__.py        # __version__
│   ├── cli.py             # Typer app — entry point
│   ├── config.py          # YAML config loader
│   ├── jira_client.py     # Jira REST client + EpicData dataclass
│   ├── path_builder.py    # Doc path derivation
│   ├── renderer.py        # Jinja2 → Markdown
│   ├── reviewer.py        # Interactive review loop
│   ├── prompts.py         # LLM prompt builders
│   ├── github_client.py   # PyGithub PR creation
│   ├── llm/
│   │   ├── base.py        # Abstract LLMProvider
│   │   ├── ollama_provider.py
│   │   └── factory.py
│   ├── templates/
│   │   └── epic_doc.md.jinja
│   └── fixtures/
│       └── sample_epic.json
├── tests/
│   └── test_path_builder.py
├── pyproject.toml
├── README.md
└── .env.example
```

---

## License

MIT
