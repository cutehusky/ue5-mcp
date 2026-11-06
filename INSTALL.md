# Installing UE5 MCP

To have an AI agent do this for you, ask it to follow [AGENT_INSTALL.md](AGENT_INSTALL.md).

UE5 MCP has two parts, and both must be running:

- **The Unreal plugin**, which runs inside the editor and serves a local API.
- **The Python MCP server**, which your AI client connects to.

```text
AI client  -->  Python MCP server (port 9000)  -->  Unreal plugin (port 8080)  -->  Unreal Editor
```

## Before you start

| You need | Notes |
|---|---|
| Unreal Engine 5.7 | Built and tested on 5.7.1 |
| Visual Studio 2022 with the **Game development with C++** workload | The plugin ships as source, so it must be compiled |
| A C++ Unreal project | For a Blueprint-only project, first add a C++ class with **Tools > New C++ Class** |
| Python 3.10 to 3.13 | 3.14 is not supported. Check with `python --version` |
| Git | Or download the repository as a ZIP |

Development and testing happen on Windows. macOS and Linux are untested, and the commands below use Windows paths.

## 1. Add the plugin

Close the Unreal Editor, then clone the repository into your project's `Plugins` folder. Create that folder if it doesn't exist.

```bash
cd <YourProject>/Plugins
git clone https://github.com/cutehusky/ue5-mcp.git UE5_MCP
```

The result should be `<YourProject>/Plugins/UE5_MCP/UE5_MCP.uplugin`.

## 2. Build the plugin

Open your `.uproject` file. When Unreal asks to rebuild the missing modules, click **Yes**. The first build can take several minutes.

If that build fails, right-click the `.uproject` file, choose **Generate Visual Studio project files**, and build the project in Visual Studio to see the full error.

Then check that **UE5_MCP** is enabled in **Edit > Plugins**. The engine plugins it depends on, such as Niagara, PCG and StateTree, are enabled with it.

## 3. Install the Python server

```bash
cd <YourProject>/Plugins/UE5_MCP/Python/MCP
python -m venv .venv
.venv/Scripts/python -m pip install --upgrade pip
.venv/Scripts/python -m pip install -e .
```

## 4. Start both parts

**From the editor (easiest):**

1. Open **Window > UE5_MCP**.
2. Set the Python executable to `<YourProject>/Plugins/UE5_MCP/Python/MCP/.venv/Scripts/python.exe`.
3. Set the script to `<YourProject>/Plugins/UE5_MCP/Python/MCP/mcp_server.py`, and the MCP port to `9000`.
4. Click **Run Python MCP server**. This also starts the Unreal API.

**From a terminal (if you want fixed ports):**

Start the editor with the API on port 8080:

```bash
UnrealEditor.exe "<YourProject>/<YourProject>.uproject" -UE5MCPApiPort=8080
```

Then start the server:

```bash
.venv/Scripts/python mcp_server.py --port 9000 --ue-api-url http://localhost:8080
```

The server is ready when it prints `StreamableHTTP session manager started`.

## 5. Connect your AI client

### Claude Code and Claude Desktop

Claude starts the server itself, so you don't need the server from step 4, only the editor and its API. Use a fixed API port: start the editor with `-UE5MCPApiPort=8080`, or turn off **Use automatic port allocation** in **Window > UE5_MCP**.

Print the setup with your real paths:

```bash
.venv/Scripts/python mcp_server.py --claude-config --ue-api-url http://localhost:8080
```

- **Claude Code:** run the `claude mcp add` command it prints.
- **Claude Desktop:** merge the JSON it prints into `claude_desktop_config.json`, opened from **Settings > Developer > Edit Config**, then restart Claude Desktop.

### Other clients

Start the server as in step 4, and connect to `http://localhost:9000/mcp`. Any client that supports streamable HTTP can use it. For example, **Cursor** uses this in `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "ue5": { "url": "http://localhost:9000/mcp" }
  }
}
```

## 6. Check that it works

Check the plugin (needs the fixed port 8080 from the terminal option):

```bash
curl http://localhost:8080/editor/status
```

You should see JSON with `engine_version` and your `project_name`.

Then ask your AI client to run `get_ue_editor_status`. If that returns the same details, everything is connected.

## Optional: let agents script the editor

Agents can call the tools directly from Python instead of through MCP, which suits long or repetitive work. To give Claude the instructions, copy the skill into your project:

```bash
cp -r <YourProject>/Plugins/UE5_MCP/skills/ue5-python-scripting <YourProject>/.claude/skills/
```

The skill covers `ue5_client.py`. [FEATURE_MAP.md](FEATURE_MAP.md) shows which Python file holds each feature.

## Optional settings

Instead of passing flags, you can put the values in `Python/MCP/.env`. Flags take priority.

```env
PORT=9000
UE5_REST_API_URL=http://localhost:8080
```

| Option | Effect |
|---|---|
| `--transport stdio` | Talk over stdin and stdout, for clients that launch the server. The default is `http` |
| `--all-tools` | Lists all 1,700+ tools, which costs about 440k tokens. By default clients see a core set and find the rest with `find_tools` |
| `UE5_MCP_VENV` | Use a different virtual environment folder |
| `UE5_MCP_AUTO_INSTALL=0` | Stop `mcp_server.py` installing missing packages |
| `-EnablePlugins=Spatialization` | Editor flag, needed by some sound attenuation and audio component features |

## Troubleshooting

| Problem | What to do |
|---|---|
| "Missing or built with a different engine version" | Accept the rebuild, or build in Visual Studio. Check that the project uses Unreal 5.7 |
| No rebuild prompt, and the plugin is missing | The project is probably Blueprint-only. Add a C++ class, then try again |
| Client reports `Unreal Editor is not reachable` | Check that the editor is open and the API is running, and that `--ue-api-url` uses the right port |
| Claude shows the server as failed | Rerun `--claude-config` and use its paths. The JSON must escape backslashes, as printed. Check that the `.venv` still exists |
| Client can't connect to the server | Check that the Python server is still running on the port you set, and that the address ends in `/mcp` |
| `pip install` fails on the Python version | Use Python 3.10 to 3.13 |
| Port already in use | Pick another port with `--port` or `-UE5MCPApiPort` |
| Breakpoints or `move_play_mouse` are refused | They need a windowed editor, not `-nullrhi` |

## Security

These tools can create, change and delete project content, and `execute_console_command` can change almost anything in the editor. Use source control, and only connect AI clients you trust.

## Updating

Close the editor, then run:

```bash
cd <YourProject>/Plugins/UE5_MCP
git pull
```

Reopen the project and accept the rebuild. If dependencies changed, run the `pip install -e .` step again.

## Uninstalling

Close the editor, delete `<YourProject>/Plugins/UE5_MCP`, and remove any `UE5_MCP` entry from your `.uproject` file. Then remove the server from your AI client's settings.
