"""Offline: every merged tool variant sends the same request as its original function, and refuses bad arguments."""
import asyncio
import inspect
import json
import sys
import types
import typing

import httpx

sys.argv = sys.argv[:1]
import mcp_server as m  # noqa: E402
from ue5_tools.app import standard_result  # noqa: E402
from ue5_tools import app  # noqa: E402
from ue5_tools.app import client_tool  # noqa: E402

requests = []


class Response:
    text = '{"ok": true}'
    status_code = 200

    def json(self):
        return {"ok": True}


def capture(*args, **kwargs):
    requests.append(json.dumps([args, kwargs], sort_keys=True, default=str))
    return Response()


for verb in ('get', 'post', 'put', 'patch', 'delete', 'request'):
    setattr(httpx, verb, capture)


def sample(annotation, index):
    if typing.get_origin(annotation) is typing.Literal:
        return typing.get_args(annotation)[0]
    optional = typing.get_origin(annotation) in (typing.Union, types.UnionType)
    args = [a for a in typing.get_args(annotation) if a is not type(None)] if optional else []
    kind = args[0] if args else annotation
    origin = typing.get_origin(kind) or kind
    if origin is bool:
        return True
    if origin is int:
        return 3 + index
    if origin is float:
        return 1.5 + index
    if origin is list:
        return []
    if origin is dict:
        return {}
    return '{"json": ' + str(index) + '}'  # JSON text must reach string parameters unchanged.


async def same_as_original(name, key, fn, arguments):
    """The merged tool sends the original's requests and returns its result, or fails with its error."""
    requests.clear()
    try:
        call = lambda: standard_result(name, fn(**arguments))
        call.__name__ = name
        direct, error = client_tool(call)(), None
    except Exception as e:
        direct, error = None, str(e)
    want = list(requests)
    requests.clear()
    try:
        got = await m.mcp.call_tool(name, {'variant': key, **arguments})
        block = (got[0] if isinstance(got, tuple) else got)[0].text
        without_arguments = lambda text: {k: v for k, v in json.loads(text).items() if k not in ('arguments', 'id', 'id_source')}
        assert error is None and without_arguments(block) == without_arguments(direct), (name, key, error, block, direct)
    except Exception as e:
        assert error and error in str(e), (name, key, error, e)
    assert list(requests) == want, (name, key, requests, want)


async def main():
    listed = {t.name: t for t in await m.mcp.list_tools()}
    variants = 0
    for name, tool in listed.items():
        props = tool.inputSchema.get('properties', {})
        if 'variant' not in props or 'Set variant to one of' not in (tool.description or ''):
            continue
        keys = props['variant']['enum']
        wrapper = app.mcp._tool_manager.get_tool(name).fn
        originals = inspect.getclosurevars(inspect.unwrap(wrapper)).nonlocals['variants']
        assert list(originals) == keys, name
        for key in keys:
            fn = originals[key]
            hints = typing.get_type_hints(fn)
            # All parameters, so optional ones are forwarded too.
            call = {p: sample(hints[p], i) for i, p in enumerate(inspect.signature(fn).parameters)}
            # JSON text is only kept whole by parameters that are strings in every variant.
            schema = inspect.signature(wrapper).parameters
            call = {p: f's{i}' if isinstance(v, str) and v.startswith('{') and schema[p].annotation is not str else v
                    for i, (p, v) in enumerate(call.items())}
            await same_as_original(name, key, fn, call)
            variants += 1
            # Only required parameters also matches the function's own defaults.
            need = {p: call[p] for p, q in inspect.signature(fn).parameters.items() if q.default is q.empty}
            await same_as_original(name, key, fn, need)
            if need:
                requests.clear()
                gone = next(iter(need))
                try:
                    out = (await m.mcp.call_tool(name, {'variant': key, **{k: v for k, v in need.items() if k != gone}}))
                    out = (out[0] if isinstance(out, tuple) else out)[0].text
                except Exception as e:  # The schema itself requires arguments every variant needs.
                    out = 'errorMessage ' + str(e)
                assert not requests and 'errorMessage' in out, (name, key, 'missing', out, requests)
        print('ok', name, len(keys))
    assert variants, 'no merged tools found'
    print(f'Verified {variants} variants; {len(listed)} tools listed in full')


asyncio.run(main())
