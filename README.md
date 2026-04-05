# Waterloo

A terminal-first personal assistant with a hybrid brain: by default it uses **local** inference (Ollama). You can switch to a **cloud** API (OpenAI-compatible) when you want stronger models. Conversation history and opt-in **memory notes** persist in SQLite on your machine.

## Setup

Requires Python 3.11+.

```bash
cd /path/to/waterloo
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Local model (Ollama)

Install [Ollama](https://ollama.com/) and pull a model, for example:

```bash
ollama pull llama3.2
```

Defaults: base URL `http://127.0.0.1:11434`, model from `WATERLOO_OLLAMA_MODEL` or `llama3.2`.

### Cloud model (OpenAI API)

Set an API key:

```bash
export OPENAI_API_KEY=sk-...
```

Optional: `OPENAI_BASE_URL` for compatible proxies (default `https://api.openai.com/v1`).

## Run

Default routing is **`local`** (Ollama). Use `/mode cloud` or `export WATERLOO_MODE=cloud` for the API when configured.

```bash
waterloo
# or
python -m waterloo
```

## Slash commands

| Command | Description |
|--------|-------------|
| `/help` | Show help |
| `/mode local\|cloud\|auto` | Force provider or automatic routing |
| `/health` | Check Ollama and cloud configuration |
| `/remember <text>` | Store an opt-in long-term memory note |
| `/forget <id>` | Delete a memory note by id |
| `/memories` | List stored notes |
| `/clear` | Clear messages in the current conversation (not memory notes) |
| `/export` | Print path to SQLite database |
| `/quit` | Exit |

In **auto** mode, messages containing sensitive keywords (for example `password`, `api key`) are routed to the local model when available.

## Configuration (environment)

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | Cloud chat completions |
| `OPENAI_BASE_URL` | API base (default OpenAI) |
| `OPENAI_MODEL` | Model name (default `gpt-4o-mini`) |
| `WATERLOO_OLLAMA_BASE` | Ollama URL (default `http://127.0.0.1:11434`) |
| `WATERLOO_OLLAMA_MODEL` | Ollama model name |
| `WATERLOO_MODE` | Initial mode: `local` (default), `auto`, or `cloud` |
| `WATERLOO_FALLBACK_CLOUD` | If `1`, use cloud when local fails in `auto` for sensitive prompts |
| `WATERLOO_DATA_DIR` | Override data directory |

## Data location

- **macOS**: `~/Library/Application Support/waterloo/`
- **Linux**: `~/.local/share/waterloo/`

Database file: `waterloo.db`. Log lines passed through redaction should not print raw API keys; pasted secrets in chat may still be sent to the configured provider.

## Threat model (v1)

- This CLI can send your prompts to **local Ollama** and/or **OpenAI** depending on mode and routing.
- Long-term **memory** is only what you add with `/remember`.
- No built-in tools (shell, filesystem) in v1.

## Development

```bash
pytest
```
