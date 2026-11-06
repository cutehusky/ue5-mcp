# UE5 MCP: install guide for AI agents

Follow this when a user asks you to install UE5 MCP in their Unreal project. It installs the plugin, the Python server, the skill and the MCP connection. For the guide written for people, see [INSTALL.md](INSTALL.md).

Windows is the tested platform. On macOS or Linux, tell the user it's untested, and use `.venv/bin/python` in place of `.venv/Scripts/python`.

## Rules

- Run the check after each step, and stop and report if it fails. Don't work around a failed build or install.
- Don't commit, and don't delete anything, unless the user asks.
- Ask before closing the Unreal Editor, because the user may have unsaved work.
- Don't change the project's engine version or `Config` files.

## 1. Find the project and check requirements

Set `PROJECT` to the folder holding the user's `.uproject` file. If there's more than one or none, ask. Then check:

| Requirement | How to check | If it fails |
|---|---|---|
| Unreal Engine 5.7 | `EngineAssociation` in the `.uproject` is `5.7`, or the user confirms | Stop and tell the user: other versions are untested |
| C++ project | `PROJECT/Source` exists | Ask the user to add a C++ class with **Tools > New C++ Class**, then continue |
| Python 3.10 to 3.13 | `py -3.13 --version`, then 3.12, 3.11, 3.10. Plain `python` may be an unsupported newer version such as 3.14 | Use the engine's own Python, `<Engine>/Engine/Binaries/ThirdParty/Python3/Win64/python.exe` (3.11 on 5.7.1). Check its version first. If that's missing, ask the user to install one |
| Visual Studio 2022 with C++ game tools | Needed by step 3 | The build in step 3 will report it |

Set `PY` to a working interpreter command, such as `py -3.12`.

## 2. Add the plugin

If `PROJECT/Plugins/UE5_MCP/UE5_MCP.uplugin` already exists, skip this step. If it is a Git checkout and the user wants an update, run `git pull` in it.

```bash
cd "$PROJECT/Plugins"   # Create Plugins first if it doesn't exist.
git clone https://github.com/cutehusky/ue5-mcp.git UE5_MCP
```

**Check:** `PROJECT/Plugins/UE5_MCP/UE5_MCP.uplugin` exists.

## 3. Build the plugin

The editor must be closed. Ask the user first if it's open. Replace `<Engine>` with the Unreal 5.7 install folder, and `<Name>` with the `.uproject` file's name without its extension. Ask the user if you can't find the engine.

```bash
"<Engine>/Engine/Build/BatchFiles/Build.bat" <Name>Editor Win64 Development -Project="$PROJECT/<Name>.uproject" -WaitMutex
```

This can take several minutes, so run it in the background if you can.

**Check:** the output ends with `Result: Succeeded`. If it fails, show the user the first `error` lines.

## 4. Install the Python server

```bash
cd "$PROJECT/Plugins/UE5_MCP/Python/MCP"
$PY -m venv .venv
.venv/Scripts/python -m pip install --upgrade pip
.venv/Scripts/python -m pip install -e .
```

**Check:** this prints `ok`.

```bash
.venv/Scripts/python -c "import mcp, httpx, dotenv; print('ok')"
```

## 5. Add the skill

```bash
mkdir -p "$PROJECT/.claude/skills"
cp -r "$PROJECT/Plugins/UE5_MCP/skills/ue5-python-scripting" "$PROJECT/.claude/skills/"
```

For a client other than Claude, skip this step and tell the user about `Plugins/UE5_MCP/skills/ue5-python-scripting/SKILL.md`.

**Check:** `PROJECT/.claude/skills/ue5-python-scripting/SKILL.md` exists.

## 6. Add the MCP server

Print the exact setup for this machine:

```bash
cd "$PROJECT/Plugins/UE5_MCP/Python/MCP"
.venv/Scripts/python mcp_server.py --claude-config --ue-api-url http://localhost:8080
```

Then, depending on the client you are running in:

- **Claude Code:** run the `claude mcp add` command it printed.
- **Claude Desktop:** merge the printed `ue5` entry into `mcpServers` in `claude_desktop_config.json`. Keep the existing entries, and tell the user to restart the app. On Windows the file is usually `%APPDATA%\Claude\claude_desktop_config.json`.
- **Other clients that launch a command:** use the same command, arguments and `env` from the printed JSON, in that client's settings.
- **Clients that only use a URL:** the user must start the server with `.venv/Scripts/python mcp_server.py --port 9000 --ue-api-url http://localhost:8080`, then connect to `http://localhost:9000/mcp`.

The configuration holds absolute paths, so don't commit it to a shared repository.

**Check:** this ends with `Stdio client verified`. It starts the server the way a client does, and doesn't need the editor.

```bash
cd tests
PYTHONPATH=.. ../.venv/Scripts/python test_stdio_client.py
```

Your own session usually can't see a new MCP server until the client restarts, so don't expect its tools to appear yet.

## 7. Check against the editor

Ask the user to open the project, or start it yourself if they agree:

```bash
"<Engine>/Engine/Binaries/Win64/UnrealEditor.exe" "$PROJECT/<Name>.uproject" -UE5MCPApiPort=8080
```

The fixed port must match step 6. If the user starts the API from **Window > UE5_MCP** instead, they must turn off **Use automatic port allocation** and set port 8080.

**Check:** once the editor has loaded, this prints the project name.

```bash
cd "$PROJECT/Plugins/UE5_MCP/Python/MCP"
.venv/Scripts/python -c "from ue5_client import ue; print(ue.get_ue_editor_status()['project_name'])"
```

## 8. Report to the user

Say what was installed and which checks passed, and name anything skipped. Tell them to:

1. Restart the AI client so it loads the server and skill.
2. Start the editor with `-UE5MCPApiPort=8080` each time, or set that port in **Window > UE5_MCP**.

Mention that these tools can change and delete project content, and that `execute_console_command` can change almost anything in the editor, so they should use source control.

## If something fails

| Symptom | Likely cause and fix |
|---|---|
| `Requires-Python` or a `pip install` error | Wrong Python version. Delete the `.venv` you just created and repeat step 4 with 3.10 to 3.13 |
| Build error about a missing toolchain | Ask the user to install Visual Studio 2022 with the C++ game development workload |
| Build error that a target can't be found | The project has no C++ module, or `<Name>` is wrong. See step 1 |
| Build says files are locked | The editor is still open. Ask the user to close it |
| `Unreal Editor is not reachable` | The editor isn't open, the API isn't on, or the port differs from step 6 |
| Client shows the server as failed | Rerun `--claude-config` and compare the paths with the client's configuration |
