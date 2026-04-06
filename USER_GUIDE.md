# Waterloo user guide

Waterloo is a **terminal assistant**: you type messages at the `you>` prompt, and it replies using a **local** AI (Ollama) and/or a **cloud** API (OpenAI-compatible), depending on how you configure it. Your chat history and optional notes are stored **on your computer** in a small SQLite database.

This guide is for **people using Waterloo**, not for contributors changing the code. Developer setup (tests, packaging) lives in [README.md](README.md).

---

## What you need

- **Python 3.11 or newer**
- For **local** chat (recommended default): [Ollama](https://ollama.com/) installed and running, with at least one model pulled (for example `llama3.2`).
- For **cloud** chat: an API key for an OpenAI-compatible service (often OpenAI), set in your environment.

---

## Install and first run

From the folder that contains the Waterloo project:

```bash
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -e .
```

Start the app:

```bash
waterloo
```

You can also run:

```bash
python -m waterloo
```

When it starts, you should see a short **Ready** panel with the **workspace** root, **data** directory (where the database lives), and the current **mode** (`local`, `cloud`, or `auto`).

Type a normal sentence and press Enter to chat. Commands that start with `/` are special (see below).

Exit with `/quit`, or press **Ctrl+C** or **Ctrl+D**.

---

## Choosing where the AI runs: modes

Waterloo can send your message to **Ollama on your machine** or to a **cloud API**. You control that with **mode**:


| Mode      | What it does                                                                                      |
| --------- | ------------------------------------------------------------------------------------------------- |
| **local** | Uses Ollama (default). Good for privacy and offline use when Ollama is running.                   |
| **cloud** | Uses the configured cloud API. Needs `OPENAI_API_KEY` (and network). Often stronger models.       |
| **auto**  | Tries to route “sensitive” phrasing to local and other messages to cloud when both are available. |


Change mode anytime:

```text
/mode local
/mode cloud
/mode auto
```

You can set a starting mode when you launch:

```bash
export WATERLOO_MODE=cloud
waterloo
```

**Tools** (`/read` and `/run`, see below) are only available in **local** mode unless you change advanced settings. If a tool says you need local mode, run `/mode local` first.

---

## Slash commands (reference)

Anything starting with `/` is a command, not a message to the AI.


| Command                            | What it does                                                        |
| ---------------------------------- | ------------------------------------------------------------------- |
| `/help`                            | List commands                                                       |
| `/health`                          | Check Ollama, cloud API key, and calendar configuration             |
| `/mode local` or `cloud` or `auto` | Set routing mode                                                    |
| `/calendar`                        | Show upcoming events from your configured calendar file or URL      |
| `/mail`                            | Show status of the mail feature (placeholder today)                 |
| `/read <path>`                     | Read a text file inside your workspace (see “Workspace and tools”)  |
| `/run <command>`                   | Run one allowed command (you confirm unless configured otherwise)   |
| `/remember <text>`                 | Save a long-term note Waterloo may use in later replies             |
| `/memories`                        | List saved notes                                                    |
| `/forget <id>`                     | Delete a note by its number from `/memories`                        |
| `/clear`                           | Clear the **current chat transcript** (notes from `/remember` stay) |
| `/export`                          | Show workspace root, database path, and tool sandbox path           |
| `/quit`                            | Exit Waterloo                                                       |


Shortcuts: `/exit` and `/q` also quit.

---

## Model-driven tools (LLM tool loop)

When you are in **`/mode local`** (and tools are not restricted by `WATERLOO_TOOLS_LOCAL_ONLY`), Waterloo sends tool definitions to the model so it can **`read_file`** and **`run_command`** on its own, using the same rules as the **`/read`** and **`/run`** slash commands (sandbox, allowlist, confirmations).

- A dim `tool read_file` or `tool run_command` line may appear when a tool runs.
- Set **`WATERLOO_LLM_TOOLS=0`** if you want **chat only** with no automatic tool use.
- **`WATERLOO_AGENT_MAX_STEPS`** caps how many tool rounds can happen per message (default **8**).
- The saved chat history shows **final replies**, not every tool step.

## Workspace layout

By default, Waterloo uses a single **workspace** directory ( **`~/.waterloo`**, or **`WATERLOO_WORKSPACE`** if you set it). Typical layout:

| Subfolder | Purpose |
|-----------|---------|
| `data/` | SQLite database (`waterloo.db`) |
| `sandbox/` | Files and cwd for **`/read`**, **`/run`**, and LLM tools |
| `ical/` | Optional default calendar file `calendar.ics` |

You can override individual locations with **`WATERLOO_DATA_DIR`**, **`WATERLOO_TOOL_ROOT`**, or **`WATERLOO_ICAL_PATH`** without changing the rest.

## Workspace and tools (`/read` and `/run`)

Waterloo can **read files** and **run a small set of shell commands**, but only inside the **sandbox** (`<workspace>/sandbox` by default).

- **Override:** set **`WATERLOO_TOOL_ROOT`** to use a different directory.

**`/read notes.txt`** reads a file **relative to that folder**, or you can use an absolute path **as long as it still lies inside** the sandbox.

**`/run`** runs a single command **without** a full shell. Only commands whose **first word** is on the allowlist are allowed (by default things like `git`, `ls`, `pwd`, `echo`, …). You can change the list with `WATERLOO_ALLOW_COMMANDS`. Before running, Waterloo asks you to confirm unless you set `WATERLOO_AUTO_APPROVE_TOOLS=1`.

If tools say they need **local** mode, run `/mode local` first (or read the section on `WATERLOO_TOOLS_LOCAL_ONLY` in the configuration table below).

---

## Memory (`/remember`)

Waterloo can inject **short reminders** into the conversation when your message **matches** saved notes (simple keyword overlap, not a full search engine).

- **`/remember I prefer dark mode`** saves a note.
- **`/memories`** lists notes with **id** numbers.
- **`/forget 3`** deletes the note numbered 3.

Only text **you** save with `/remember` is stored as long-term memory; Waterloo does not silently index your whole disk.

---

## Calendar (`/calendar`)

You can attach a **read-only calendar** in standard **iCalendar (.ics)** form.

1. Use **one** of:
   - Drop **`calendar.ics`** into **`<workspace>/ical/`** (default workspace is `~/.waterloo`), **or**
   - Set **`WATERLOO_ICAL_PATH`** to any `.ics` file on disk, **or**
   - Set **`WATERLOO_ICAL_URL`** to an **`https://`** link that returns an `.ics` file.
2. Start Waterloo and run **`/calendar`**.

You will see up to **20** non-recurring events in the next **14 days**. Recurring events (`RRULE`) are not expanded yet.

**Privacy:** many “secret” calendar links embed a private token in the URL. Treat those like passwords: use environment variables, do not paste them into public chats, and do not commit them to git.

---

## Mail (`/mail`)

Mail integration is **not implemented** yet. The `/mail` command explains that and points you to future documentation. No mailbox is accessed today.

---

## Configuration cheat sheet

These environment variables are read when Waterloo starts. Use your shell profile or a small wrapper script if you want them every time.


| Variable                                   | Purpose                                                                         |
| ------------------------------------------ | ------------------------------------------------------------------------------- |
| `OPENAI_API_KEY`                           | Enables cloud chat when set                                                     |
| `OPENAI_BASE_URL`                          | Optional; default is OpenAI’s API                                               |
| `OPENAI_MODEL`                             | Cloud model name (default `gpt-4o-mini`)                                        |
| `WATERLOO_OLLAMA_BASE`                     | Ollama address (default `http://127.0.0.1:11434`)                               |
| `WATERLOO_OLLAMA_MODEL`                    | Ollama model name (default `llama3.2`)                                          |
| `WATERLOO_MODE`                            | Initial mode: `local`, `cloud`, or `auto`                                       |
| `WATERLOO_WORKSPACE`                       | Root folder for default paths (default `~/.waterloo`)                            |
| `WATERLOO_DATA_DIR`                        | Override database directory (default `<workspace>/data`)                        |
| `WATERLOO_TOOL_ROOT`                       | Override sandbox for `/read` and `/run` (default `<workspace>/sandbox`)        |
| `WATERLOO_TOOLS_LOCAL_ONLY`                | If `1` (default), tools only in `/mode local`                                   |
| `WATERLOO_ALLOW_COMMANDS`                  | Comma-separated allowed first words for `/run`                                  |
| `WATERLOO_AUTO_APPROVE_TOOLS`              | If `1`, skip confirmation before `/run`                                         |
| `WATERLOO_ICAL_PATH` / `WATERLOO_ICAL_URL` | Calendar `.ics` path or HTTPS URL (optional default: `<workspace>/ical/calendar.ics`) |
| `WATERLOO_FALLBACK_CLOUD`                  | In `auto`, whether to use cloud when local is unavailable for sensitive prompts |
| `WATERLOO_LLM_TOOLS`                       | Set `0` to disable model-driven `read_file` / `run_command`                     |
| `WATERLOO_AGENT_MAX_STEPS`                 | Max tool rounds per message (default `8`)                                       |


---

## Where your data is stored

By default, the database is **`~/.waterloo/data/waterloo.db`** (under **`WATERLOO_WORKSPACE`**). Older installs may have used OS-specific paths or an earlier default at **`~/waterloo`**; you can set **`WATERLOO_DATA_DIR`**, move your data to **`~/.waterloo`**, or set **`WATERLOO_WORKSPACE`** to keep the old location.

Use **`/export`** inside Waterloo to print the exact workspace, database, and sandbox paths on your machine.

---

## Privacy and safety (short)

- **Local mode** keeps the conversation with Ollama on your machine (Ollama’s own policies still apply).
- **Cloud mode** sends the current conversation (and system text Waterloo adds) to the API provider you configured. Do not paste secrets you are not willing to send there.
- **`/remember`** only stores what you explicitly save.
- **Tools** only read or run what the sandbox and allowlists permit, and by default only in **local** mode.

---

## Troubleshooting


| Problem                             | What to try                                                                                             |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------- |
| “No provider” or Ollama errors      | Run `ollama serve` (or start the Ollama app), then `/health`. Pull a model: `ollama pull llama3.2`.     |
| Cloud mode fails                    | `export OPENAI_API_KEY=...`, check network, try `/health`.                                              |
| `/read` or `/run` refused           | Use `/mode local`, or set `WATERLOO_TOOLS_LOCAL_ONLY=0` only if you understand the risk.                |
| `/calendar` empty or errors         | Check `WATERLOO_ICAL_PATH` / `WATERLOO_ICAL_URL`, ensure HTTPS for URLs, try a known-good `.ics` file.  |
| Wrong or missing files from `/read` | Paths must stay under the tool sandbox (default `<workspace>/sandbox`). Put files there or set `WATERLOO_TOOL_ROOT`. |


---

## Getting more help

- In the app: `/help`
- Project overview and developer install: [README.md](README.md)

