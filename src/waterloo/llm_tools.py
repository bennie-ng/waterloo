"""OpenAI-style tool definitions for LLM-driven read/run."""

from __future__ import annotations

from typing import Any

OPENAI_TOOLS_SPEC: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Read a UTF-8 text file within the configured workspace sandbox. "
                "Path may be relative to the workspace root or absolute if still inside it."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path relative to workspace or absolute under workspace root",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": (
                "Run a single shell command without shell interpolation; only allowlisted "
                "command prefixes are permitted (e.g. git, ls, pwd). User may need to confirm."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Full command line (first token must be allowlisted)",
                    },
                },
                "required": ["command"],
            },
        },
    },
]
