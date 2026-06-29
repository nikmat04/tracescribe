# TraceScribe

TraceScribe is a CLI tool that turns a Jira epic into an Instana Knowledge Center documentation draft and, after review, opens a GitHub pull request.

## Features

- Fetch epic metadata from Jira
- Build the target Knowledge Center path automatically
- Render a Markdown document from a structured template
- Optionally use a local LLM via Ollama for prose sections
- Let you review/edit before submission
- Open a GitHub PR with the generated document

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com/) for local LLM generation (optional if using `--no-llm`)

## Installation

### 1. Install Ollama

```bash
brew install ollama
```

### 2. Pull the default model

```bash
ollama pull llama3.3:70b-instruct-q4_K_M
```

### 3. Install TraceScribe

From GitHub:

```bash
pip install git+https://github.com/nikmat04/tracescribe.git
```

For local development:

```bash
pip install -e .
```

## Quick Start

Initialize your config:

```bash
tracescribe config init
```

This creates `~/.tracescribe/config.yaml` and prompts for your Jira PAT and GitHub token.  
Then run:

```bash
tracescribe generate INSTA-4821
```

## CLI Usage

### Generate docs

```bash
tracescribe generate INSTA-4821
```

Options:

- `--mock` — use fixture Jira data instead of calling Jira
- `--dry-run` — print the generated doc to stdout and skip GitHub
- `--no-llm` — skip LLM generation and leave template placeholders in place

Example:

```bash
tracescribe generate INSTA-4821 --mock --dry-run
```

### Config commands

Create config:

```bash
tracescribe config init
```

Show resolved config (with secrets masked):

```bash
tracescribe config show
```

## Environment Variables

TraceScribe also supports environment variable fallbacks for config values:

- `JIRA_BASE_URL`
- `JIRA_PAT`
- `GITHUB_TOKEN`
- `GITHUB_REPO`

## Development

Run tests:

```bash
pytest
```

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
  base_url: https://api.github.com  # IBM GitHub: https://github.ibm.com/api/v3

llm:
  provider: ollama
  model: llama3.3:70b-instruct-q4_K_M
  base_url: http://localhost:11434
```
