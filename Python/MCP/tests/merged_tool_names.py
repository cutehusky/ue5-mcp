"""Test helper: lets a smoke test keep naming a function that is now a variant of a merged tool.

Calls still go through the merged tool's own schema and dispatch, so the test exercises what clients use.
"""
import inspect
from types import SimpleNamespace


def use_old_names(mcp):
    list_tools, call_tool = mcp.list_tools, mcp.call_tool

    async def variants():
        found = {}
        for tool in await list_tools():
            wrapper = mcp._tool_manager.get_tool(tool.name).fn
            for key, fn in inspect.getclosurevars(wrapper).nonlocals.get('variants', {}).items():
                found[fn.__name__] = (tool, key)
        return found

    async def listed():
        found = await variants()
        merged = {tool.name for tool, _ in found.values()}
        def own_schema(tool, key):
            wrapper = mcp._tool_manager.get_tool(tool.name).fn
            accepted = inspect.signature(inspect.getclosurevars(wrapper).nonlocals['variants'][key]).parameters
            properties = tool.inputSchema['properties']
            return {**tool.inputSchema, 'properties': {p: properties[p] for p in accepted}}

        return [t for t in await list_tools() if t.name not in merged] + [
            SimpleNamespace(name=old, description=tool.description, inputSchema=own_schema(tool, key))
            for old, (tool, key) in found.items()]

    async def call(name, arguments):
        found = (await variants()).get(name)
        if found:
            return await call_tool(found[0].name, {'variant': found[1], **arguments})
        return await call_tool(name, arguments)

    mcp.list_tools, mcp.call_tool = listed, call
