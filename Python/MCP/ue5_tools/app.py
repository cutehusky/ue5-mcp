"""Shared server state for the tool modules: settings, the FastMCP instance and small request helpers.

Tool modules read app.BASE_URL at call time, so changing it here applies everywhere.
"""
import argparse
import functools
import inspect
import json
import os
import re
import types
import typing
import urllib.parse

import dotenv
import httpx
from mcp.server.fastmcp import FastMCP

# Editor operations such as mesh rebuilds and compiles outlast httpx's 5 s default, which reported failure while the edit
# continued. Calls that pass their own timeout keep it.
def _with_defaults(request):
    """Apply a longer timeout, and send query spaces as %20: the Unreal HTTP server does not decode httpx's +."""
    def run(url, *a, **kw):
        params = kw.pop("params", None)
        if params:
            pairs = {k: "" if v is None else str(v) for k, v in params.items()}
            url = f"{url}?{urllib.parse.urlencode(pairs, quote_via=urllib.parse.quote)}"
        return request(url, *a, **{"timeout": 180, **kw})
    return run


for _verb in ("get", "post", "put", "patch", "delete"):
    setattr(httpx, _verb, _with_defaults(getattr(httpx, _verb)))
_send = _with_defaults(lambda url, *a, **kw: _request(kw.pop("method"), url, *a, **kw))
_request = httpx.request
httpx.request = lambda method, url, *a, **kw: _send(url, *a, method=method, **kw)

dotenv.load_dotenv()

parser = argparse.ArgumentParser(description="UE5 Blueprint MCP server")
parser.add_argument("--port", type=int, help="MCP HTTP port")
parser.add_argument("--ue-api-url", help="Unreal Editor HTTP API URL")
parser.add_argument("--all-tools", action="store_true", help="List every tool instead of the core set and catalog")
parser.add_argument("--transport", choices=("http", "stdio"), default=os.getenv("UE5_MCP_TRANSPORT", "http"),
                    help="http serves --port; stdio is for clients that launch the server, such as Claude")
parser.add_argument("--claude-config", action="store_true", help="Print the setup for Claude Code and Claude Desktop, then exit")
args = parser.parse_args()

PORT = args.port or int(os.getenv("PORT", "9000"))
BASE_URL = args.ue_api_url or os.getenv("UE5_REST_API_URL", "http://localhost:8080")

mcp = FastMCP("UE5BlueprintMCP", port=PORT)


# First match wins. Categories come from each message's wording, so a fix is advice rather than a guarantee.
ERROR_KINDS = (
    ("needs_confirmation", r"confirm", "Inspect the current state, then retry with confirm=True."),
    ("paused_at_breakpoint", r"breakpoint", "Use inspect_blueprint_debug_state, then control_blueprint_debugger to continue."),
    ("stale_state", r"stale|snapshot|fingerprint|expected_", "Read the current value again and retry with it."),
    ("play_state", r"\bPIE\b|play session|play-in-editor", "Check is_playing with get_ue_editor_status, then use control_ue_play_session."),
    ("not_found", r"not found|not a |does not exist|no such|failed to load|could not (load|find)|unknown",
     "Check the name or path with list_assets, get_graph, describe_asset or find_tools."),
    ("unavailable", r"bpluginb|unavailable|not enabled|unsupported|not supported", "This needs an engine feature or plugin that is not available here."),
    ("invalid_argument", r"must|require|invalid|cannot|out of range|exceed", "Correct the arguments; describe_tool shows what this tool accepts."),
)


def _failure(tool: str, message: str, **extra) -> str:
    message = message.removeprefix("Error:").strip()
    kind, fix = next(((k, h) for k, pattern, h in ERROR_KINDS if re.search(pattern, message, re.I)),
                      ("editor_error", "Check get_editor_logs for details."))
    return json.dumps({**extra, "success": False, "tool": tool, "errorMessage": message, "errorKind": kind, "fix": fix})


def standard_result(tool: str, text):
    """Give a tool's reply one shape: objects carry success, and failures also carry errorMessage and the tool name.

    Lists and plain values such as an asset path are returned as they are.
    """
    if not isinstance(text, str):
        return text
    stripped = text.strip()
    if stripped in ("", "OK"):
        return json.dumps({"success": True, "tool": tool})
    if stripped.startswith("Error"):
        return _failure(tool, stripped)
    try:
        data = json.loads(stripped)
    except ValueError:
        return text
    if not isinstance(data, dict):
        return text
    nested = data.get("error")
    if "errorMessage" in data or (isinstance(nested, dict) and "message" in nested):
        return _failure(tool, data.get("errorMessage") or nested["message"], **{k: v for k, v in data.items() if k != "tool"})
    if not data:
        return json.dumps({"success": True, "tool": tool})
    return json.dumps({"success": True, **data})


