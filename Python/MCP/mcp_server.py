import os
import json
import argparse
import importlib.util
from pathlib import Path
import subprocess
import sys
from typing import Literal
import venv


def _venv_python(venv_dir: Path) -> Path:
    """Return the platform-specific Python executable inside a venv."""
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _usable_venv(path: Path) -> bool:
    interpreter = _venv_python(path)
    if not interpreter.exists():
        return False
    try:
        subprocess.run(
            [str(interpreter), "-c", "import sys; assert sys.prefix != sys.base_prefix"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def _ensure_virtual_environment():
    """Create/select a project venv and re-run this script inside it."""
    if os.getenv("UE5_MCP_VENV_ACTIVE") == "1":
        return
    if sys.prefix != sys.base_prefix:
        return

    project_dir = Path(__file__).resolve().parent
    requested = os.getenv("UE5_MCP_VENV")
    candidates = [Path(requested)] if requested else [project_dir / ".venv"]

    # Reuse the UE-compatible environment created by the setup workflow when
    # the conventional .venv is unavailable or was created from a deleted
    # interpreter.
    if not requested:
        candidates.append(project_dir / ".venv-ue311")

    target = next((path for path in candidates if _usable_venv(path)), None)
    if target is None:
        target = candidates[0]
        target.parent.mkdir(parents=True, exist_ok=True)
        venv.EnvBuilder(with_pip=True, clear=True).create(target)

    interpreter = _venv_python(target).resolve()
    if interpreter == Path(sys.executable).resolve():
        return

    child_env = os.environ.copy()
    child_env["UE5_MCP_VENV_ACTIVE"] = "1"
    command = [str(interpreter), str(Path(__file__).resolve()), *sys.argv[1:]]
    if os.name == "nt":
        # execve on Windows starts a new process and ends this one, which a client that launched this one sees as an exit.
        sys.exit(subprocess.call(command, env=child_env))
    os.execve(str(interpreter), command, child_env)


_ensure_virtual_environment()


def _ensure_dependencies():
    """Install the small runtime dependency set when this script is run directly.

    UE's bundled Python may not have pip packages installed yet.  Keep this
    opt-out so packaged/offline deployments can fail fast instead.
    """
    if os.getenv("UE5_MCP_AUTO_INSTALL", "1").lower() in {"0", "false", "no", "off"}:
        return

    required = {
        "httpx": "httpx>=0.27,<1",
        "mcp": "mcp>=1.20,<2",
        "dotenv": "python-dotenv>=1,<2",
    }
    missing = [spec for module, spec in required.items()
               if importlib.util.find_spec(module) is None]
    if not missing:
        return

    command = [sys.executable, "-m", "pip", "install", *missing]
    try:
        # stdout carries the MCP protocol in stdio mode, so pip must not write there.
        subprocess.run(command, check=True, stdout=sys.stderr)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(
            "UE5 MCP dependencies are missing and automatic installation failed. "
            f"Run {' '.join(command)} manually or set UE5_MCP_AUTO_INSTALL=0."
        ) from exc


_ensure_dependencies()

import importlib  # noqa: E402
import pkgutil  # noqa: E402
import types  # noqa: E402

import ue5_tools  # noqa: E402
from ue5_tools import app  # noqa: E402

for _module in pkgutil.iter_modules(ue5_tools.__path__):
    _loaded = importlib.import_module(f"ue5_tools.{_module.name}")
    # Keep every tool and helper reachable as mcp_server.<name> for scripts and tests.
    globals().update({k: v for k, v in vars(_loaded).items() if not k.startswith("__") and k != "BASE_URL"})


class _ServerModule(types.ModuleType):
    """Forwards mcp_server.BASE_URL to app.BASE_URL, which is what the tools read."""

    @property
    def BASE_URL(self):
        return app.BASE_URL

    @BASE_URL.setter
    def BASE_URL(self, value):
        app.BASE_URL = value


sys.modules[__name__].__class__ = _ServerModule


def claude_config() -> str:
    """The setup for Claude Code and Claude Desktop, using this machine's paths."""
    command = str(Path(sys.executable).resolve())
    script = str(Path(__file__).resolve())
    env = {"UE5_REST_API_URL": app.BASE_URL}
    desktop = {"mcpServers": {"ue5": {"command": command, "args": [script, "--transport", "stdio"], "env": env}}}
    return (f'Claude Code:\n  claude mcp add ue5 --env UE5_REST_API_URL={app.BASE_URL} -- "{command}" "{script}" --transport stdio\n\n'
            f"Claude Desktop (claude_desktop_config.json):\n{json.dumps(desktop, indent=2)}\n")


async def main():
    if app.args.transport == "stdio":
        await mcp.run_stdio_async()
    else:
        await mcp.run_streamable_http_async()


def run():
    """Console entry point installed by pyproject.toml."""
    import asyncio

    if app.args.claude_config:
        print(claude_config())
        return
    asyncio.run(main())


if __name__ == "__main__":
    run()
