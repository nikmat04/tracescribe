# TraceScribe

> **Auto-generate Instana Knowledge Center documentation from Jira epics — locally, with a single command.**

TraceScribe pulls an epic from Jira, drafts a structured Markdown documentation page using a local LLM (Ollama), lets you review and edit it, then opens a pull request against the Knowledge Center GitHub repo.

All data stays on your machine. The LLM runs locally via Ollama — nothing leaves your laptop.

---

## Team Onboarding

Follow these steps once to get up and running:

### 1. Install Ollama

```bash
brew install ollama
```

### 2. Pull the model

```bash
ollama pull llama3.3:70b-instruct-q4_K_M
```

> The model is ~24 GB. This only needs to be done once. Subsequent `generate` calls are instant.

### 3. Install TraceScribe

```bash
pip install git+https://github.com/nikmat04/tracescribe.git
```

Or pin to a stable release:

```bash
pip install git+https://github.com/nikmat04/tracescribe.git@v0.1.0
```

### 4. Configure

```bash
tracescribe config init
```

This creates `~/.tracescribe/config.yaml` and prompts for your Jira PAT and GitHub token.  
Alternatively, export the environment variables listed in [`.env.example`](.env.example).

### 5. Generate docs

```bash
tracescribe generate INSTA-4821
```

TraceScribe will:
1. Fetch the epic from Jira
2. Generate structured documentation using the local LLM
3. Show you a preview and let you review / edit
4. Open a pull request against the Knowledge Center repo

---

## CLI Reference

### `tracescribe generate <EPIC_KEY>`

Generate a documentation page for a Jira epic.

| Flag | Description |
|------|-------------|
| `--mock` | Use local fixture data instead of calling Jira. Useful for development and demos without a live Jira connection. |
| `--dry-run` | Print the generated doc to stdout only; skip the interactive review and GitHub PR creation. Useful for scripting. |
| `--no-llm` | Skip LLM generation. The output will be a filled-in template with placeholder stubs instead of LLM-written prose. |

**Examples:**

```bash
# Full flow against real Jira
tracescribe generate INSTA-4821

# Development / demo — no Jira, no GitHub
tracescribe generate INSTA-4821 --mock --dry-run

# Full flow with fixture data, interactive review included
tracescribe generate INSTA-4821 --mock

# Generate without LLM (template stubs only)
tracescribe generate INSTA-4821 --no-llm
```

### `tracescribe config init`

Interactively create `~/.tracescribe/config.yaml`.

### `tracescribe config show`

Print the resolved configuration (YAML + env var overrides) to the terminal.

---

## Configuration

TraceScribe reads `~/.tracescribe/config.yaml`. Missing keys fall back to environment variables.

```yaml
# ~/.tracescribe/config.yaml
jira:
  base_url: https://jsw.ibm.com
  pat: ${JIRA_PAT}

github:
  token: ${GITHUB_TOKEN}
  repo: instana/instana-knowledge-center
  base_branch: main

llm:
  provider: ollama
  model: llama3.3:70b-instruct-q4_K_M
  base_url: http://localhost:11434
```

See [`.env.example`](.env.example) for all supported environment variables.

---

## Project Structure

```
tracescribe/
├── tracescribe/
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   ├── jira_client.py
│   ├── path_builder.py
│   ├── renderer.py
│   ├── reviewer.py
│   ├── prompts.py
│   ├── github_client.py
│   ├── llm/
│   │   ├── base.py
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

## Development

```bash
git clone https://github.com/nikmat04/tracescribe.git
cd tracescribe
pip install -e .
tracescribe --help
```

---

## License

MIT
