"""Advertised tool list and catalog, through a real MCP client session against the running editor."""
import asyncio
import json
import sys

import httpx
from mcp.shared.memory import create_connected_server_and_client_session as connect

sys.argv = sys.argv[:1]
import mcp_server as m  # noqa: E402

m.BASE_URL = 'http://127.0.0.1:8080'
TOKEN_BUDGET = 30000
BP = '/Game/UE5MCP_Test/BP_MCP_Catalog'


def text(result):
    assert not result.isError, result.content
    return result.content[0].text


async def main():
    every = {t.name for t in await m.mcp.list_tools()}
    missing = m.CORE_TOOLS - every
    assert not missing, ('core names that do not exist', sorted(missing))
    async with connect(m.mcp._mcp_server) as c:
        listed = (await c.list_tools()).tools
        tokens = sum(len(json.dumps(t.inputSchema)) + len(t.description or '') + len(t.name) for t in listed) // 4
        print(f'advertised {len(listed)} of {len(every)} tools, about {tokens} tokens')
        assert tokens <= TOKEN_BUDGET, sorted(((len(t.description or ''), t.name) for t in listed), reverse=True)[:12]
        names = {t.name for t in listed}
        assert {'find_tools', 'describe_tool', 'call_tool', 'create_blueprint'} <= names
        assert 'set_niagara_validation_rule' not in names

        call = lambda n, **a: c.call_tool(n, a)
        domains = json.loads(text(await call('find_tools')))
        assert domains['total'] == len(every) - 3 and 'niagara' in domains['domains'], domains
        for query, want in (('niagara validation rule string array', 'set_niagara_validation_rule'),
                            ('skeleton socket rename', 'rename_skeleton_socket'), ('import sound', 'import_sound_wave')):
            rows = json.loads(text(await call('find_tools', query=query)))['matches']
            assert want in [r['name'] for r in rows[:5]], (query, rows)
        assert json.loads(text(await call('find_tools', query='zzzqqq')))['matches'] == []
        some = json.loads(text(await call('find_tools', domain='pcg', limit=3)))['matches']
        assert len(some) == 3 and all(r['domain'] == 'pcg' for r in some), some

        d = json.loads(text(await call('describe_tool', name='rename_skeleton_socket')))
        assert 'socket_name' in d['input_schema']['properties'], d
        assert 'errorMessage' in json.loads(text(await call('describe_tool', name='nope')))

        # A hidden tool runs through the catalog, and directly by name.
        run = lambda n, **a: call('call_tool', name=n, arguments=a)
        s = json.loads(text(await run('inspect_gameplay_tag_settings')))
        assert 'redirects' in s, s
        assert 'errorMessage' in json.loads(text(await run('nope')))
        assert 'errorMessage' in json.loads(text(await run('find_tools')))             # no recursion
        assert 'errorMessage' in json.loads(text(await run('rename_skeleton_socket', wrong=1)))
        assert 'redirects' in json.loads(text(await call('inspect_gameplay_tag_settings')))

        # Advertised workflow: create, compile and delete a Blueprint.
        httpx.post(m.BASE_URL + '/assets/delete', json={'AssetPath': BP}, timeout=120)
        text(await call('create_blueprint', bp_path=BP, parent_class='Actor'))
        text(await call('add_variable_to_bp', bp_path=BP, var_signature='float Speed'))
        text(await call('compile_blueprint', bp_path=BP))
        assert 'Speed' in text(await call('get_blueprint_variables', bp_path=BP))
        httpx.post(m.BASE_URL + '/assets/delete', json={'AssetPath': BP}, timeout=120)

        # The existing play tool drives PIE, so the duplicate start/stop tools are not advertised.
        wait = lambda want: _wait_play(c, want)
        text(await call('control_ue_play_session', operation='start'))
        await wait(True)
        assert 'player_pawn' in text(await call('inspect_play_session', limit=1))
        text(await call('control_ue_play_session', operation='stop'))
        await wait(False)
    print('Tool catalog verified')


async def _wait_play(c, want):
    for _ in range(90):
        status = json.loads((await c.call_tool('get_ue_editor_status', {})).content[0].text)
        if status['is_playing'] == want:
            return
        await asyncio.sleep(1)
    raise AssertionError(('play state', want))


asyncio.run(main())
