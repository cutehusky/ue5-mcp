"""Start the server the way Claude does, over stdio, through both a venv Python and a plain one, and call tools.

Works without an editor; with one on the API URL, get_ue_editor_status also reports the engine.
"""
import asyncio
import json
import sys
import time
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SCRIPT = Path(__file__).resolve().parents[1] / 'mcp_server.py'


async def check(python):
    started = time.time()
    server = StdioServerParameters(command=python, args=[str(SCRIPT), '--transport', 'stdio'], env={
        **__import__('os').environ, 'UE5_REST_API_URL': 'http://127.0.0.1:8080'})
    async with stdio_client(server) as (read, write), ClientSession(read, write) as session:
        await asyncio.wait_for(session.initialize(), 60)
        tools = (await session.list_tools()).tools
        names = {t.name for t in tools}
        assert {'find_tools', 'get_ue_editor_status', 'organize_blueprint_graph'} <= names and len(names) < 200, len(names)
        reply = json.loads((await session.call_tool('get_ue_editor_status', {})).content[0].text)
        assert reply.get('engine_version') or 'not reachable' in reply.get('errorMessage', ''), reply
        found = json.loads((await session.call_tool('find_tools', {'query': 'niagara renderer'})).content[0].text)
        assert found['matches'], found
        print(python, len(names), 'tools,', f'{time.time() - started:.1f}s,', reply.get('engine_version') or reply['errorMessage'])


for interpreter in sys.argv[1:] or [sys.executable]:
    asyncio.run(check(interpreter))
print('Stdio client verified')
