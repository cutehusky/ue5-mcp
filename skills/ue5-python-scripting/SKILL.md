---
name: ue5-python-scripting
description: Drive the Unreal Editor by writing and running Python scripts against the UE5_MCP plugin's tools, instead of many separate MCP tool calls. Use for repetitive or multi-step Unreal work, such as building Blueprint graphs, placing many actors, bulk asset edits or automated playtests, and when an MCP tool you need isn't listed.
---

# Scripting Unreal with UE5_MCP

Every MCP tool is also a Python function. A script can loop, branch and pass results between calls in one run, and only what it prints comes back to you. Prefer a script for more than a few calls or anything repetitive. Use MCP tools for one-off calls, or when you can't run Python on the machine.

## Before you start

The editor must be running with the plugin's API on. Find the folder and check the connection:

- The server folder is `Plugins/UE5_MCP/Python/MCP`. Run scripts with its Python: `.venv/Scripts/python` on Windows, or `.venv-ue311/Scripts/python` if that is the one that exists.
- Set `PYTHONPATH` to that folder if the script is elsewhere.
- Set `UE5_REST_API_URL` if the API isn't on `http://localhost:8080`.
- Keep throwaway scripts outside the project's source folders.

```python
from ue5_client import ue, UE5Error
print(ue.get_ue_editor_status()["project_name"])
```

## Find the right function

Don't read the whole tool list. In order of cost:

1. `ue.find("niagara renderer")` searches names and summaries. Add `feature="niagara"` to narrow it.
2. `print(ue.describe("connect_pins"))` gives the signature, file, line and docs.
3. `Plugins/UE5_MCP/FEATURE_MAP.md` maps each feature to its Python file. `tool_map.json` has every function, for searching with grep.

Read a tool's source only when its docs don't answer the question.

## Calling tools

Replies are parsed into dicts or lists, and a failure raises `UE5Error` with `.message`, `.kind`, `.fix` and `.reply`. Plain values, such as an asset path, come back as they are.

```python
from ue5_client import ue, UE5Error

BP = "/Game/Demo/BP_Door"
ue.create_blueprint(BP, "/Script/Engine.Actor")
r = ue.edit_blueprint_graph(BP, [
    {"id": "start", "tool": "add_event_to_graph", "args": {"event_name": "ReceiveBeginPlay"}},
    {"id": "say", "tool": "add_function_call_to_graph",
     "args": {"function_name": "PrintString", "class_to_call": "/Script/Engine.KismetSystemLibrary"}},
], [["start.then", "say.execute"]], [["say.InString", "Hello"]])
ue.organize_blueprint_graph(BP)
result = ue.compile_blueprint(BP)
if not result["success"]:
    print(result["messages"])          # A failed compile is a result, not an exception.
ue.save_asset(BP)

try:
    ue.connect_pins(BP, "EventGraph", r["nodes"][0]["node_id"], "nope", r["nodes"][1]["node_id"], "execute")
except UE5Error as error:
    print(error.message)               # It names the node and lists its pins.
```

## Things that catch people out

- **Saving:** edits aren't saved until `save_asset` or `save_editor_world`, or a tool's `save=True`.
- **Confirmation:** destructive tools need `confirm=True`, and many take `dry_run=True`. Use a dry run first on anything you can't easily undo.
- **Replies differ from MCP:** direct calls don't add the `id` field, and lists aren't wrapped in `result`. Read `node_id` or the path from the reply.
- **`success` can be false without raising:** `compile_blueprint` is the common case, so check it.
- **Play sessions:** many edits refuse to run during play. Check `is_playing` with `get_ue_editor_status`. Breakpoints and `move_play_mouse` need a windowed editor.
- **Variants:** `kind: "variant"` functions in the map are callable directly by name, without the `variant` argument.

## After scripting

Check the result rather than trusting the script ran: `ue.list_blueprint_errors("/Game/Demo")`, `ue.get_project_errors()`, `ue.get_editor_logs(severity="Error")`, or a playtest with `control_ue_play_session` and `read_play_actor_properties`.

If you add or change a tool in the plugin, run `Python/MCP/gen_tool_docs.py` to refresh the map.
