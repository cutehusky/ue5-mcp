"""Native per-map navigation configuration, system recreation and cold persistence."""
import argparse
import json
import time
import uuid
from pathlib import Path
import httpx
from smoke_audio_component_instances import cleanup_external_fixture

PROJECT=Path(__file__).resolve().parents[5]
MODULE='/Script/UE5_MCP.PersistentNavigationSystemConfig'
SYSTEM='/Script/NavigationSystem.NavigationSystemV1'
NULL='/Script/Engine.NullNavSysConfig'


def run(base,phase,partitioned):
    state_file=PROJECT/'Saved'/'UE5MCP_Test'/('world_navigation_partitioned.json' if partitioned else 'world_navigation.json')
    def call(method,route,body=None):
        r=httpx.request(method,base+route,json=body,timeout=180)
        assert r.is_success,(r.status_code,r.text)
        return r.json()
    def inspect(): return call('GET','/worlds/settings')
    def nav(): return inspect()['navigation']
    def stored(n): return {k:n[k] for k in ['config_class','system_class','supported_agent_indices','supported_agent_bits','default_agent_name','bool_settings']}
    def edit(n,**kw): return call('PATCH','/worlds/settings',{'bSetNavigation':True,'Navigation':n}|kw)
    def load(path):
        s=call('POST','/worlds/load',{'WorldPath':path,'DirtyPolicy':'discard','bConfirm':True}); assert s['success'],s
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
    if phase=='cleanup':
        cleanup(json.loads(state_file.read_text()))
        print('Owned navigation fixture removed')
        return
    if phase=='verify':
        state=json.loads(state_file.read_text())
        try:
            load(state['map']); s=inspect()
            assert stored(s['navigation'])==state['expected'],s
            assert not s['dirty'],s
            assert s['navigation']['live_system_class']==SYSTEM,s
            print(('Partitioned' if partitioned else 'Ordinary')+' navigation config persisted and native system recreated after cold restart: OK')
        finally: cleanup(state)
        return
    assert not state_file.exists(),'Verify existing fixture first'
    state={'original':call('GET','/worlds/inspect')['world_path'],'map':'/Game/UE5MCP_Test/MCP_AudioInstances_'+uuid.uuid4().hex[:8]}
    created=False; keep=False
    try:
        req={'WorldPath':state['map'],'DirtyPolicy':'fail','bSave':True}
        if partitioned: req['TemplatePath']='/Engine/Maps/Templates/OpenWorld'
        s=call('POST','/worlds/create',req); assert s['success'],s; created=True
        before=inspect()
        config={'ConfigClass':MODULE,'bSetSystemClass':True,'SystemClass':SYSTEM,'bSetSupportedAgents':True,
                'SupportedAgentIndices':[0,2],'bSetDefaultAgentName':True,'DefaultAgentName':'MCP_TestAgent',
                'BoolSettings':{'bStrictlyStatic':True,'bCreateOnClient':True,'bAutoSpawnMissingNavData':False,'bSpawnNavDataInNavBoundsLevel':False}}
        assert edit(config,bConfirm=True,bDryRun=True)['changed']
        assert inspect()==before,'Dry-run allocated or changed config'
        bad=[{'ConfigClass':'/Script/Engine.Object'}, {'bSetSystemClass':True,'SystemClass':'/Script/Engine.Actor'},
             {'bSetSystemClass':True,'SystemClass':''}, {'bSetSupportedAgents':True,'SupportedAgentIndices':[0,0]},
             {'bSetSupportedAgents':True,'SupportedAgentIndices':[16]}, {'BoolSettings':{'bUnknown':True}},
             {'ConfigClass':NULL,'bSetSystemClass':True,'SystemClass':SYSTEM}, {'ConfigClass':NULL}]
        for n in bad:
            # A valid scalar edit must not happen if navigation preflight fails.
            r=httpx.patch(base+'/worlds/settings',json={'bSetNavigation':True,'Navigation':n,'NumericSettings':{'KillZ':-123}},timeout=180)
            assert r.status_code>=400,r.text
            assert inspect()==before,'Rejected navigation request partially mutated map'
        s=edit(config,bConfirm=True); n=s['navigation']
        assert s['changed'] and s['dirty'] and n['live_system_class']==SYSTEM,s
        assert n['supported_agent_indices']==[0,2] and n['supported_agent_bits']==5,n
        assert n['default_agent_name']=='MCP_TestAgent' and n['bool_settings']==config['BoolSettings'],n
        assert n['config_path'].startswith(s['settings_path']+'.'),n
        expected=stored(n); copied_path=n['config_path']
        call('POST','/editor/transactions/undo')
        assert stored(nav())==stored(before['navigation']),nav()
        call('POST','/editor/transactions/redo')
        assert stored(nav())==expected and nav()['live_system_class']==SYSTEM,nav()
        assert not edit(config)['changed']
        assert nav()['config_path']==copied_path,'No-op allocated a fresh config'
        # Disabling uses a real Null config and destroys the live native system.
        s=edit({'ConfigClass':NULL},bConfirm=True)
        assert s['navigation']['system_class']=='' and s['navigation']['live_system_path']=='',s
        call('POST','/editor/transactions/undo')
        assert stored(nav())==expected and nav()['live_system_class']==SYSTEM,nav()
        # Empty masks round-trip without an invented default agent.
        edit({'bSetSupportedAgents':True,'SupportedAgentIndices':[]})
        assert nav()['supported_agent_indices']==[] and nav()['supported_agent_bits']==0,nav()
        call('POST','/editor/transactions/undo')
        assert stored(nav())==expected,nav()
        s=edit(config,bSave=True); assert s['saved'] and not s['dirty'],s
        assert not edit(config,bSave=True)['saved']
        call('POST','/editor/play',{'Operation':'start'})
        try:
            for _ in range(100):
                if call('GET','/editor/status')['is_playing']: break
                time.sleep(.05)
            r=httpx.patch(base+'/worlds/settings',json={'bSetNavigation':True,'Navigation':{'ConfigClass':NULL},'bConfirm':True},timeout=180)
            assert r.status_code>=400,r.text
            assert stored(nav())==expected
        finally:
            call('POST','/editor/play',{'Operation':'stop'})
            for _ in range(100):
                if not call('GET','/editor/status')['is_playing']: break
                time.sleep(.05)
        state['expected']=expected
        state_file.parent.mkdir(parents=True,exist_ok=True); state_file.write_text(json.dumps(state))
        load(state['original']); keep=True
        print('Native navigation config: copy ownership, whole-request preflight, dry-run, flags/agents, undo/redo, system disable/restore, no-op/save and PIE guard: OK; restart and verify')
    finally:
        if created and not keep: cleanup(state)


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--base-url',default='http://127.0.0.1:8080')
    p.add_argument('--phase',choices=['prepare','verify','cleanup'],required=True); p.add_argument('--partitioned',action='store_true')
    a=p.parse_args(); run(a.base_url,a.phase,a.partitioned)