def standard_tool(fn):
    """Wrap a tool so its reply has the standard shape and an unreachable editor is a result the caller can act on."""
    @functools.wraps(fn)
    def run(*a, **kw):
        try:
            return standard_result(fn.__name__, fn(*a, **kw))
        except httpx.ConnectError:
            message = f"Unreal Editor is not reachable at {BASE_URL}. Start the editor with the UE5_MCP plugin enabled."
        except httpx.TimeoutException:
            message = "The editor did not answer in time. It may still be working; check get_ue_editor_status before retrying."
        return json.dumps({"success": False, "tool": fn.__name__, "errorMessage": message, "errorKind": "editor_unavailable",
                           "fix": "Retry after the editor responds to get_ue_editor_status."})
    return run


CREATE_TOOL = re.compile(r"(create|add|spawn|duplicate|import|place|insert|copy|upsert)_")
_NOT_THE_ITEM = re.compile(r"parent|source|previous|expected|old|template|version|transaction|session|request|snapshot")
_REPLY_ID = re.compile(r"id|guid|.*_id|.*_guid|.*nodeid|.*guid|actor_?path|component_?path|created_.*|new_.*|output_path")
_REPLY_PATH = re.compile(r"path|asset_?path|bp_?path|world_?path|package_?path|asset|blueprint")
_ARG_ITEM = re.compile(r"new_.*|.*_name|name|label|tag|var_signature")
_ARG_NOT_ITEM = re.compile(r"graph_name|parent_name|.*class|.*class_path|.*type.*|mapping.*|event_name_filter")
_ARG_PATH = re.compile(r".*path")


def created_id(reply, arguments: dict):
    """Find the id of what a create tool made: an id in its reply, else the name or path it was asked to create."""
    if isinstance(reply, str):
        return reply, "reply"
    fields = {k: v for k, v in reply.items() if isinstance(v, str) and v and not _NOT_THE_ITEM.search(k.lower())} if isinstance(reply, dict) else {}
    for key, value in fields.items():
        if _REPLY_ID.fullmatch(key.lower()):
            return value, "reply"
    args = {k: v for k, v in arguments.items() if isinstance(v, str) and v and (k == "source_name" or not _NOT_THE_ITEM.search(k))}
    if "destination_path" in args and "asset_name" in args:
        return f"{args['destination_path'].rstrip('/')}/{args['asset_name']}", "arguments"
    for key, value in args.items():
        if _ARG_ITEM.fullmatch(key) and not _ARG_NOT_ITEM.fullmatch(key):
            return (value.split()[-1] if key == "var_signature" else value), "arguments"
    for key, value in fields.items():
        if _REPLY_PATH.fullmatch(key.lower()):
            return value, "reply"
    for key, value in args.items():
        if _ARG_PATH.fullmatch(key):
            return value, "arguments"
    return None, None


def client_tool(fn):
    """What MCP clients call: every reply is an object with success and tool, including lists and plain values."""
    @functools.wraps(fn)
    def run(*a, **kw):
        arguments = {k: v for k, v in kw.items() if v not in (None, "")}
        shown = {k: (v[:300] if isinstance(v, str) else v) for k, v in arguments.items()}
        try:
            text = fn(*a, **kw)
        except (ValueError, TypeError, KeyError) as error:
            return json.dumps({**json.loads(_failure(fn.__name__, str(error))), "arguments": shown})
        if not isinstance(text, str):
            return text
        try:
            data = json.loads(text)
        except ValueError:
            data = text
        reply = {"tool": fn.__name__, **data} if isinstance(data, dict) and "success" in data else {"success": True, "tool": fn.__name__, "result": data}
        if not reply.get("success"):
            reply["arguments"] = shown
        elif CREATE_TOOL.match(fn.__name__) and not kw.get("dry_run") and "id" not in reply:
            found, origin = created_id(data, arguments)
            if found:
                reply.update(id=found, id_source=origin)
        return json.dumps(reply)
    return run


_register_tool = mcp.tool


def _tool(*a, **kw):
    register = _register_tool(*a, **kw)

    def decorate(fn):
        if inspect.iscoroutinefunction(fn):  # The catalog tools relay other tools' results.
            return register(fn)
        wrapped = standard_tool(fn)
        register(client_tool(wrapped))
        return wrapped
    return decorate


mcp.tool = _tool

