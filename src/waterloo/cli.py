"""Interactive CLI / REPL."""

from __future__ import annotations

import logging

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from waterloo import __version__
from waterloo import config as cfg
from waterloo.logging_utils import redact_secrets
from waterloo.memory import (
    add_memory_note,
    append_message,
    clear_messages,
    connect,
    delete_memory_note,
    init_schema,
    list_memory_notes,
    load_messages,
    recall_notes_for_query,
)
from waterloo.providers import ChatProvider, OllamaProvider, OpenAICompatibleProvider
from waterloo.router import Mode, decide_route

log = logging.getLogger("waterloo")

SYSTEM_PERSONA = (
    "You are Waterloo, a concise and capable terminal assistant inspired by a JARVIS-style aide. "
    "Be direct, avoid filler, and ask clarifying questions when needed."
)


def _parse_mode_arg(arg: str) -> Mode | None:
    a = arg.lower().strip()
    if a in {"auto", "local", "cloud"}:
        return a  # type: ignore[return-value]
    return None


def _check_ollama(provider: OllamaProvider) -> tuple[bool, str]:
    import httpx

    try:
        url = f"{provider.base_url}/api/tags"
        with httpx.Client(timeout=5.0) as client:
            r = client.get(url)
            r.raise_for_status()
        return True, "Ollama reachable"
    except Exception as e:
        return False, f"Ollama: {redact_secrets(str(e))}"


def _check_cloud(key: str | None) -> tuple[bool, str]:
    if not key:
        return False, "OPENAI_API_KEY not set"
    return True, "OPENAI_API_KEY present"


def build_system_content(memory_snippets: list[str]) -> str:
    parts = [SYSTEM_PERSONA]
    if memory_snippets:
        joined = "\n".join(f"- {s}" for s in memory_snippets)
        parts.append("User-approved memory (may be incomplete):\n" + joined)
    return "\n\n".join(parts)


def run_repl() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    console = Console(highlight=False)

    data_dir = cfg.data_dir()
    dbp = cfg.db_path()
    conn = connect(dbp)
    init_schema(conn)

    conversation_id = "default"

    ollama = OllamaProvider(cfg.ollama_base(), cfg.ollama_model())
    cloud_key = cfg.openai_api_key()
    cloud: ChatProvider | None
    if cloud_key:
        cloud = OpenAICompatibleProvider(cloud_key, cfg.openai_base_url(), cfg.openai_model())
    else:
        cloud = None

    mode: Mode = cfg.initial_mode()  # type: ignore[assignment]
    fallback = cfg.fallback_cloud_enabled()

    console.print(
        Panel.fit(
            f"[bold]Waterloo[/bold] {__version__}\nData: {dbp}\nMode: {mode} (/mode to change)",
            title="Ready",
        )
    )

    while True:
        try:
            line = console.input("[bold cyan]you>[/bold cyan] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\nBye.")
            return 0

        if not line:
            continue

        if line.startswith("/"):
            parts = line.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""

            if cmd in {"/quit", "/exit", "/q"}:
                console.print("Bye.")
                return 0

            if cmd == "/help":
                console.print(
                    "[bold]Commands[/bold]\n"
                    "/mode local|cloud|auto — routing\n"
                    "/health — providers\n"
                    "/remember <text> — save a note\n"
                    "/memories — list notes\n"
                    "/forget <id> — delete note\n"
                    "/clear — clear this chat transcript\n"
                    "/export — show DB path\n"
                    "/quit — exit"
                )
                continue

            if cmd == "/mode":
                m = _parse_mode_arg(arg)
                if not m:
                    console.print("Usage: /mode local|cloud|auto")
                    continue
                mode = m
                console.print(f"Mode set to [bold]{mode}[/bold]")
                continue

            if cmd == "/health":
                ok_o, msg_o = _check_ollama(ollama)
                ok_c, msg_c = _check_cloud(cloud_key)
                console.print(f"{'[green]OK[/green]' if ok_o else '[red]NO[/red]'} {msg_o}")
                console.print(f"{'[green]OK[/green]' if ok_c else '[red]NO[/red]'} {msg_c}")
                continue

            if cmd == "/remember":
                if not arg.strip():
                    console.print("Usage: /remember <text>")
                    continue
                nid = add_memory_note(conn, arg.strip())
                console.print(f"Stored memory note [bold]#{nid}[/bold].")
                continue

            if cmd == "/memories":
                notes = list_memory_notes(conn)
                if not notes:
                    console.print("No memory notes.")
                else:
                    for n in notes:
                        console.print(f"[bold]#{n.id}[/bold] {n.content}")
                continue

            if cmd == "/forget":
                if not arg.strip() or not arg.strip().isdigit():
                    console.print("Usage: /forget <id>")
                    continue
                if delete_memory_note(conn, int(arg.strip())):
                    console.print("Deleted.")
                else:
                    console.print("Note not found.")
                continue

            if cmd == "/clear":
                clear_messages(conn, conversation_id)
                console.print("Conversation messages cleared (memory notes kept).")
                continue

            if cmd == "/export":
                console.print(f"SQLite database: {dbp}")
                continue

            console.print(f"Unknown command: {cmd}. Try /help")
            continue

        user_text = line
        local_available, _ = _check_ollama(ollama)
        cloud_available = cloud is not None

        decision = decide_route(
            mode,
            user_text,
            local_available=local_available,
            cloud_available=cloud_available,
            fallback_cloud=fallback,
        )
        console.print(f"[dim]{decision.reason}[/dim]")

        provider: ChatProvider | None
        model_name: str | None
        if decision.backend == "local":
            provider = ollama
            model_name = cfg.ollama_model()
        else:
            provider = cloud
            model_name = cfg.openai_model()

        if provider is None:
            console.print(
                "[red]No provider available. Start Ollama and/or set OPENAI_API_KEY.[/red]"
            )
            continue

        recalled = recall_notes_for_query(conn, user_text)
        system_content = build_system_content(recalled)

        history = load_messages(conn, conversation_id)
        messages: list[dict[str, str]] = [{"role": "system", "content": system_content}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_text})

        append_message(conn, conversation_id, "user", user_text)

        try:
            reply = provider.complete(messages, model=model_name)
        except Exception as e:
            err = redact_secrets(str(e))
            log.info("Completion failed: %s", err)
            console.print(f"[red]Error:[/red] {err}")
            append_message(conn, conversation_id, "assistant", f"[error] {err}")
            continue

        append_message(conn, conversation_id, "assistant", reply)
        console.print(Panel(Markdown(reply), title="waterloo", border_style="green"))

    return 0


def main() -> None:
    raise SystemExit(run_repl())


if __name__ == "__main__":
    main()
