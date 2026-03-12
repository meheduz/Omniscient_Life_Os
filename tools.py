"""
Omniscient Agent - Function Calling (The Hands)
Tool implementations for Gemini Live API.
"""

from __future__ import annotations

import subprocess
import shlex
from pathlib import Path
from typing import Any

from config import ALLOWED_EXECUTABLES as CONFIG_ALLOWED_EXECUTABLES, COMMAND_TIMEOUT
from memory import save_memory as _save_memory, search_memory as _search_memory


# Allowed command executables for safe terminal execution
ALLOWED_EXECUTABLES = set(CONFIG_ALLOWED_EXECUTABLES)
_CURRENT_WORKDIR = Path.cwd()


def _is_command_allowed(command: str) -> bool:
    """Check if command is allowed (cd, python/python3, g++, ./a.out)."""
    try:
        parts = shlex.split(command)
    except ValueError:
        return False
    if not parts:
        return False
    if parts[0] == "cd":
        return len(parts) >= 2
    if parts[0] in ALLOWED_EXECUTABLES:
        return True
    return False


def execute_terminal(command: str) -> dict[str, Any]:
    """
    Safely run terminal commands. Allowed: cd, python/python3 scripts,
    g++ compilation, ./a.out execution.
    Returns dict with stdout, stderr, returncode.
    """
    if not _is_command_allowed(command):
        return {
            "stdout": "",
            "stderr": f"Command not allowed. Only cd, python scripts, g++, and ./a.out are permitted.",
            "returncode": -1,
        }

    try:
        parts = shlex.split(command)
    except ValueError as e:
        return {"stdout": "", "stderr": f"Invalid command syntax: {e}", "returncode": -1}

    if not parts:
        return {"stdout": "", "stderr": "Empty command.", "returncode": -1}

    global _CURRENT_WORKDIR
    if parts[0] == "cd":
        target_str = parts[1]
        target = Path(target_str).expanduser()
        if not target.is_absolute():
            target = (_CURRENT_WORKDIR / target).resolve()
        if not target.exists():
            return {"stdout": "", "stderr": f"Directory not found: {target}", "returncode": -1}
        if not target.is_dir():
            return {"stdout": "", "stderr": f"Not a directory: {target}", "returncode": -1}
        _CURRENT_WORKDIR = target
        return {
            "stdout": f"Changed directory to: {_CURRENT_WORKDIR}",
            "stderr": "",
            "returncode": 0,
        }

    try:
        result = subprocess.run(
            parts,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT,
            cwd=str(_CURRENT_WORKDIR),
        )
        return {
            "stdout": result.stdout or "",
            "stderr": result.stderr or "",
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": f"Command timed out after {COMMAND_TIMEOUT} seconds.",
            "returncode": -1,
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "returncode": -1,
        }


def save_memory(fact: str, collection=None) -> str:
    """Save a fact to ChromaDB. Returns document ID."""
    return _save_memory(fact, collection)


def search_memory(query: str, n_results: int = 5, collection=None) -> list[dict]:
    """Search ChromaDB for relevant past context."""
    return _search_memory(query, n_results, collection)


# Build Gemini Live API tools (types.Tool with FunctionDeclarations)
def get_gemini_tools():
    """Return types.Tool list for LiveConnectConfig."""
    from google.genai import types

    return [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="execute_terminal",
                    description="Run a terminal command. Allowed: cd (directory navigation), python/python3 (run Python scripts), g++ (compile C++), ./a.out (run compiled binary). Returns stdout and stderr.",
                    parameters_json_schema={
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "The shell command to execute (e.g., 'cd /tmp', 'python plot.py', 'g++ main.cpp -o a.out', './a.out')",
                            },
                        },
                        "required": ["command"],
                    },
                ),
                types.FunctionDeclaration(
                    name="save_memory",
                    description="Save a fact or piece of information to long-term memory. Use for: meals eaten, research notes, habits, sleep schedule, diet goals, project context, etc.",
                    parameters_json_schema={
                        "type": "object",
                        "properties": {
                            "fact": {
                                "type": "string",
                                "description": "The fact or information to store (e.g., 'User ate biryani for lunch', 'User is modeling short-range artillery trajectories')",
                            },
                        },
                        "required": ["fact"],
                    },
                ),
                types.FunctionDeclaration(
                    name="search_memory",
                    description="Search long-term memory for past context. Use to answer questions about habits, past meals, research notes, sleep schedule, diet goals, etc.",
                    parameters_json_schema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query (e.g., 'diet goals', 'past meals', 'sleep schedule')",
                            },
                            "n_results": {
                                "type": "integer",
                                "description": "Number of results to return (default 5)",
                            },
                        },
                        "required": ["query"],
                    },
                ),
            ]
        )
    ]
