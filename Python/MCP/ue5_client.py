"""Call the Unreal tools directly from a Python script, without an MCP client.

    from ue5_client import ue, UE5Error

    node = ue.add_branch_node_to_graph("/Game/BP_Door", "EventGraph")["node_id"]
    ue.find("niagara renderer")                  # Search every tool.
    print(ue.describe("connect_pins"))           # Signature, file and docs.

Replies come back parsed, and failures raise UE5Error. Calls still go over HTTP to the running editor.
Run with the server's virtual environment, from this folder or with it on PYTHONPATH. Set UE5_REST_API_URL for another port.
"""
import difflib
import inspect
import json
import logging
import os
import sys
from pathlib import Path

MAP_FILE = Path(__file__).resolve().parents[2] / "tool_map.json"


def _load_server():
    # mcp_server restarts itself in a venv, installs packages and reads the command line: all wrong inside someone's script.
    saved_argv, saved_env = sys.argv, {k: os.environ.get(k) for k in ("UE5_MCP_VENV_ACTIVE", "UE5_MCP_AUTO_INSTALL")}
    sys.argv = sys.argv[:1]
    os.environ.update(UE5_MCP_VENV_ACTIVE="1", UE5_MCP_AUTO_INSTALL="0")
    try:
        import mcp_server
    except ImportError as error:
        raise ImportError(f"{error}. Run this script with the UE5_MCP server's virtual environment, Python/MCP/.venv, "
                          "and see INSTALL.md step 3.") from error
    finally:
        sys.argv = saved_argv
        for key, value in saved_env.items():
            os.environ.pop(key, None) if value is None else os.environ.__setitem__(key, value)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    return mcp_server


_server = _load_server()
from ue5_tools import app  # noqa: E402


class UE5Error(RuntimeError):
    """A tool reported failure. message says what is wrong, and fix suggests what to do."""

    def __init__(self, reply: dict):
        self.reply = reply
        self.tool = reply.get("tool", "")
        self.message = reply.get("errorMessage", "")
        self.kind = reply.get("errorKind", "")
        self.fix = reply.get("fix", "")
        super().__init__(f"{self.tool}: {self.message} ({self.fix})")


class Client:
    def __init__(self, url: str = ""):
        self.url = url or app.BASE_URL

    def _map(self) -> dict:
        return json.loads(MAP_FILE.read_text(encoding="utf-8"))["tools"]

    def __getattr__(self, name: str):
        tools = self._map()
        if name not in tools:
            close = difflib.get_close_matches(name, tools, 3)
            raise AttributeError(f"No tool named {name}. Did you mean: {', '.join(close) or 'none close'}? ue.find() searches them all.")
        function = getattr(_server, name)

        def call(*args, **kwargs):
            app.BASE_URL = self.url
            text = app.standard_tool(function)(*args, **kwargs)
            try:
                reply = json.loads(text) if isinstance(text, str) else text
            except ValueError:
                return text
            if isinstance(reply, dict) and reply.get("success") is False and "errorMessage" in reply:
                raise UE5Error(reply)
            return reply
        call.__name__ = name
        call.__doc__ = inspect.getdoc(function)
        return call

    def find(self, query: str = "", feature: str = "", limit: int = 15) -> list[dict]:
        """Search tools by keywords in the name and summary, optionally within one feature."""
        words = query.lower().replace("_", " ").split()
        scored = []
        for name, tool in self._map().items():
            if feature and tool["feature"] != feature:
                continue
            title, summary = name.replace("_", " "), tool["summary"].lower()
            score = sum(3 * (w in title) + (w in summary) for w in words)
            if score or not words:
                scored.append((-score, name, tool))
        return [{"name": name, **tool} for _, name, tool in sorted(scored, key=lambda row: row[:2])[:limit]]

    def describe(self, name: str) -> str:
        """Return a tool's signature, location and full documentation."""
        tool = self._map()[name]
        return f"{name}{tool['signature']}\n{tool['file']}:{tool['line']}\n\n{inspect.getdoc(getattr(_server, name)) or ''}"


ue = Client()
