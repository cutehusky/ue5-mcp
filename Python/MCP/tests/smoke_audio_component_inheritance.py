"""Native inherited SCS Audio Component overrides; prepare, restart, verify."""
import argparse
import json
import uuid
from pathlib import Path
import httpx

STATE = Path(__file__).resolve().parents[5]/'Saved'/'UE5MCP_Test'/'audio_component_inheritance.json'


def run(base, phase, native=False):
    state_file=STATE.with_name('audio_component_native_inheritance.json') if native else STATE
    component_name='AudioComponent0' if native else 'Audio'
    def call(method, route, body=None, **params):
        r = httpx.request(method,base+route,json=body,params=params,timeout=180)
        assert r.is_success,(r.status_code,r.text)
        try:
            return r.json()
        except ValueError:
            return r.text

    def inspect(bp):
        return call('GET','/audio/components/settings',bp_path=bp,component_name=component_name)

    def edit(bp, **changes):
        return call('PATCH','/audio/components/settings',{'BpPath':bp,'ComponentName':component_name} | changes)

    def values(bp, volume, pitch):
        s = inspect(bp)
        assert abs(s['numeric_settings']['VolumeMultiplier']-volume)<1e-6, s
        assert abs(s['numeric_settings']['PitchMultiplier']-pitch)<1e-6, s
        return s

    def snapshot(s):
        return {k:s[k] for k in ['numeric_settings','bool_settings','references','concurrency_paths']}

    assert not call('GET','/editor/status')['is_playing']
    if phase=='verify':
        state = json.loads(state_file.read_text())
        try:
            for bp, expected in state['expected'].items():
                s = inspect(bp)
                assert snapshot(s)==expected['settings'] and s['has_local_override']==expected['override'], s
            if native:
                original=call('GET','/worlds/inspect')['world_path']
                package='/Game/UE5MCP_Test/MCP_NativeAudioSpawn_'+uuid.uuid4().hex[:8]
                created=False
                try:
                    result=call('POST','/worlds/create',{'WorldPath':package,'DirtyPolicy':'fail','bSave':True})
                    assert result['success'],result
                    created=True
                    for bp, expected in state['expected'].items():
                        actor=call('POST','/editor/actors/spawn',{'AssetPath':bp})
                        actual=call('GET','/audio/components/settings',actor_path=actor,component_name=component_name)
                        assert snapshot(actual)==expected['settings'],actual
                finally:
                    if created:
                        call('POST','/worlds/load',{'WorldPath':original,'DirtyPolicy':'discard','bConfirm':True})
                        call('POST','/assets/delete',{'AssetPath':package})
            child, grandchild, parent = state['child'],state['grandchild'],state['parent']
            assert edit(grandchild,bResetInheritedOverride=True,bSave=True)['changed']
            assert snapshot(inspect(grandchild))==snapshot(inspect(child))
            assert not inspect(grandchild)['has_local_override']
            assert edit(child,bResetInheritedOverride=True,bSave=True)['changed']
            assert snapshot(inspect(child))==snapshot(inspect(parent))
            assert not inspect(child)['has_local_override']
            print('Inherited Audio Component overrides survived cold restart; native reset restores parent settings: OK')
        finally:
            for bp in reversed(state['assets']):
                call('POST','/assets/delete',{'AssetPath':bp})
            for asset in state.get('extras',[]):
                call('POST','/assets/delete',{'AssetPath':asset})
            state_file.unlink(missing_ok=True)
        return

    assert not state_file.exists(), 'Verify existing inheritance fixture first'
    assets=[]
    extras=[]
    keep=False
    name='BP_MCP_AudioInheritance_'+uuid.uuid4().hex[:8]
    def create(suffix, parent='Actor'):
        result=call('POST','/blueprint',{'BpPath':'/Game/UE5MCP_Test/'+name+suffix,'ParentClass':parent})
        bp=result.get('BpPath') or result['bpPath']
        assets.append(bp)
        call('POST','/blueprints/compile',{'BpPath':bp})
        return bp

    def generated(bp):
        return bp+'.'+bp.rsplit('/',1)[1]+'_C'

    try:
        parent=create('_Parent','AmbientSound' if native else 'Actor')
        if not native:
            call('POST','/blueprints/components',{'BpPath':parent,'ComponentName':'Audio','ComponentClass':'AudioComponent'})
        native_sibling=create('_NativeSibling','AmbientSound') if native else None
        native_before=inspect(native_sibling) if native else None
        edit(parent,NumericSettings={'VolumeMultiplier':.25,'PitchMultiplier':.9},BoolSettings={'bAutoActivate':False},
             References={'Sound':'/Engine/EngineSounds/1kSineTonePing.1kSineTonePing'},bSave=True)
        child=create('_Child',generated(parent))
        sibling=create('_Sibling',generated(parent))
        original=inspect(parent)
        before=values(child,.25,.9)
        assert before['inherited'] and not before['has_local_override'],before
        if native:
            assert before['native_default_subobject'] and before['template_path'].startswith(child),before
        assert not before['dirty'],before
        preview=edit(child,NumericSettings={'VolumeMultiplier':.55},bDryRun=True,bSave=True)
        assert preview['would_change'] and not preview['changed']
        assert inspect(child)==before and inspect(parent)==original
        assert not edit(child,NumericSettings={'VolumeMultiplier':.25})['changed']
        assert inspect(child)==before
        r=httpx.patch(base+'/audio/components/settings',json={'BpPath':child,'ComponentName':component_name,
                      'NumericSettings':{'VolumeMultiplier':.55},'References':{'Sound':'/Engine/EngineSounds/Master.Master'}},timeout=180)
        assert r.status_code>=400 and inspect(child)==before and inspect(parent)==original
        assert edit(child,NumericSettings={'VolumeMultiplier':.55})['changed']
        s=values(child,.55,.9)
        assert s['has_local_override'] and inspect(parent)==original
        values(sibling,.25,.9)
        call('POST','/editor/transactions/undo')
        assert snapshot(inspect(child))==snapshot(before),inspect(child)
        call('POST','/editor/transactions/redo')
        assert snapshot(inspect(child))==snapshot(s),inspect(child)
        edit(child,bSave=True)
        grandchild=create('_Grandchild',generated(child))
        assert not values(grandchild,.55,.9)['has_local_override']
        edit(grandchild,NumericSettings={'PitchMultiplier':.7},bSave=True)
        values(grandchild,.55,.7)
        values(child,.55,.9)
        r=httpx.post(base+'/audio/concurrencies/create',json={'AssetPath':'/Game/UE5MCP_Test/'+name+'_Concurrency','bSave':True},timeout=180)
        assert r.is_success,r.text
        extras.append(r.text)
        edit(parent,NumericSettings={'VolumeMultiplier':.3,'PitchMultiplier':.8},BoolSettings={'bIsUISound':True},
             References={'SoundClassOverride':'/Engine/EngineSounds/Master.Master'},bSetConcurrency=True,ConcurrencyPaths=extras,bSave=True)
        values(sibling,.3,.8)
        values(child,.55,.8)
        values(grandchild,.55,.7)
        for bp in [child,sibling,grandchild]:
            s=inspect(bp)
            assert s['bool_settings']['bIsUISound'] and s['concurrency_paths']==extras,s
            assert s['references']['SoundClassOverride']=='/Engine/EngineSounds/Master.Master',s
        # Undoable reset uses the native override record rather than copying parent values.
        assert not edit(child,bResetInheritedOverride=True,bDryRun=True)['changed']
        assert values(child,.55,.8)['has_local_override']
        assert edit(child,bResetInheritedOverride=True)['changed']
        assert not values(child,.3,.8)['has_local_override']
        values(grandchild,.3,.7)
        call('POST','/editor/transactions/undo')
        assert values(child,.55,.8)['has_local_override']
        values(grandchild,.55,.7)
        # Native compile may dirty descendant packages; save each explicit fixture.
        for bp in assets:
            edit(bp,bSave=True)
        expected={bp:{'settings':snapshot(inspect(bp)),'override':inspect(bp)['has_local_override']} for bp in assets}
        if native:
            assert inspect(native_sibling)==native_before,inspect(native_sibling)
        state_file.parent.mkdir(parents=True,exist_ok=True)
        state_file.write_text(json.dumps({'assets':assets,'extras':extras,'parent':parent,'child':child,'grandchild':grandchild,'expected':expected}))
        keep=True
        print('Inherited native overrides: preflight/no-op, parent/sibling isolation, undo/redo, multilevel propagation, reset and save: OK; restart then verify')
    finally:
        if not keep:
            for bp in reversed(assets):
                call('POST','/assets/delete',{'AssetPath':bp})
            for asset in extras:
                call('POST','/assets/delete',{'AssetPath':asset})


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--base-url',default='http://127.0.0.1:8080')
    p.add_argument('--phase',choices=['prepare','verify'],required=True)
    p.add_argument('--native',action='store_true')
    a=p.parse_args()
    run(a.base_url,a.phase,a.native)
