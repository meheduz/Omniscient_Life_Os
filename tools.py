"""
Omniscient Agent - Function Calling (The Hands)
Tool implementations for Gemini Live API.
"""

from __future__ import annotations

import subprocess
import re
from typing import Any

from memory import save_memory as _save_memory, search_memory as _search_memory


# Allowed command patterns for safe terminal execution
ALLOWED_PATTERNS = [
    r"^\s*cd\s+",           # cd /path
    r"^\s*python\s+",        # python script.py
    r"^\s*python3\s+",       # python3 script.py
    r"^\s*g\+\+\s+",         # g++ file.cpp
    r"^\s*\./a\.out",        # ./a.out
    r"^\s*\./a\.out\s",      # ./a.out with args
]


def _is_command_allowed(command: str) -> bool:
    """Check if command matches allowed patterns (cd, python, g++, ./a.out)."""
    cmd_stripped = command.strip()
    if not cmd_stripped:
        return False
    for pattern in ALLOWED_PATTERNS:
        if re.match(pattern, cmd_stripped, re.IGNORECASE):
            return True
    # Exact match for ./a.out
    if cmd_stripped == "./a.out":
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
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=None,  # Uses current working directory
        )
        return {
            "stdout": result.stdout or "",
            "stderr": result.stderr or "",
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": "Command timed out after 60 seconds.",
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
