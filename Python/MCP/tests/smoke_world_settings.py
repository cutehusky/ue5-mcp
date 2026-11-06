"""Prepare, restart editor, verify typed persistent World Settings and clean fixtures."""
import argparse
import json
import time
import uuid
from pathlib import Path
import httpx
from smoke_audio_component_instances import cleanup_external_fixture

PROJECT=Path(__file__).resolve().parents[5]


def run(base, phase, partitioned):
    state_file=PROJECT/'Saved'/'UE5MCP_Test'/('world_settings_partitioned.json' if partitioned else 'world_settings.json')
    def call(method, route, body=None):
        r=httpx.request(method,base+route,json=body,timeout=180)
        assert r.is_success,(r.status_code,r.text)
        return r.json()
    def inspect():
        return call('GET','/worlds/settings')
    def values(s):
        return {k:s[k] for k in ['numeric_settings','bool_settings','class_settings','enum_settings']}
    def edit(**kw):
        return call('PATCH','/worlds/settings',kw)
    def load(path):
        r=call('POST','/worlds/load',{'WorldPath':path,'DirtyPolicy':'discard','bConfirm':True})
        assert r['success'],r
    def cleanup(state):
        load(state['original'])
        call('POST','/assets/delete',{'AssetPath':state['map']})
        if partitioned:
            cleanup_external_fixture(state['map'])
            name=state['map'].rsplit('/',1)[1]
            for p in (PROJECT/'Content'/'UE5MCP_Test').glob(name+'_HLOD*.uasset'):
                call('POST','/assets/delete',{'AssetPath':'/Game/UE5MCP_Test/'+p.stem})
        state_file.unlink(missing_ok=True)
    assert not call('GET','/editor/status')['is_playing']
    if phase=='verify':
        state=json.loads(state_file.read_text())
        try:
            load(state['map'])
            actual=inspect()
            assert values(actual)==state['expected'],actual
            assert not actual['dirty'],actual
            print('Typed '+('partitioned ' if partitioned else '')+'World Settings survived cold restart: OK')
        finally:
            cleanup(state)
        return
    assert not state_file.exists(),'Verify the previous fixture first'
    original=call('GET','/worlds/inspect')['world_path']
    # Reuse the guarded UUID cleanup resolver for partitioned map files.
    package='/Game/UE5MCP_Test/MCP_AudioInstances_'+uuid.uuid4().hex[:8]
    state={'original':original,'map':package}
    created=False; keep=False
    try:
        req={'WorldPath':package,'DirtyPolicy':'fail','bSave':True}
        if partitioned:
            req['TemplatePath']='/Engine/Maps/Templates/OpenWorld'
        r=call('POST','/worlds/create',req); assert r['success'],r; created=True
        before=inspect(); assert not before['dirty'],before
        request={'WorldPath':package,'NumericSettings':{'GlobalGravityZ':-345.5,'KillZ':-65432,'WorldToMeters':123,
                 'PackedLightAndShadowMapTextureSize':2048,'LightmassSettings.NumIndirectLightingBounces':7,
                 'LightmassSettings.IndirectLightingQuality':2.5,'LightmassSettings.DirectIlluminationOcclusionFraction':.25},
                 'BoolSettings':{'bGlobalGravitySet':True,'bEnableWorldBoundsChecks':False,'LightmassSettings.bUseAmbientOcclusion':True},
                 'ClassSettings':{'DefaultGameMode':'/Script/Engine.GameModeBase','KillZDamageType':'/Script/Engine.DamageType'},
                 'EnumSettings':{'VisibilityAggressiveness':'VIS_MostAggressive','LightmassSettings.VolumeLightingMethod':'VLM_SparseVolumeLightingSamples'}}
        assert edit(**request,bDryRun=True)['changed']
        assert inspect()==before,'Dry-run changed native settings or package state'
        bad=[{'NumericSettings':{'WorldToMeters':0}}, {'NumericSettings':{'LightmassSettings.NumIndirectLightingBounces':1.5}},
             {'NumericSettings':{'PackedLightAndShadowMapTextureSize':1000}}, {'BoolSettings':{'bWorldGravitySet':True}},
             {'EnumSettings':{'VisibilityAggressiveness':'VIS_Max'}}, {'WorldPath':'/Game/Wrong'},
             {'NumericSettings':{'KillZ':-222},'ClassSettings':{'DefaultGameMode':'/Script/Engine.Actor'}},
             {'ClassSettings':{'DefaultPhysicsVolumeClass':''}}]

        if partitioned:
            bad.append({'NumericSettings':{'KillZ':-123},'BoolSettings':{'bPrecomputeVisibility':True}})
            assert before['forced_bool_settings']=={'bPrecomputeVisibility':False},before
        else:
            assert before['forced_bool_settings']=={},before
        for body in bad:
            r=httpx.patch(base+'/worlds/settings',json=body,timeout=180)
            assert r.status_code>=400,r.text
            assert inspect()==before,'Rejected request partially changed settings'
        result=edit(**request); assert result['changed'] and result['dirty'] and not result['saved'],result
        expected=values(inspect())
        for group,fields in [('NumericSettings','numeric_settings'),('BoolSettings','bool_settings'),('ClassSettings','class_settings'),('EnumSettings','enum_settings')]:
            for key,value in request[group].items():
                assert expected[fields][key]==value,(key,value,expected)
        call('POST','/editor/transactions/undo')
        assert values(inspect())==values(before),inspect()
        call('POST','/editor/transactions/redo')
        assert values(inspect())==expected,inspect()
        assert not edit(**request)['changed'],'No-op should not create a mutation'
        assert edit(ClassSettings={'DefaultGameMode':''})['changed']
        assert inspect()['class_settings']['DefaultGameMode']==''
        edit(ClassSettings=request['ClassSettings'])
        r=edit(bSave=True); assert r['saved'] and not r['dirty'],r
        assert not edit(**request,bSave=True)['saved'],'Clean no-op should not rewrite the map'
        call('POST','/editor/play',{'Operation':'start'})
        try:
            for _ in range(100):
                if call('GET','/editor/status')['is_playing']: break
                time.sleep(.05)
            r=httpx.patch(base+'/worlds/settings',json={'NumericSettings':{'KillZ':-999}},timeout=180)
            assert r.status_code>=400,r.text
            assert values(inspect())==expected
        finally:
            call('POST','/editor/play',{'Operation':'stop'})
            for _ in range(100):
                if not call('GET','/editor/status')['is_playing']: break
                time.sleep(.05)
        state['expected']=expected
        state_file.parent.mkdir(parents=True,exist_ok=True); state_file.write_text(json.dumps(state))
        load(original); keep=True
        print('Typed World Settings: preflight, dry-run, undo/redo, no-op, class clear, save and PIE guard: OK; restart and verify')
    finally:
        if created and not keep:
            cleanup(state)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--base-url',default='http://127.0.0.1:8080')
    p.add_argument('--phase',choices=['prepare','verify'],required=True)
    p.add_argument('--partitioned',action='store_true')
    a=p.parse_args(); run(a.base_url,a.phase,a.partitioned)
