"""Run prepare, restart editor, then verify placed native and Blueprint audio instances."""
import argparse
import json
import uuid
import hashlib
import re
import shutil
from pathlib import Path
import httpx

PROJECT = Path(__file__).resolve().parents[5]
STATE = PROJECT/'Saved'/'UE5MCP_Test'/'audio_component_instances.json'


def cleanup_external_fixture(package):
    assert re.fullmatch(r'/Game/UE5MCP_Test/MCP_AudioInstances_[0-9a-f]{8}',package),package
    name=package.rsplit('/',1)[1]
    content=(PROJECT/'Content').resolve()
    assert not (content/'UE5MCP_Test'/(name+'.umap')).exists(), 'Unload and delete test map first'
    for subtree in ['__ExternalActors__','__ExternalObjects__']:
        root=(content/subtree/'UE5MCP_Test').resolve()
        target=(root/name).resolve()
        assert root.is_relative_to(content) and target.parent==root and target.name==name,target
        if target.exists():
            shutil.rmtree(target)


def run(base, phase, partitioned=False):
    state_file = STATE.with_name('audio_component_external_instances.json') if partitioned else STATE
    def call(method, route, body=None, **params):
        r = httpx.request(method, base+route, json=body, params=params, timeout=180)
        assert r.is_success, (r.status_code, r.text)
        try:
            return r.json()
        except ValueError:
            return r.text

    def load(path):
        result = call('POST','/worlds/load', {'WorldPath':path,'DirtyPolicy':'discard','bConfirm':True})
        assert result['success'], result

    def cleanup_partition_assets(package):
        cleanup_external_fixture(package)
        name=package.rsplit('/',1)[1]
        # NewMapFromTemplate creates map-specific HLOD layers alongside the fixture.
        for path in (PROJECT/'Content'/'UE5MCP_Test').glob(name+'_HLOD*.uasset'):
            assert re.fullmatch(re.escape(name)+r'_HLOD[0-9]+_[A-Za-z0-9_]+',path.stem),path
            call('POST','/assets/delete',{'AssetPath':'/Game/UE5MCP_Test/'+path.stem})

    def inspect(actor):
        return call('GET','/audio/components/settings', actor_path=actor, component_name='Audio')

    def edit(actor, **changes):
        return call('PATCH','/audio/components/settings', {'ActorPath':actor,'ComponentName':'Audio'} | changes)

    def settings(s):
        return {k:s[k] for k in ['numeric_settings','bool_settings','references','concurrency_paths']}

    assert not call('GET','/editor/status')['is_playing']
    if phase == 'verify':
        state = json.loads(state_file.read_text())
        try:
            load(state['map'])
            for actor, expected in state['expected'].items():
                actual = inspect(actor)
                assert settings(actual)==expected, actual
                assert not actual['dirty'], actual
                if partitioned:
                    assert actual['package_path']==state['packages'][actor],actual
            template = call('GET','/audio/components/settings', bp_path=state['bp'], component_name='Audio')
            assert settings(template)==state['template'], template
            print(('External-actor' if partitioned else 'Placed')+' native and Blueprint Audio Component settings survived editor restart without changing archetype: OK')
        finally:
            load(state['original'])
            for asset in [state['map'], state['bp']]:
                call('POST','/assets/delete', {'AssetPath':asset})
            if partitioned:
                cleanup_partition_assets(state['map'])
            state_file.unlink(missing_ok=True)
        return

    assert not state_file.exists(), 'Existing instance fixture needs verify first'
    original = call('GET','/worlds/inspect')['world_path']
    name = 'MCP_AudioInstances_'+uuid.uuid4().hex[:8]
    package = '/Game/UE5MCP_Test/'+name
    bp = None
    created = False
    keep = False
    try:
        # Fail instead of discarding unrelated editor edits when entering the fixture.
        request = {'WorldPath':package,'DirtyPolicy':'fail','bSave':True}
        if partitioned:
            request['TemplatePath']='/Engine/Maps/Templates/OpenWorld'
        r = call('POST','/worlds/create', request)
        assert r['success'], r
        created = True
        if partitioned:
            p = call('GET','/worlds/partition')
            assert p['partitioned'] and p['external_actors'],p
        result = call('POST','/blueprint', {'BpPath':package+'_BP','ParentClass':'Actor'})
        bp = result.get('BpPath') or result['bpPath']
        call('POST','/blueprints/compile', {'BpPath':bp})
        call('POST','/blueprints/components', {'BpPath':bp,'ComponentName':'Audio','ComponentClass':'AudioComponent'})
        call('PATCH','/audio/components/settings', {'BpPath':bp,'ComponentName':'Audio','BoolSettings':{'bAutoActivate':False},'bSave':True})
        template = settings(call('GET','/audio/components/settings', bp_path=bp, component_name='Audio'))
        native = call('POST','/editor/actors/spawn', {'ActorClass':'/Script/Engine.Actor'})
        call('POST','/scene/actors/components', {'ActorPath':native,'ComponentName':'Audio',
             'ComponentClass':'/Script/Engine.AudioComponent','Properties':{'bAutoActivate':'False'}})
        blueprint = call('POST','/editor/actors/spawn', {'AssetPath':bp})
        if partitioned:
            for actor in [native,blueprint]:
                call('PATCH','/editor/actors/properties',{'ActorPath':actor,'Properties':{'bIsSpatiallyLoaded':'False'}})
        call('POST','/worlds/save', {})
        map_file=PROJECT/'Content'/'UE5MCP_Test'/(name+'.umap')
        map_digest=hashlib.sha256(map_file.read_bytes()).hexdigest()
        packages={}
        expected = {}
        for actor, volume in [(native,.27),(blueprint,.61)]:
            before = inspect(actor)
            if partitioned:
                assert '/__ExternalActors__/' in before['package_path'],before
                external=PROJECT/'Content'/(before['package_path'].removeprefix('/Game/')+'.uasset')
                assert external.exists(),external
                old_digest=hashlib.sha256(external.read_bytes()).hexdigest()
                packages[actor]=before['package_path']
            changes = {'NumericSettings':{'VolumeMultiplier':volume,'PitchMultiplier':.7},
                       'BoolSettings':{'bIsUISound':True,'bAutoActivate':False},
                       'References':{'Sound':'/Engine/EngineSounds/1kSineTonePing.1kSineTonePing'}}
            preview = edit(actor, **changes, bDryRun=True, bSave=True)
            assert preview['would_change'] and not preview['changed'] and not preview['saved']
            assert inspect(actor)==before
            r = httpx.patch(base+'/audio/components/settings', json={'ActorPath':actor,'ComponentName':'Audio',
                            'NumericSettings':{'VolumeMultiplier':.9},'References':{'Sound':'/Engine/EngineSounds/Master.Master'}}, timeout=180)
            assert r.status_code>=400 and inspect(actor)==before
            r = httpx.patch(base+'/audio/components/settings', json={'ActorPath':actor,'BpPath':bp,'ComponentName':'Audio'}, timeout=180)
            assert r.status_code>=400
            applied = edit(actor, **changes)
            assert applied['changed'] and applied['dirty'], applied
            after = settings(inspect(actor))
            assert abs(after['numeric_settings']['VolumeMultiplier']-volume)<1e-6, after
            assert after['references']['Sound']==changes['References']['Sound'], after
            call('POST','/editor/transactions/undo')
            assert settings(inspect(actor))==settings(before)
            call('POST','/editor/transactions/redo')
            assert settings(inspect(actor))==after
            saved = edit(actor, **changes, bSave=True)
            assert not saved['changed'] and saved['saved'] and not saved['dirty'], saved
            expected[actor] = settings(inspect(actor))
            if partitioned:
                assert saved['package_path']==before['package_path'],saved
                assert hashlib.sha256(external.read_bytes()).hexdigest()!=old_digest
                assert hashlib.sha256(map_file.read_bytes()).hexdigest()==map_digest, 'Component save unexpectedly rewrote the map'
        assert settings(call('GET','/audio/components/settings', bp_path=bp, component_name='Audio'))==template
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps({'original':original,'map':package,'bp':bp,'template':template,'expected':expected,'packages':packages}))
        keep = True
        print('Placed Audio Component preflight, instance changes, undo/redo, no-op/package save and template independence: OK; restart then verify')
    finally:
        load(original)
        if not keep:
            if created:
                call('POST','/assets/delete', {'AssetPath':package})
                if partitioned:
                    cleanup_partition_assets(package)
            if bp:
                call('POST','/assets/delete', {'AssetPath':bp})


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--base-url', default='http://127.0.0.1:8080')
    p.add_argument('--phase', choices=['prepare','verify'], required=True)
    p.add_argument('--partitioned', action='store_true')
    args = p.parse_args()
    run(args.base_url,args.phase,args.partitioned)