common_instruction = """
Valid Unreal Engine class name should be:
for Engine class like 'Actor', 'Pawn', 'Character', 'GameModeBase', etc.
for BP generated class should be /Game/YourFolder/YourBlueprint.YourBlueprint_C
for C++ class should be /Script/YourModule.YourClass

Valid variable, function or custom event signature is in c++ style:
for UObject type use valid Unreal Engine class name with * (e.g. Actor* ActorInput, StaticMeshComponent* MeshCompInput).
for array, set, map type use TArray<> TSet<> TMap<> (e.g. TArray<int32> IntArray, TSet<float> FloatSet, TMap<FString, int32> StringIntMap).
for struct type use valid Unreal Engine struct name (e.g. Vector Location, Rotator Rotation, Transform TransformInput).
for enum type use valid Unreal Engine enum name (e.g. EPhysicalSurface SurfaceType, ECollisionChannel CollisionChannel).
for basic type use int32, float, double, bool, FString, FName, FText,...
Variable use only single variable signature (e.g. 'float NewVar', 'Actor* TargetActor').
Function or custom event use multiple parameters separated by comma (e.g. `int32 Count, Actor* TargetActor, bool bIsActive').

Valid Blueprint path should start with /Game/ 

Valid value string to set default value of variable or pin:
for basic type should be in c++ style, can be deserialized to the variable type. 
for UObject type, use the full path of the asset (e.g. '/Game/StarterContent/Shapes/Shape_Cube.Shape_Cube' for StaticMesh etc.)
"""


def _unsupported(tool_name: str, reason: str) -> str:
    """Return a structured result for features not exposed by the native plugin."""
    import json
    return json.dumps({
        "error": {
            "code": "unsupported_operation",
            "tool": tool_name,
            "message": reason,
        }
    })


def _asset_request(path: str, asset_path: str, properties: dict | None = None,
                   operation: str = "set_properties", dry_run: bool = False,
                   save: bool = False, confirm: bool = False) -> str:
    response = httpx.patch(f"{BASE_URL}/{path}", json={
        "AssetPath": asset_path, "Operation": operation,
        "Properties": properties or {}, "bDryRun": dry_run,
        "bSave": save, "bConfirm": confirm
    })
    return response.text


def _ext(route: str, body: dict) -> str:
    return httpx.post(f"{BASE_URL}{route}", json=body, timeout=180).text


def merged_annotation(kinds: set, optional: bool = False):
    """Union of a merged parameter's types. A string-only parameter stays plain str: FastMCP decodes JSON text passed to
    any other annotation, which would turn a snapshot string into a dict."""
    members = {member for kind in kinds for member in (typing.get_args(kind) if typing.get_origin(kind) in (typing.Union, types.UnionType) else (kind,))}
    members.discard(type(None))
    if members == {str}:
        return str
    return typing.Union[(*members, None)] if optional else typing.Union[tuple(members)]


def merged_tool(name: str, variants: dict) -> callable:
    """List one tool that runs one of several functions, chosen by its required variant argument.

    Its schema is the union of the functions' parameters. A parameter is required only if every variant requires it, so
    the wrapper refuses arguments the chosen variant lacks or requires, as a result the caller can correct.
    """
    hints = {key: typing.get_type_hints(fn) for key, fn in variants.items()}
    signatures = {key: inspect.signature(fn) for key, fn in variants.items()}
    required = {key: [n for n, p in sig.parameters.items() if p.default is p.empty] for key, sig in signatures.items()}
    types = {}
    for key, sig in signatures.items():
        for param in sig.parameters:
            types.setdefault(param, set()).add(hints[key][param])
    parameters = [inspect.Parameter("variant", inspect.Parameter.KEYWORD_ONLY, annotation=typing.Literal[tuple(variants)])]
    for param, kinds in types.items():
        if all(param in r for r in required.values()):
            parameters.append(inspect.Parameter(param, inspect.Parameter.KEYWORD_ONLY, annotation=merged_annotation(kinds)))
    for param, kinds in types.items():
        if not all(param in r for r in required.values()):
            parameters.append(inspect.Parameter(param, inspect.Parameter.KEYWORD_ONLY, default=None,
                                                annotation=merged_annotation(kinds, optional=True)))

    def run(**arguments):
        variant = arguments.pop("variant")
        supplied = {k: v for k, v in arguments.items() if v is not None}
        accepted = signatures[variant].parameters
        unknown = sorted(set(supplied) - set(accepted))
        missing = [p for p in required[variant] if p not in supplied]
        if unknown or missing:
            return json.dumps({"errorMessage": f"Variant {variant} requires {required[variant]} and accepts {list(accepted)}; "
                                               f"missing {missing}, not accepted {unknown}"})
        return variants[variant](**supplied)

    run.__name__ = name
    run.__signature__ = inspect.Signature(parameters, return_annotation=str)
    wrapped = standard_tool(run)
    sections = [f"Set variant to one of: {', '.join(variants)}."]
    for key, fn in variants.items():
        needs = ", ".join(required[key]) or "nothing else"
        sections.append(f"variant={key} requires {needs}; accepts {', '.join(signatures[key].parameters) or 'nothing'}.\n{inspect.getdoc(fn) or ''}")
    mcp.add_tool(client_tool(wrapped), name=name, description="\n\n".join(sections))
    return wrapped
