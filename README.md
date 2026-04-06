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
| `/read <path>` | Read a UTF-8 file under `WATERLOO_TOOL_ROOT` (see tools below) |
| `/run <command>` | Run one allowlisted command (prompts unless auto-approved) |
| `/remember <text>` | Store an opt-in long-term memory note |
| `/forget <id>` | Delete a memory note by id |
| `/memories` | List stored notes |
| `/clear` | Clear messages in the current conversation (not memory notes) |
| `/export` | Print paths to SQLite database and tool root |
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
| `WATERLOO_TOOL_ROOT` | Directory boundary for `/read` paths and working directory for `/run` (default: `~/waterloo-ws`, created if missing) |
| `WATERLOO_MAX_READ_BYTES` | Max bytes for `/read` (default `262144`) |
| `WATERLOO_ALLOW_COMMANDS` | Comma-separated list of allowed command **first tokens** for `/run` (default: `git,ls,pwd,which,echo,wc,head`) |
| `WATERLOO_TOOLS_LOCAL_ONLY` | If `1` (default), `/read` and `/run` only when `/mode local` |
| `WATERLOO_AUTO_APPROVE_TOOLS` | If `1`, skip the confirmation prompt before `/run` |

## Phase 2 tools (guarded)

Default workspace folder for `/read` and `/run` is **`~/waterloo-ws`** (unless you set `WATERLOO_TOOL_ROOT`). The app creates that directory on demand if it does not exist.

- **`/read`**: resolves the path to stay under `WATERLOO_TOOL_ROOT`, then reads a UTF-8 file up to `WATERLOO_MAX_READ_BYTES`.
- **`/run`**: runs a single argv via `subprocess` with **no shell** (`shell=False`). The first token after parsing must be in `WATERLOO_ALLOW_COMMANDS`. You get a **y/n** prompt unless `WATERLOO_AUTO_APPROVE_TOOLS=1`.
- With **`WATERLOO_TOOLS_LOCAL_ONLY=1`** (default), tools are disabled in `cloud` and `auto` modes so chat can use the API without accidental local execution. Use `/mode local` for tools, or set `WATERLOO_TOOLS_LOCAL_ONLY=0` if you accept that risk.

## Data location

- **macOS**: `~/Library/Application Support/waterloo/`
- **Linux**: `~/.local/share/waterloo/`

Database file: `waterloo.db`. Log lines passed through redaction should not print raw API keys; pasted secrets in chat may still be sent to the configured provider.

## Threat model

- This CLI can send your prompts to **local Ollama** and/or **OpenAI** depending on mode and routing.
- Long-term **memory** is only what you add with `/remember`.
- **`/read` and `/run`** only access or execute what you allow: path sandbox under `WATERLOO_TOOL_ROOT`, allowlisted command prefixes, and (by default) **local mode only**. Misconfiguration or setting `WATERLOO_TOOLS_LOCAL_ONLY=0` can widen exposure.

## Development

```bash
pytest
```
